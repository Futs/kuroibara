"""Enhanced search endpoints with MangaUpdates integration."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.services.enhanced_search import enhanced_search_service
from app.core.services.mangaupdates import mangaupdates_service
from app.core.services.tiered_indexing import tiered_search_service
from app.models.user import User
from app.schemas.search import SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/enhanced", response_model=SearchResponse)
async def enhanced_search(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    include_provider_matches: bool = Query(
        True, description="Include provider matches for download sources"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Enhanced search using tiered indexing system.

    This endpoint uses the tiered indexing system with MangaUpdates as primary,
    MadaraDex as secondary, and MangaDex as tertiary sources.

    If include_provider_matches=True, will also search providers to find download sources.
    """
    try:
        # Use the tiered search service
        results = await tiered_search_service.search(query, limit=limit)
        print(
            f"[DEBUG] Tiered search returned {len(results)} results for query '{query}'"
        )
        logger.info(
            f"Tiered search returned {len(results)} results for query '{query}'"
        )

        # Convert results to the expected format
        search_results = []
        for result in results:
            print(
                f"[DEBUG] Processing result: {result.title} from {result.source_indexer}"
            )
            logger.info(
                f"Processing result: {result.title} from {result.source_indexer}"
            )
            # Normalize type field to match enum values
            manga_type = "unknown"
            if result.type:
                type_lower = result.type.lower()
                if type_lower in ["manga", "manhua", "manhwa", "comic"]:
                    manga_type = type_lower
                elif type_lower == "novel":
                    manga_type = "comic"  # Map novel to comic for now
                else:
                    manga_type = "unknown"

            # For indexer results, we need to use a special provider format
            # to indicate this should use the enhanced search add-to-library flow
            provider_name = (
                result.source_indexer.lower() if result.source_indexer else "unknown"
            )
            if provider_name == "mangaupdates":
                provider_name = (
                    "enhanced_mangaupdates"  # Special identifier for frontend
                )

            search_result = {
                "id": result.source_id,
                "title": result.title,
                "alternative_titles": result.alternative_titles or {},
                "description": result.description,
                "cover_image": result.cover_image_url,
                "type": manga_type,
                "status": result.status or "unknown",
                "year": result.year,
                "is_nsfw": result.is_nsfw,
                "genres": result.genres or [],
                "authors": [
                    author.get("name", "") for author in (result.authors or [])
                ],
                "provider": provider_name,
                "url": result.source_url or "",
                "confidence_score": result.confidence_score,
                "in_library": False,  # TODO: Implement library checking
                "provider_matches": [],  # Will be populated if requested
            }

            # Add provider matches for MangaUpdates results
            print(
                f"[DEBUG] Checking provider matches: include={include_provider_matches}, indexer={result.source_indexer}"
            )
            logger.info(
                f"Checking provider matches: include={include_provider_matches}, indexer={result.source_indexer}"
            )
            if (
                include_provider_matches
                and result.source_indexer
                and result.source_indexer.lower() == "mangaupdates"
            ):
                print(f"[DEBUG] Starting provider match search for {result.title}")
                logger.info(f"Starting provider match search for {result.title}")
                try:
                    # Get or create the MangaUpdates entry in DB
                    from sqlalchemy import select

                    from app.models.mangaupdates import MangaUpdatesEntry

                    mu_result = await db.execute(
                        select(MangaUpdatesEntry).where(
                            MangaUpdatesEntry.mu_series_id == result.source_id
                        )
                    )
                    mu_entry = mu_result.scalars().first()
                    print(
                        f"[DEBUG] MU entry from DB: {mu_entry.title if mu_entry else 'None'}"
                    )

                    # If not in DB, create it from the search result
                    if not mu_entry:
                        print(f"[DEBUG] Creating MangaUpdates entry for {result.title}")
                        logger.info(
                            f"Creating MangaUpdates entry for {result.title} (ID: {result.source_id})"
                        )

                        # Create entry using the service method
                        try:
                            series_id = int(result.source_id)
                            async with mangaupdates_service.api as api:
                                mu_entry = (
                                    await mangaupdates_service._create_entry_from_api(
                                        series_id, api, db
                                    )
                                )

                            if mu_entry:
                                print(f"[DEBUG] Created MU entry: {mu_entry.title}")
                                logger.info(
                                    f"Created MangaUpdates entry: {mu_entry.title}"
                                )
                            else:
                                print("[DEBUG] Failed to create MU entry")
                                logger.warning(
                                    f"Failed to create MangaUpdates entry "
                                    f"for series {series_id}"
                                )
                        except Exception as e:
                            print(f"[DEBUG] Exception creating MU entry: {e}")
                            logger.error(f"Failed to create MangaUpdates entry: {e}")

                    print(
                        f"[DEBUG] About to check if mu_entry exists: "
                        f"{mu_entry is not None}"
                    )
                    if mu_entry:
                        print("[DEBUG] MU entry exists, starting provider matching")
                        # Find provider matches
                        from app.core.services.enhanced_search import ProviderMatcher

                        matcher = ProviderMatcher()
                        print(
                            "[DEBUG] Created ProviderMatcher, "
                            "calling find_provider_matches"
                        )
                        provider_matches = await matcher.find_provider_matches(
                            mu_entry, max_providers=5
                        )
                        print(
                            f"[DEBUG] Provider matching returned "
                            f"{len(provider_matches)} matches"
                        )
                        search_result["provider_matches"] = provider_matches
                        logger.info(
                            f"Found {len(provider_matches)} provider matches "
                            f"for {result.title}"
                        )
                    else:
                        print("[DEBUG] MU entry is None, skipping provider matching")

                except Exception as e:
                    logger.warning(
                        f"Failed to get provider matches for {result.title}: {e}",
                        exc_info=True,
                    )

            search_results.append(search_result)

        # Calculate pagination
        total_results = len(search_results)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = search_results[start_idx:end_idx]

        return SearchResponse(
            results=paginated_results,
            total=total_results,
            page=page,
            limit=limit,
            has_next=end_idx < total_results,
        )

    except Exception as e:
        logger.error(f"Enhanced search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/indexers/health")
async def get_indexer_health(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get health status of all indexers in the tiered system.

    Returns the connection status and response times for each indexer.
    """
    try:
        health_results = await tiered_search_service.test_all_indexers()

        # Format the health results
        indexer_status = {}
        healthy_count = 0

        for indexer_name, (is_healthy, message) in health_results.items():
            indexer_status[indexer_name] = {
                "healthy": is_healthy,
                "message": message,
                "tier": (
                    "primary"
                    if indexer_name == "MangaUpdates"
                    else "secondary" if indexer_name == "MadaraDex" else "tertiary"
                ),
            }
            if is_healthy:
                healthy_count += 1

        return {
            "indexers": indexer_status,
            "summary": {
                "total_indexers": len(health_results),
                "healthy_indexers": healthy_count,
                "overall_health": (
                    healthy_count / len(health_results) if health_results else 0
                ),
            },
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/enhanced/add-from-mangaupdates")
async def add_to_library_from_mangaupdates(
    mu_entry_id: str,
    selected_provider_match: Optional[Dict] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add manga to library from MangaUpdates entry.

    Args:
        mu_entry_id: MangaUpdates entry ID
        selected_provider_match: Optional provider match for download source
    """
    try:
        manga = await enhanced_search_service.add_to_library_from_mu(
            mu_entry_id=mu_entry_id,
            user_id=str(current_user.id),
            db=db,
            selected_provider_match=selected_provider_match,
        )

        return {
            "message": "Manga added to library successfully",
            "manga_id": str(manga.id),
            "title": manga.title,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add manga from MangaUpdates: {e}")
        raise HTTPException(status_code=500, detail="Failed to add manga to library")


@router.get("/mangaupdates/{series_id}")
async def get_mangaupdates_details(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get detailed information about a MangaUpdates series.

    This endpoint fetches comprehensive metadata from MangaUpdates
    and finds available provider matches.
    """
    try:
        # Get or create MangaUpdates entry
        mu_entry = await mangaupdates_service.search_and_create_entry(
            query=f"series_id:{series_id}",  # Special query format for direct ID lookup
            db=db,
            auto_select_best=True,
        )

        if not mu_entry:
            raise HTTPException(status_code=404, detail="Series not found")

        # Find provider matches
        from app.core.services.enhanced_search import ProviderMatcher

        matcher = ProviderMatcher()
        provider_matches = await matcher.find_provider_matches(
            mu_entry, max_providers=10
        )

        # Check library status
        from app.core.services.enhanced_search import EnhancedSearchResult

        result = EnhancedSearchResult(mu_entry)
        result.provider_matches = provider_matches
        result.in_library, result.library_manga = (
            await enhanced_search_service._check_library_status(
                mu_entry, str(current_user.id), db
            )
        )

        return {
            "mu_entry": {
                "id": str(mu_entry.id),
                "mu_series_id": mu_entry.mu_series_id,
                "title": mu_entry.title,
                "alternative_titles": mu_entry.alternative_titles,
                "description": mu_entry.description,
                "cover_image_url": mu_entry.cover_image_url,
                "type": mu_entry.type,
                "status": mu_entry.status,
                "year": mu_entry.year,
                "is_nsfw": mu_entry.is_nsfw,
                "genres": mu_entry.genres,
                "categories": mu_entry.categories,
                "authors": mu_entry.authors,
                "artists": mu_entry.artists,
                "rating": mu_entry.rating,
                "rating_count": mu_entry.rating_count,
                "popularity_rank": mu_entry.popularity_rank,
                "latest_chapter": mu_entry.latest_chapter,
                "total_chapters": mu_entry.total_chapters,
            },
            "provider_matches": provider_matches,
            "in_library": result.in_library,
            "library_manga_id": (
                str(result.library_manga.id) if result.library_manga else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MangaUpdates details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch series details")


@router.post("/refresh-mangaupdates")
async def refresh_mangaupdates_entries(
    batch_size: int = Query(
        10, ge=1, le=50, description="Number of entries to refresh"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Manually trigger refresh of stale MangaUpdates entries.

    This endpoint refreshes entries that haven't been updated recently
    with fresh data from the MangaUpdates API.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        refreshed_count = await mangaupdates_service.refresh_stale_entries(
            db, batch_size
        )

        return {
            "message": f"Refreshed {refreshed_count} MangaUpdates entries",
            "refreshed_count": refreshed_count,
        }
    except Exception as e:
        logger.error(f"Failed to refresh MangaUpdates entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh entries")


@router.get("/provider-matches/{mu_entry_id}")
async def get_provider_matches(
    mu_entry_id: UUID,
    max_providers: int = Query(
        5, ge=1, le=20, description="Maximum providers to search"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get provider matches for a specific MangaUpdates entry.

    This endpoint searches configured providers for content matching
    the given MangaUpdates entry.
    """
    try:
        from sqlalchemy import select

        from app.models.mangaupdates import MangaUpdatesEntry

        # Get MangaUpdates entry
        result = await db.execute(
            select(MangaUpdatesEntry).where(MangaUpdatesEntry.id == mu_entry_id)
        )
        mu_entry = result.scalars().first()

        if not mu_entry:
            raise HTTPException(status_code=404, detail="MangaUpdates entry not found")

        # Find provider matches
        from app.core.services.enhanced_search import ProviderMatcher

        matcher = ProviderMatcher()
        provider_matches = await matcher.find_provider_matches(mu_entry, max_providers)

        return {
            "mu_entry_id": str(mu_entry_id),
            "title": mu_entry.title,
            "provider_matches": provider_matches,
            "total_matches": len(provider_matches),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to find provider matches")


@router.post("/create-mapping")
async def create_manga_mapping(
    manga_id: UUID,
    mu_entry_id: UUID,
    confidence_score: float = Query(1.0, ge=0.0, le=1.0),
    mapping_source: str = Query("manual", description="Source of the mapping"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a mapping between existing manga and MangaUpdates entry.

    This endpoint allows linking existing manga in the library
    with MangaUpdates entries for enhanced metadata.
    """
    try:
        from sqlalchemy import select

        from app.models.manga import Manga
        from app.models.mangaupdates import MangaUpdatesEntry

        # Verify manga exists and user has access
        manga_result = await db.execute(select(Manga).where(Manga.id == manga_id))
        manga = manga_result.scalars().first()

        if not manga:
            raise HTTPException(status_code=404, detail="Manga not found")

        # Verify MangaUpdates entry exists
        mu_result = await db.execute(
            select(MangaUpdatesEntry).where(MangaUpdatesEntry.id == mu_entry_id)
        )
        mu_entry = mu_result.scalars().first()

        if not mu_entry:
            raise HTTPException(status_code=404, detail="MangaUpdates entry not found")

        # Create mapping
        mapping = await mangaupdates_service.create_manga_mapping(
            manga=manga,
            mu_entry=mu_entry,
            db=db,
            confidence_score=confidence_score,
            mapping_source=mapping_source,
        )

        return {
            "message": "Mapping created successfully",
            "mapping_id": str(mapping.id),
            "manga_title": manga.title,
            "mu_title": mu_entry.title,
            "confidence_score": confidence_score,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mapping")


@router.get("/search-suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get search suggestions based on partial query.

    This endpoint provides autocomplete suggestions from MangaUpdates
    to help users find content more easily.
    """
    try:
        # For now, return a simple search to get suggestions
        # In the future, this could use a dedicated autocomplete API
        search_results = await enhanced_search_service.search(
            query=query,
            db=db,
            page=1,
            limit=limit,
            user_id=str(current_user.id),
            include_provider_matches=False,  # Skip provider matching for suggestions
        )

        # Extract just the titles for suggestions
        suggestions = []
        for result in search_results.results:
            suggestions.append(
                {
                    "title": result.title,
                    "mu_entry_id": result.id,
                    "year": result.year,
                    "type": result.type,
                    "cover_image": result.cover_image,
                }
            )

        return {"query": query, "suggestions": suggestions}

    except Exception as e:
        logger.error(f"Failed to get search suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")
