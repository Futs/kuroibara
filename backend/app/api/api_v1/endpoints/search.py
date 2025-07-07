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
    all_providers = provider_registry.get_all_providers()

    # Get user's provider preferences
    user_preferences = await get_user_provider_preferences(db, current_user.id)

    if user_preferences:
        # Use user preferences for prioritization
        priority_providers, regular_providers = (
            prioritize_providers_by_user_preferences(all_providers, user_preferences)
        )
        # Limit regular providers to avoid too many requests
        max_regular_providers = 10
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

    # Give each provider a reasonable limit to ensure we get good results
    # Don't divide by number of providers as this makes each provider return too few results
    results_per_provider = min(
        query.limit, 10
    )  # Each provider can return up to 10 results

    logger.info(f"Total providers to search: {len(selected_providers)}")
    logger.info(f"Selected providers: {[p.name for p in selected_providers]}")
    logger.info(f"Results per provider: {results_per_provider}")

    # Search with all selected providers concurrently with timeout
    async def search_with_provider(provider):
        try:
            logger.info(
                f"Starting search with provider {provider.name} (class: {provider.__class__.__name__})"
            )
            # Add timeout to prevent slow providers from blocking
            results, _, _ = await asyncio.wait_for(
                provider.search(
                    query=query.query,
                    page=1,  # Always use page 1 for multi-provider search
                    limit=results_per_provider,
                ),
                timeout=15.0,  # Increased timeout to 15 seconds
            )
            logger.info(f"Provider {provider.name} returned {len(results)} results")
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
            return results
        except asyncio.TimeoutError:
            logger.warning(f"Provider {provider.name} timed out after 15 seconds")
            return []
        except Exception as e:
            logger.error(f"Error searching with provider {provider.name}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    # Run searches concurrently
    search_tasks = [search_with_provider(provider) for provider in selected_providers]
    all_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten results and handle exceptions
    flattened_results = []
    successful_providers = 0
    for i, results in enumerate(all_results):
        if isinstance(results, Exception):
            logger.error(
                f"Provider {selected_providers[i].name} failed with exception: {results}"
            )
            continue
        if results and isinstance(results, list):
            logger.info(
                f"Adding {len(results)} results from {selected_providers[i].name}"
            )
            flattened_results.extend(results)
            successful_providers += 1
        elif results:
            logger.warning(
                f"Provider {selected_providers[i].name} returned non-list results: {type(results)}"
            )
        else:
            logger.info(f"Provider {selected_providers[i].name} returned no results")

    logger.info(
        f"Multi-provider search completed: {successful_providers}/{len(selected_providers)} providers successful, {len(flattened_results)} total results"
    )

    # Sort results by relevance (title similarity to query)
    def calculate_relevance(result):
        title_lower = result.title.lower()
        query_lower = query.query.lower()
        if query_lower in title_lower:
            return title_lower.index(query_lower)
        return 1000  # Low relevance for non-matching titles

    flattened_results.sort(key=calculate_relevance)

    # Limit results to requested limit
    limited_results = flattened_results[: query.limit]

    return {
        "results": limited_results,
        "total": len(flattened_results),
        "page": query.page,
        "limit": query.limit,
        "has_next": len(flattened_results) > query.limit,
        "providers_searched": len(selected_providers),
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
