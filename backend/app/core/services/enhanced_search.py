"""Enhanced search service integrating MangaUpdates with provider matching."""

import asyncio
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.registry import provider_registry
from app.core.services.mangaupdates import mangaupdates_service
from app.models.manga import Manga
from app.models.mangaupdates import MangaUpdatesEntry, MangaUpdatesMapping
from app.schemas.search import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class EnhancedSearchResult:
    """Enhanced search result with MangaUpdates metadata and provider availability."""

    def __init__(self, mu_entry: MangaUpdatesEntry):
        self.mu_entry = mu_entry
        self.provider_matches: List[Dict] = []
        self.confidence_score: float = 0.0
        self.in_library: bool = False
        self.library_manga: Optional[Manga] = None

    def to_search_result(self) -> SearchResult:
        """Convert to standard SearchResult schema."""
        return SearchResult(
            id=str(self.mu_entry.id),
            title=self.mu_entry.title,
            alternative_titles=self.mu_entry.alternative_titles or {},
            description=self.mu_entry.description,
            cover_image=self.mu_entry.cover_image_url,
            type=self.mu_entry.type or "unknown",
            status=self.mu_entry.status or "unknown",
            year=self.mu_entry.year,
            is_nsfw=self.mu_entry.is_nsfw,
            genres=self.mu_entry.genres or [],
            authors=[
                author.get("name", "") for author in (self.mu_entry.authors or [])
            ],
            provider="enhanced_mangaupdates",
            url=self.mu_entry.mu_url or "",
            in_library=self.in_library,
            extra={
                "mu_series_id": self.mu_entry.mu_series_id,
                "rating": self.mu_entry.rating,
                "rating_count": self.mu_entry.rating_count,
                "popularity_rank": self.mu_entry.popularity_rank,
                "provider_matches": self.provider_matches,
                "confidence_score": self.confidence_score,
                "categories": self.mu_entry.categories or [],
                "latest_chapter": self.mu_entry.latest_chapter,
                "total_chapters": self.mu_entry.total_chapters,
            },
        )


class ProviderMatcher:
    """Service for matching MangaUpdates entries with provider content."""

    def __init__(self):
        self.similarity_threshold = 0.7  # Minimum similarity for auto-matching

    async def find_provider_matches(
        self, mu_entry: MangaUpdatesEntry, max_providers: int = 5
    ) -> List[Dict]:
        """Find matching content across providers for a MangaUpdates entry."""
        logger.info(f"[PROVIDER_MATCH] Starting provider matching for {mu_entry.title}")
        matches = []

        # Get available providers
        providers = provider_registry.get_all_providers()
        max_search = min(max_providers, len(providers))
        logger.info(
            f"[PROVIDER_MATCH] Found {len(providers)} total providers, "
            f"will search {max_search}"
        )

        # Search each provider
        for i, provider in enumerate(providers[:max_providers]):
            try:
                logger.info(
                    f"[PROVIDER_MATCH] Searching provider {i + 1}/{max_search}: "
                    f"{provider.name}"
                )
                provider_matches = await self._search_provider(provider, mu_entry)
                if provider_matches:
                    logger.info(
                        f"[PROVIDER_MATCH] Found {len(provider_matches)} "
                        f"matches from {provider.name}"
                    )
                    matches.extend(provider_matches)
                else:
                    logger.info(f"[PROVIDER_MATCH] No matches from {provider.name}")
            except Exception as e:
                logger.warning(
                    f"[PROVIDER_MATCH] Error searching provider "
                    f"{provider.name}: {e}"
                )

        # Sort by confidence score
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        logger.info(
            f"[PROVIDER_MATCH] Completed provider matching, "
            f"found {len(matches)} total matches"
        )
        return matches[:10]  # Return top 10 matches

    async def _search_provider(
        self, provider, mu_entry: MangaUpdatesEntry
    ) -> List[Dict]:
        """Search a specific provider for matches."""
        matches = []

        # Try different search terms
        search_terms = [mu_entry.title]

        # Add alternative titles
        if mu_entry.alternative_titles:
            search_terms.extend(mu_entry.alternative_titles.values())

        for term in search_terms[:3]:  # Limit to avoid rate limiting
            try:
                results, _, _ = await provider.search(term, limit=5)

                for result in results:
                    confidence = self._calculate_confidence(mu_entry, result)
                    if confidence >= self.similarity_threshold:
                        matches.append(
                            {
                                "provider": provider.name,
                                "external_id": result.id,
                                "title": result.title,
                                "url": result.url,
                                "confidence": confidence,
                                "search_term": term,
                            }
                        )

                # Add small delay to respect rate limits
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.debug(f"Error searching {provider.name} with term '{term}': {e}")

        return matches

    def _calculate_confidence(
        self, mu_entry: MangaUpdatesEntry, provider_result
    ) -> float:
        """Calculate confidence score for a match."""
        # Title similarity (primary factor)
        title_similarity = SequenceMatcher(
            None, mu_entry.title.lower(), provider_result.title.lower()
        ).ratio()

        confidence = title_similarity * 0.7  # 70% weight for title

        # Alternative title similarity
        if mu_entry.alternative_titles:
            alt_similarities = []
            for alt_title in mu_entry.alternative_titles.values():
                alt_sim = SequenceMatcher(
                    None, alt_title.lower(), provider_result.title.lower()
                ).ratio()
                alt_similarities.append(alt_sim)

            if alt_similarities:
                confidence += (
                    max(alt_similarities) * 0.2
                )  # 20% weight for best alt title

        # Year similarity (if available)
        if (
            mu_entry.year
            and hasattr(provider_result, "year")
            and provider_result.year
            and abs(mu_entry.year - provider_result.year) <= 1
        ):
            confidence += 0.1  # 10% weight for year match

        return min(confidence, 1.0)


class EnhancedSearchService:
    """Enhanced search service using MangaUpdates as primary metadata source."""

    def __init__(self):
        self.provider_matcher = ProviderMatcher()

    async def search(
        self,
        query: str,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        user_id: Optional[str] = None,
        include_provider_matches: bool = True,
    ) -> SearchResponse:
        """Enhanced search using MangaUpdates as primary source."""

        # Search MangaUpdates
        async with mangaupdates_service.api as api:
            mu_results = await api.search_series(query, page, limit)

        if not mu_results.get("results"):
            return SearchResponse(
                results=[], total=0, page=page, limit=limit, has_next=False
            )

        # Process results
        enhanced_results = []

        for mu_result in mu_results["results"]:
            try:
                # Get or create MangaUpdates entry
                series_id = mu_result["record"]["series_id"]
                mu_entry = await self._get_or_create_mu_entry(series_id, db)

                if not mu_entry:
                    continue

                # Create enhanced result
                enhanced_result = EnhancedSearchResult(mu_entry)

                # Check if in library
                if user_id:
                    enhanced_result.in_library, enhanced_result.library_manga = (
                        await self._check_library_status(mu_entry, user_id, db)
                    )

                # Find provider matches if requested
                if include_provider_matches:
                    enhanced_result.provider_matches = (
                        await self.provider_matcher.find_provider_matches(
                            mu_entry, max_providers=3
                        )
                    )

                    # Calculate overall confidence based on provider availability
                    if enhanced_result.provider_matches:
                        enhanced_result.confidence_score = max(
                            match["confidence"]
                            for match in enhanced_result.provider_matches
                        )

                enhanced_results.append(enhanced_result)

            except Exception as e:
                logger.error(f"Error processing MangaUpdates result {mu_result}: {e}")

        # Convert to SearchResult objects
        search_results = [result.to_search_result() for result in enhanced_results]

        return SearchResponse(
            results=search_results,
            total=mu_results.get("total_hits", len(search_results)),
            page=page,
            limit=limit,
            has_next=len(search_results) == limit,
        )

    async def _get_or_create_mu_entry(
        self, series_id: int, db: AsyncSession
    ) -> Optional[MangaUpdatesEntry]:
        """Get existing or create new MangaUpdates entry."""
        # Check if entry exists
        result = await db.execute(
            select(MangaUpdatesEntry).where(
                MangaUpdatesEntry.mu_series_id == str(series_id)
            )
        )
        existing_entry = result.scalars().first()

        if existing_entry:
            # Check if needs refresh
            if existing_entry.needs_refresh():
                async with mangaupdates_service.api as api:
                    await mangaupdates_service._update_entry_from_api(
                        existing_entry, api, db
                    )
            return existing_entry

        # Create new entry
        async with mangaupdates_service.api as api:
            return await mangaupdates_service._create_entry_from_api(series_id, api, db)

    async def _check_library_status(
        self, mu_entry: MangaUpdatesEntry, user_id: str, db: AsyncSession
    ) -> Tuple[bool, Optional[Manga]]:
        """Check if MangaUpdates entry is in user's library."""
        # Look for existing mapping
        result = await db.execute(
            select(MangaUpdatesMapping, Manga)
            .join(Manga, MangaUpdatesMapping.manga_id == Manga.id)
            .where(MangaUpdatesMapping.mu_entry_id == mu_entry.id)
        )

        mapping_and_manga = result.first()
        if mapping_and_manga:
            mapping, manga = mapping_and_manga

            # Check if manga is in user's library
            from app.models.library import MangaUserLibrary

            library_result = await db.execute(
                select(MangaUserLibrary).where(
                    (MangaUserLibrary.manga_id == manga.id)
                    & (MangaUserLibrary.user_id == user_id)
                )
            )

            if library_result.scalars().first():
                return True, manga

        return False, None

    async def add_to_library_from_mu(
        self,
        mu_entry_id: str,
        user_id: str,
        db: AsyncSession,
        selected_provider_match: Optional[Dict] = None,
    ) -> Manga:
        """Add manga to library from MangaUpdates entry."""
        # Try to parse as UUID first, then as series ID
        logger.info(f"Starting add_from_mangaupdates with mu_entry_id: {mu_entry_id}")

        try:
            # Try UUID lookup first
            logger.info(f"Trying UUID lookup for: {mu_entry_id}")
            result = await db.execute(
                select(MangaUpdatesEntry).where(MangaUpdatesEntry.id == mu_entry_id)
            )
            mu_entry = result.scalars().first()
            logger.info(f"UUID lookup result: {mu_entry}")
        except Exception as e:
            logger.info(f"UUID lookup failed: {e}")
            mu_entry = None

        if not mu_entry:
            # Try series ID lookup (now as string)
            logger.info(f"Trying series ID lookup for: {mu_entry_id}")
            result = await db.execute(
                select(MangaUpdatesEntry).where(
                    MangaUpdatesEntry.mu_series_id == str(mu_entry_id)
                )
            )
            mu_entry = result.scalars().first()
            logger.info(f"Series ID lookup result: {mu_entry}")

            if not mu_entry:
                # Create new entry from MangaUpdates API using direct series ID
                logger.info("No existing entry found, creating new one")
                from app.core.services.mangaupdates import mangaupdates_service

                try:
                    logger.info(f"Converting mu_entry_id '{mu_entry_id}' to int")
                    series_id = int(mu_entry_id)
                    logger.info(f"Successfully converted to series_id: {series_id}")

                    logger.info("Opening mangaupdates_service.api context manager")
                    async with mangaupdates_service.api as api:
                        logger.info(f"Context manager opened, API object: {type(api)}")
                        logger.info(
                            f"Calling mangaupdates_service._create_entry_from_api({series_id}, api, db)"
                        )
                        mu_entry = await mangaupdates_service._create_entry_from_api(
                            series_id, api, db
                        )
                        logger.info(
                            f"_create_entry_from_api returned: {type(mu_entry)} - {mu_entry}"
                        )

                    logger.info(f"Context manager closed, final result: {mu_entry}")

                except ValueError as e:
                    logger.error(
                        f"ValueError converting mu_entry_id '{mu_entry_id}' to int: {e}"
                    )
                    # If mu_entry_id is not a valid integer, try searching
                    logger.info(
                        f"Falling back to search_and_create_entry with query: {mu_entry_id}"
                    )
                    mu_entry = await mangaupdates_service.search_and_create_entry(
                        query=mu_entry_id, db=db, auto_select_best=True
                    )
                    logger.info(f"search_and_create_entry returned: {mu_entry}")
                except Exception as e:
                    logger.error(f"Error creating MangaUpdates entry: {e}")
                    import traceback

                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise

            if not mu_entry:
                raise ValueError(
                    f"Could not find or create MangaUpdates entry for ID: {mu_entry_id}"
                )

        # Check if already mapped to a manga
        mapping_result = await db.execute(
            select(MangaUpdatesMapping, Manga)
            .join(Manga, MangaUpdatesMapping.manga_id == Manga.id)
            .where(MangaUpdatesMapping.mu_entry_id == mu_entry.id)
        )

        mapping_and_manga = mapping_result.first()
        if mapping_and_manga:
            mapping, existing_manga = mapping_and_manga

            # Add to user's library if not already there
            from app.models.library import MangaUserLibrary

            library_result = await db.execute(
                select(MangaUserLibrary).where(
                    (MangaUserLibrary.manga_id == existing_manga.id)
                    & (MangaUserLibrary.user_id == user_id)
                )
            )

            if not library_result.scalars().first():
                library_item = MangaUserLibrary(
                    user_id=user_id, manga_id=existing_manga.id
                )
                db.add(library_item)
                await db.commit()

            return existing_manga

        # Create new manga from MangaUpdates data
        manga_data = {
            "title": mu_entry.title,
            "alternative_titles": mu_entry.alternative_titles,
            "description": mu_entry.description,
            "cover_image": mu_entry.cover_image_url,
            "type": mu_entry.type or "unknown",
            "status": mu_entry.status or "unknown",
            "year": mu_entry.year,
            "is_nsfw": mu_entry.is_nsfw,
        }

        # If a provider match was selected, add provider info
        if selected_provider_match:
            manga_data.update(
                {
                    "provider": selected_provider_match["provider"],
                    "external_id": selected_provider_match["external_id"],
                    "external_url": selected_provider_match["url"],
                }
            )

        manga = Manga(**manga_data)
        db.add(manga)
        await db.flush()  # Get the ID

        # Create mapping
        mapping = MangaUpdatesMapping(
            manga_id=manga.id,
            mu_entry_id=mu_entry.id,
            confidence_score=(
                selected_provider_match.get("confidence", 1.0)
                if selected_provider_match
                else 1.0
            ),
            mapping_source="manual",
            verified_by_user=True,
        )
        db.add(mapping)

        # Add to user's library
        from app.models.library import MangaUserLibrary

        library_item = MangaUserLibrary(user_id=user_id, manga_id=manga.id)
        db.add(library_item)

        # Fetch chapters from provider if one was selected
        if selected_provider_match:
            from app.core.providers.registry import provider_registry
            from app.models.manga import Chapter

            try:
                provider_name = selected_provider_match["provider"]
                external_id = selected_provider_match["external_id"]

                logger.info(
                    f"Fetching chapters from provider {provider_name} for manga {external_id}"
                )

                # Get the provider
                provider = provider_registry.get_provider(provider_name)
                if provider:
                    # Fetch all chapters from provider (handle pagination)
                    all_chapters = []
                    page = 1
                    limit = 100

                    while True:
                        chapters, total, has_next = await provider.get_chapters(
                            external_id, page=page, limit=limit
                        )
                        if not chapters:
                            break

                        all_chapters.extend(chapters)

                        if not has_next:
                            break

                        page += 1

                        # Safety check to prevent infinite loops
                        if page > 50:  # Max 5000 chapters
                            logger.warning(
                                f"Reached maximum page limit (50) for manga {external_id}"
                            )
                            break

                    logger.info(
                        f"Fetched {len(all_chapters)} chapters from provider {provider_name}"
                    )

                    # Create chapter records
                    for chapter_data in all_chapters:
                        try:
                            chapter_number = str(chapter_data.get("number", "0"))

                            # Check if chapter already exists
                            existing_chapter = await db.execute(
                                select(Chapter).where(
                                    (Chapter.manga_id == manga.id)
                                    & (Chapter.number == chapter_number)
                                )
                            )
                            if existing_chapter.scalars().first():
                                continue  # Skip duplicate chapters

                            # Parse dates
                            publish_at = None
                            readable_at = None
                            if chapter_data.get("publish_at"):
                                try:
                                    from datetime import datetime

                                    publish_at = datetime.fromisoformat(
                                        str(chapter_data["publish_at"]).replace(
                                            "Z", "+00:00"
                                        )
                                    )
                                except Exception:
                                    pass

                            if chapter_data.get("readable_at"):
                                try:
                                    from datetime import datetime

                                    readable_at = datetime.fromisoformat(
                                        str(chapter_data["readable_at"]).replace(
                                            "Z", "+00:00"
                                        )
                                    )
                                except Exception:
                                    pass

                            chapter = Chapter(
                                manga_id=manga.id,
                                title=chapter_data.get(
                                    "title", f"Chapter {chapter_number}"
                                ),
                                number=chapter_number,
                                volume=chapter_data.get("volume"),
                                language=chapter_data.get("language", "en"),
                                pages_count=chapter_data.get("pages_count", 0),
                                external_id=chapter_data.get("id"),
                                source=chapter_data.get("source", provider_name),
                                publish_at=publish_at,
                                readable_at=readable_at,
                                download_status="not_downloaded",
                            )

                            db.add(chapter)

                        except Exception as e:
                            chapter_num = chapter_data.get("number", "unknown")
                            logger.error(f"Error creating chapter {chapter_num}: {e}")
                            continue

                    logger.info(f"Successfully created chapters for manga {manga.id}")
                else:
                    logger.warning(f"Provider '{provider_name}' not found")

            except Exception as e:
                logger.error(f"Error fetching chapters from provider: {e}")
                # Don't fail the entire operation if chapter fetch fails
                pass

        await db.commit()
        await db.refresh(manga)

        logger.info(f"Added manga to library from MangaUpdates: {manga.title}")
        return manga


# Global service instance
enhanced_search_service = EnhancedSearchService()
