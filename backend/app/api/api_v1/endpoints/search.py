import asyncio
import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.core.providers.user_preferences import (
    apply_fallback_prioritization,
    get_user_provider_preferences,
    prioritize_providers_by_user_preferences,
)
from app.models.library import MangaUserLibrary
from app.models.manga import Manga
from app.models.provider import ProviderStatus
from app.models.user import User
from app.schemas.search import (
    ProviderInfo,
    SearchFilter,
    SearchQuery,
    SearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_library_status(
    search_results: List[Any], user_id: str, db: AsyncSession
) -> List[Any]:
    """
    Check if search results are already in the user's library and add in_library field.

    Args:
        search_results: List of search result objects
        user_id: Current user ID
        db: Database session

    Returns:
        List of search results with in_library field added
    """
    if not search_results:
        return search_results

    try:
        # Get all manga titles and providers from search results
        manga_lookup = {}
        for result in search_results:
            # Create a lookup key based on title and provider
            key = (result.title.lower().strip(), result.provider)
            manga_lookup[key] = result

        # Query database for existing manga with matching external_id and provider
        # This is more reliable than title matching for external manga
        external_lookups = []
        title_lookups = []

        for result in search_results:
            # For external manga, check by provider + external_id (most reliable)
            if (
                hasattr(result, "id")
                and hasattr(result, "provider")
                and result.provider
                and result.id
            ):
                external_lookups.append((result.provider, result.id))
            # Also check by title as fallback
            title_lookups.append(result.title)

        existing_manga = []

        # First, try to find by external_id and provider (most reliable)
        if external_lookups:
            from sqlalchemy import or_

            external_conditions = []
            for provider, external_id in external_lookups:
                external_conditions.append(
                    (Manga.provider == provider) & (Manga.external_id == external_id)
                )

            if external_conditions:
                external_query = select(Manga).where(or_(*external_conditions))
                external_result = await db.execute(external_query)
                existing_manga.extend(external_result.scalars().all())

        # Also check by title for any manga not found by external_id
        if title_lookups:
            title_query = select(Manga).where(Manga.title.in_(title_lookups))
            title_result = await db.execute(title_query)
            title_manga = title_result.scalars().all()

            # Add title-matched manga that weren't already found by external_id
            existing_external_ids = {
                (m.provider, m.external_id)
                for m in existing_manga
                if m.provider and m.external_id
            }
            for manga in title_manga:
                if (manga.provider, manga.external_id) not in existing_external_ids:
                    existing_manga.append(manga)

        # Get manga IDs that are in the user's library
        if existing_manga:
            manga_ids = [manga.id for manga in existing_manga]
            library_query = select(MangaUserLibrary.manga_id).where(
                MangaUserLibrary.user_id == user_id,
                MangaUserLibrary.manga_id.in_(manga_ids),
            )
            library_result = await db.execute(library_query)
            library_manga_ids = set(library_result.scalars().all())

            # Create mappings for library checking
            external_to_manga_id = {}
            title_to_manga_id = {}

            for manga in existing_manga:
                # Map by external_id + provider (most reliable)
                if manga.provider and manga.external_id:
                    external_key = (manga.provider, manga.external_id)
                    external_to_manga_id[external_key] = manga.id

                # Map by title + provider (fallback)
                title_key = (manga.title.lower().strip(), manga.provider)
                title_to_manga_id[title_key] = manga.id
        else:
            library_manga_ids = set()
            external_to_manga_id = {}
            title_to_manga_id = {}

        # Add in_library field to each search result
        for result in search_results:
            manga_id = None

            # First try external_id + provider lookup (most reliable)
            if (
                hasattr(result, "id")
                and hasattr(result, "provider")
                and result.provider
                and result.id
            ):
                external_key = (result.provider, result.id)
                manga_id = external_to_manga_id.get(external_key)

            # Fallback to title + provider lookup
            if manga_id is None:
                title_key = (result.title.lower().strip(), result.provider)
                manga_id = title_to_manga_id.get(title_key)

            result.in_library = manga_id is not None and manga_id in library_manga_ids

        return search_results

    except Exception as e:
        logger.error(f"Error checking library status: {e}")
        # If there's an error, just return results without library status
        for result in search_results:
            result.in_library = False
        return search_results


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
                requires_flaresolverr=provider_info["requires_flaresolverr"],
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

            # Check library status for single provider results
            results_with_library_status = await check_library_status(
                results, current_user.id, db
            )

            return {
                "results": results_with_library_status,
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

    # Calculate pagination for multi-provider search
    # We need to gather enough results to satisfy the requested page
    # Strategy: Get multiple pages from providers to ensure we have enough results

    # Calculate how many results we need to skip (offset)
    offset = (query.page - 1) * query.limit

    # Calculate how many total results we need to collect
    # We need offset + limit results to properly paginate
    total_needed = offset + query.limit

    # Give each provider a reasonable limit to ensure we get good results
    # Increase the limit per provider to gather more results for pagination
    results_per_provider = min(
        max(query.limit, 20), 50  # Each provider can return 20-50 results
    )

    # Calculate which page to request from each provider
    # For multi-provider search, we'll request multiple pages if needed
    max_pages_per_provider = max(
        1, (total_needed // len(selected_providers) // results_per_provider) + 1
    )
    max_pages_per_provider = min(
        max_pages_per_provider, 3
    )  # Limit to 3 pages per provider

    logger.info(f"Total providers to search: {len(selected_providers)}")
    logger.info(f"Selected providers: {[p.name for p in selected_providers]}")
    logger.info(f"Results per provider: {results_per_provider}")
    logger.info(f"Max pages per provider: {max_pages_per_provider}")
    logger.info(
        f"Requested page: {query.page}, offset: {offset}, total needed: {total_needed}"
    )

    # Search with all selected providers concurrently with timeout
    async def search_with_provider(provider):
        try:
            logger.info(
                f"Starting search with provider {provider.name} (class: {provider.__class__.__name__})"
            )

            all_results = []
            provider_has_more = False

            # Get multiple pages from this provider if needed
            for page_num in range(1, max_pages_per_provider + 1):
                try:
                    # Add timeout to prevent slow providers from blocking
                    results, total, has_next = await asyncio.wait_for(
                        provider.search(
                            query=query.query,
                            page=page_num,
                            limit=results_per_provider,
                        ),
                        timeout=15.0,  # Increased timeout to 15 seconds
                    )

                    all_results.extend(results)
                    provider_has_more = has_next

                    # If this page returned fewer results than requested, no point getting more pages
                    if len(results) < results_per_provider:
                        break

                    # If we have enough results for this provider, stop
                    if len(all_results) >= results_per_provider * 2:
                        break

                except Exception as e:
                    logger.warning(
                        f"Error getting page {page_num} from {provider.name}: {e}"
                    )
                    break

            results = all_results
            logger.info(
                f"Provider {provider.name} returned {len(results)} results across {max_pages_per_provider} pages"
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
            return results, provider_has_more
        except asyncio.TimeoutError:
            logger.warning(f"Provider {provider.name} timed out after 15 seconds")
            return [], False
        except Exception as e:
            logger.error(f"Error searching with provider {provider.name}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return [], False

    # Run searches concurrently
    search_tasks = [search_with_provider(provider) for provider in selected_providers]
    all_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Flatten results and handle exceptions
    flattened_results = []
    successful_providers = 0
    any_provider_has_more = False

    for i, result in enumerate(all_results):
        if isinstance(result, Exception):
            logger.error(
                f"Provider {selected_providers[i].name} failed with exception: {result}"
            )
            continue

        # Handle tuple return (results, has_more)
        if isinstance(result, tuple) and len(result) == 2:
            results, has_more = result
            if results and isinstance(results, list):
                logger.info(
                    f"Adding {len(results)} results from {selected_providers[i].name}"
                )
                flattened_results.extend(results)
                successful_providers += 1
                any_provider_has_more = any_provider_has_more or has_more
            else:
                logger.info(
                    f"Provider {selected_providers[i].name} returned no results"
                )
        # Handle legacy single return (just results)
        elif result and isinstance(result, list):
            logger.info(
                f"Adding {len(result)} results from {selected_providers[i].name} (legacy format)"
            )
            flattened_results.extend(result)
            successful_providers += 1
        elif result:
            logger.warning(
                f"Provider {selected_providers[i].name} returned unexpected format: {type(result)}"
            )
        else:
            logger.info(f"Provider {selected_providers[i].name} returned no results")

    logger.info(
        f"Multi-provider search completed: {successful_providers}/{len(selected_providers)} providers successful, {len(flattened_results)} total results"
    )

    # Remove duplicates based on title and provider
    seen = set()
    unique_results = []
    for result in flattened_results:
        key = (result.title.lower(), result.provider)
        if key not in seen:
            seen.add(key)
            unique_results.append(result)

    flattened_results = unique_results
    logger.info(f"After deduplication: {len(flattened_results)} unique results")

    # Sort results by relevance (title similarity to query)
    def calculate_relevance(result):
        title_lower = result.title.lower()
        query_lower = query.query.lower()
        if query_lower in title_lower:
            return title_lower.index(query_lower)
        return 1000  # Low relevance for non-matching titles

    flattened_results.sort(key=calculate_relevance)

    # Implement proper pagination
    total_results = len(flattened_results)
    start_index = offset
    end_index = offset + query.limit

    # Get the results for the requested page
    paginated_results = flattened_results[start_index:end_index]

    # Calculate if there are more results
    # There are more results if:
    # 1. We have more results in our current collection beyond this page
    # 2. Any provider indicated they have more results (suggesting we could get more by fetching additional pages)
    has_next = end_index < total_results or any_provider_has_more

    logger.info(
        f"Pagination: total={total_results}, offset={offset}, page_size={len(paginated_results)}, has_next={has_next}"
    )

    # Check library status for paginated results
    paginated_results_with_library_status = await check_library_status(
        paginated_results, current_user.id, db
    )

    return {
        "results": paginated_results_with_library_status,
        "total": total_results,
        "page": query.page,
        "limit": query.limit,
        "has_next": has_next,
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
