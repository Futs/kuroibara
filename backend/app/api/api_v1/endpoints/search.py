import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.core.providers.user_preferences import (
    apply_fallback_prioritization,
    get_user_provider_preferences,
    prioritize_providers_by_user_preferences,
)
from app.models.provider import ProviderStatus
from app.models.user import User
from app.schemas.search import (
    ProviderInfo,
    SearchFilter,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_enabled_providers(db: AsyncSession):
    """Get only enabled providers based on database status."""
    try:
        # Get all providers from registry
        all_providers = provider_registry.get_all_providers()

        # Get provider statuses from database
        result = await db.execute(select(ProviderStatus))
        provider_statuses = {ps.provider_id: ps for ps in result.scalars().all()}

        # Filter to only enabled providers
        enabled_providers = []
        for provider in all_providers:
            provider_id = provider.name.lower()
            status_record = provider_statuses.get(provider_id)

            # Include provider if:
            # 1. No status record exists (default to enabled)
            # 2. Status record exists and is_enabled is True
            if not status_record or status_record.is_enabled:
                enabled_providers.append(provider)
            else:
                logger.debug(f"Excluding disabled provider: {provider.name}")

        logger.info(
            f"Using {len(enabled_providers)}/{len(all_providers)} enabled providers"
        )
        return enabled_providers

    except Exception as e:
        logger.error(f"Error filtering enabled providers: {e}")
        # Fallback to all providers if database query fails
        return provider_registry.get_all_providers()


@router.get("/providers", response_model=List[ProviderInfo])
async def get_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get available search providers with health status.
    """
    try:
        # Get provider info from registry
        provider_info_list = provider_registry.get_provider_info()

        # Get provider statuses from database
        result = await db.execute(select(ProviderStatus))
        provider_statuses = {ps.provider_id: ps for ps in result.scalars().all()}

        # Combine provider info with status
        enhanced_providers = []
        for provider_info in provider_info_list:
            provider_id = provider_info["id"]
            status_record = provider_statuses.get(provider_id)

            enhanced_provider = ProviderInfo(
                id=provider_info["id"],
                name=provider_info["name"],
                url=provider_info["url"],
                supports_nsfw=provider_info["supports_nsfw"],
                status=status_record.status if status_record else "unknown",
                is_enabled=status_record.is_enabled if status_record else True,
                last_check=status_record.last_check if status_record else None,
                response_time=status_record.response_time if status_record else None,
                uptime_percentage=(
                    status_record.uptime_percentage if status_record else 100
                ),
                consecutive_failures=(
                    status_record.consecutive_failures if status_record else 0
                ),
                is_healthy=status_record.is_healthy if status_record else True,
            )
            enhanced_providers.append(enhanced_provider)

        return enhanced_providers

    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        # Fallback to basic provider info if database query fails
        return provider_registry.get_provider_info()


@router.post("", response_model=SearchResponse)
async def search_manga(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Search for manga across providers.

    Args:
        query: The search query
        current_user: The current user
        db: The database session
    """

    # If provider is specified, use that provider
    if query.provider:
        provider = provider_registry.get_provider(query.provider)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{query.provider}' not found",
            )

        # Check if provider is enabled
        try:
            result = await db.execute(
                select(ProviderStatus).where(
                    ProviderStatus.provider_id == provider.name.lower()
                )
            )
            provider_status = result.scalar_one_or_none()

            if provider_status and not provider_status.is_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Provider '{query.provider}' is currently disabled due to health issues",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Could not check provider status for {query.provider}: {e}")
            # Continue anyway if we can't check status

        # Search using the provider
        try:
            results, total, has_next = await provider.search(
                query=query.query,
                page=query.page,
                limit=query.limit,
            )

            return {
                "results": results,
                "total": total,
                "page": query.page,
                "limit": query.limit,
                "has_next": has_next,
            }
        except Exception as e:
            logger.error(f"Error searching with provider {provider.name}: {e}")
            return {
                "results": [],
                "total": 0,
                "page": query.page,
                "limit": query.limit,
                "has_next": False,
            }

    # If no provider is specified, search across multiple providers
    all_providers = await get_enabled_providers(db)

    # Get user's provider preferences
    user_preferences = await get_user_provider_preferences(db, current_user.id)

    if user_preferences:
        # Use user preferences for prioritization
        priority_providers, regular_providers = (
            prioritize_providers_by_user_preferences(all_providers, user_preferences)
        )
        # Limit regular providers to avoid too many requests
        max_regular_providers = 20
        selected_providers = (
            priority_providers + regular_providers[:max_regular_providers]
        )

        logger.info(
            f"Using user preferences: {len(priority_providers)} favorite providers, {min(len(regular_providers), max_regular_providers)} regular providers"
        )
    else:
        # Fallback to hardcoded prioritization for users without preferences
        priority_providers, generic_providers = apply_fallback_prioritization(
            all_providers
        )
        selected_providers = priority_providers + generic_providers

        logger.info(
            f"Using fallback prioritization: {len(priority_providers)} priority providers, {len(generic_providers)} generic providers"
        )

    # Calculate pagination strategy for multi-provider search
    # We'll use a more sophisticated approach that distributes pagination across providers

    # For multi-provider search, we need to calculate how many results to skip
    # and how many to fetch from each provider to achieve proper pagination
    total_offset = (query.page - 1) * query.limit

    # Estimate results per provider based on historical data or use a reasonable default
    # This is an approximation since we don't know exact counts until we search
    estimated_results_per_provider = 20  # Conservative estimate

    # Calculate which providers to query and with what pagination
    providers_to_query = []
    remaining_offset = total_offset
    remaining_limit = query.limit

    for provider in selected_providers:
        if remaining_limit <= 0:
            break

        # Calculate page and limit for this provider
        provider_page = max(1, (remaining_offset // estimated_results_per_provider) + 1)
        provider_offset_in_page = remaining_offset % estimated_results_per_provider

        # Request more results than needed to account for offset within page
        provider_limit = min(remaining_limit + provider_offset_in_page, 50)

        providers_to_query.append(
            {
                "provider": provider,
                "page": provider_page,
                "limit": provider_limit,
                "skip_results": provider_offset_in_page,
            }
        )

        # Update remaining counts (approximate)
        estimated_provider_results = min(
            provider_limit - provider_offset_in_page, estimated_results_per_provider
        )
        remaining_offset = max(0, remaining_offset - estimated_provider_results)
        remaining_limit -= estimated_provider_results

    logger.info(f"Total providers to search: {len(providers_to_query)}")
    logger.info(
        f"Pagination strategy: page={query.page}, limit={query.limit}, total_offset={total_offset}"
    )

    # Search with selected providers using calculated pagination
    async def search_with_provider(provider_config):
        provider = provider_config["provider"]
        page = provider_config["page"]
        limit = provider_config["limit"]
        skip_results = provider_config["skip_results"]

        try:
            logger.info(
                f"Starting search with provider {provider.name} (page={page}, limit={limit}, skip={skip_results})"
            )
            # Add timeout to prevent slow providers from blocking
            results, total_provider_results, has_next = await asyncio.wait_for(
                provider.search(
                    query=query.query,
                    page=page,
                    limit=limit,
                ),
                timeout=15.0,  # Increased timeout to 15 seconds
            )

            # Skip results if we're in the middle of a page
            if skip_results > 0 and len(results) > skip_results:
                results = results[skip_results:]

            logger.info(
                f"Provider {provider.name} returned {len(results)} results (after skipping {skip_results})"
            )
            if len(results) == 0:
                logger.warning(
                    f"Provider {provider.name} returned no results for query '{query.query}'"
                )
            else:
                # Log first result for debugging
                first_result = results[0]
                logger.info(
                    f"First result from {provider.name}: {first_result.title} - Cover: {bool(first_result.cover_image)}"
                )
            return results, total_provider_results
        except asyncio.TimeoutError:
            logger.warning(f"Provider {provider.name} timed out after 15 seconds")
            return [], 0
        except Exception as e:
            logger.error(f"Error searching with provider {provider.name}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return [], 0

    # Run searches concurrently
    search_tasks = [
        search_with_provider(provider_config) for provider_config in providers_to_query
    ]
    all_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten results and handle exceptions
    flattened_results = []
    successful_providers = 0
    total_estimated_results = 0

    for i, result_tuple in enumerate(all_results):
        provider_name = providers_to_query[i]["provider"].name

        if isinstance(result_tuple, Exception):
            logger.error(
                f"Provider {provider_name} failed with exception: {result_tuple}"
            )
            continue

        if not isinstance(result_tuple, tuple) or len(result_tuple) != 2:
            logger.warning(
                f"Provider {provider_name} returned unexpected result format: {type(result_tuple)}"
            )
            continue

        results, provider_total = result_tuple

        if results and isinstance(results, list):
            logger.info(
                f"Adding {len(results)} results from {provider_name} (total available: {provider_total})"
            )
            flattened_results.extend(results)
            successful_providers += 1
            total_estimated_results += provider_total
        else:
            logger.info(f"Provider {provider_name} returned no results")

    logger.info(
        f"Multi-provider search completed: {successful_providers}/{len(providers_to_query)} providers successful, {len(flattened_results)} total results"
    )

    # Sort results by relevance (title similarity to query)
    def calculate_relevance(result):
        title_lower = result.title.lower()
        query_lower = query.query.lower()
        if query_lower in title_lower:
            return title_lower.index(query_lower)
        return 1000  # Low relevance for non-matching titles

    flattened_results.sort(key=calculate_relevance)

    # For multi-provider pagination, we need to be more careful about the total count
    # Since we're doing distributed pagination, we use the estimated total
    # The actual total might be different, but this provides a reasonable approximation

    # Limit results to requested limit (should already be close due to our pagination logic)
    limited_results = flattened_results[: query.limit]

    # Calculate if there are more results available
    # This is an approximation based on whether we got results from all queried providers
    # and whether any provider indicated more results are available
    has_next = len(flattened_results) >= query.limit or total_estimated_results > (
        query.page * query.limit
    )

    return {
        "results": limited_results,
        "total": max(
            total_estimated_results,
            (query.page - 1) * query.limit + len(limited_results),
        ),
        "page": query.page,
        "limit": query.limit,
        "has_next": has_next,
        "providers_searched": len(providers_to_query),
        "providers_successful": successful_providers,
    }


@router.get("/genres", response_model=List[str])
async def get_genres(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get available manga genres.
    """
    # Common manga genres
    genres = [
        "Action",
        "Adventure",
        "Comedy",
        "Drama",
        "Fantasy",
        "Horror",
        "Mystery",
        "Romance",
        "Sci-Fi",
        "Slice of Life",
        "Sports",
        "Supernatural",
        "Thriller",
        "Ecchi",
        "Harem",
        "Isekai",
        "Josei",
        "Mecha",
        "Military",
        "Music",
        "Parody",
        "Psychological",
        "School",
        "Seinen",
        "Shoujo",
        "Shounen",
        "Yaoi",
        "Yuri",
    ]
    return sorted(genres)


@router.post("/filter", response_model=SearchResponse)
async def filter_manga(
    filter_data: SearchFilter,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Filter manga by various criteria.
    """
    # This would be implemented to filter manga by various criteria
    # For now, return a mock response

    # In a real implementation, this would query the database or external APIs
    # based on the filter criteria

    # Mock response for demonstration purposes
    return {
        "results": [],
        "total": 0,
        "page": page,
        "limit": limit,
        "has_next": False,
    }
