"""Enhanced search service using tiered indexing system."""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.tiered_indexing import (
    tiered_search_service, 
    UniversalMetadata,
    IndexerTier
)
from app.models.mangaupdates import (
    UniversalMangaEntry, 
    UniversalMangaMapping, 
    CrossIndexerReference
)
from app.models.manga import Manga
from app.schemas.search import SearchResult, SearchResponse

logger = logging.getLogger(__name__)


class EnhancedTieredSearchService:
    """Enhanced search service with tiered indexing and intelligent caching."""
    
    def __init__(self):
        self.tiered_service = tiered_search_service
    
    async def search(
        self,
        query: str,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        user_id: Optional[str] = None,
        include_provider_matches: bool = True,
        use_cache: bool = True,
        min_confidence: float = 0.5
    ) -> SearchResponse:
        """
        Enhanced search using tiered indexing system.
        
        Args:
            query: Search query
            db: Database session
            page: Page number
            limit: Results per page
            user_id: User ID for library status
            include_provider_matches: Whether to find provider matches
            use_cache: Whether to use cached results
            min_confidence: Minimum confidence score for results
        """
        
        # First, check if we have cached results
        if use_cache:
            cached_results = await self._get_cached_results(query, db, page, limit)
            if cached_results:
                logger.info(f"Using cached results for query: {query}")
                return await self._process_cached_results(
                    cached_results, user_id, include_provider_matches, db
                )
        
        # Perform tiered search
        logger.info(f"Performing tiered search for: {query}")
        tiered_results = await self.tiered_service.search(
            query=query,
            limit=limit * 2,  # Get more results to account for filtering
            use_fallback=True,
            min_results=5
        )
        
        if not tiered_results:
            return SearchResponse(
                results=[],
                total=0,
                page=page,
                limit=limit,
                has_next=False
            )
        
        # Filter by confidence
        filtered_results = [
            result for result in tiered_results 
            if result.confidence_score >= min_confidence
        ]
        
        # Store results in database for caching and cross-referencing
        stored_entries = await self._store_search_results(filtered_results, db)
        
        # Convert to search results
        search_results = []
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        for entry in stored_entries[start_idx:end_idx]:
            search_result = await self._convert_to_search_result(
                entry, user_id, include_provider_matches, db
            )
            if search_result:
                search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            total=len(stored_entries),
            page=page,
            limit=limit,
            has_next=len(stored_entries) > end_idx
        )
    
    async def get_details(
        self,
        entry_id: str,
        db: AsyncSession,
        user_id: Optional[str] = None,
        include_cross_references: bool = True
    ) -> Optional[Dict]:
        """Get detailed information about a universal manga entry."""
        
        # Get the universal entry
        result = await db.execute(
            select(UniversalMangaEntry).where(UniversalMangaEntry.id == entry_id)
        )
        entry = result.scalars().first()
        
        if not entry:
            return None
        
        # Get cross-references if requested
        cross_refs = {}
        if include_cross_references:
            cross_refs = await self._get_cross_references(entry, db)
        
        # Check library status
        in_library, library_manga = await self._check_library_status(entry, user_id, db)
        
        # Get provider matches if needed
        provider_matches = []
        if library_manga:
            # If in library, get provider matches from existing data
            from app.core.services.enhanced_search import ProviderMatcher
            matcher = ProviderMatcher()
            provider_matches = await matcher.find_provider_matches(
                self._convert_to_legacy_format(entry), max_providers=5
            )
        
        return {
            "entry": self._entry_to_dict(entry),
            "cross_references": cross_refs,
            "in_library": in_library,
            "library_manga_id": str(library_manga.id) if library_manga else None,
            "provider_matches": provider_matches
        }
    
    async def add_to_library(
        self,
        entry_id: str,
        user_id: str,
        db: AsyncSession,
        preferred_indexer: Optional[str] = None,
        selected_provider_match: Optional[Dict] = None
    ) -> Manga:
        """Add manga to library from universal entry."""
        
        # Get the universal entry
        result = await db.execute(
            select(UniversalMangaEntry).where(UniversalMangaEntry.id == entry_id)
        )
        entry = result.scalars().first()
        
        if not entry:
            raise ValueError("Universal manga entry not found")
        
        # Check if already mapped to a manga
        mapping_result = await db.execute(
            select(UniversalMangaMapping, Manga)
            .join(Manga, UniversalMangaMapping.manga_id == Manga.id)
            .where(UniversalMangaMapping.universal_entry_id == entry.id)
        )
        
        mapping_and_manga = mapping_result.first()
        if mapping_and_manga:
            mapping, existing_manga = mapping_and_manga
            
            # Add to user's library if not already there
            from app.models.library import MangaUserLibrary
            library_result = await db.execute(
                select(MangaUserLibrary).where(
                    (MangaUserLibrary.manga_id == existing_manga.id) &
                    (MangaUserLibrary.user_id == user_id)
                )
            )
            
            if not library_result.scalars().first():
                library_item = MangaUserLibrary(
                    user_id=user_id,
                    manga_id=existing_manga.id
                )
                db.add(library_item)
                await db.commit()
            
            return existing_manga
        
        # Create new manga from universal entry
        manga_data = {
            "title": entry.title,
            "alternative_titles": entry.alternative_titles,
            "description": entry.description,
            "cover_image": entry.cover_image_url,
            "type": entry.type or "unknown",
            "status": entry.status or "unknown",
            "year": entry.year,
            "is_nsfw": entry.is_nsfw,
        }
        
        # If a provider match was selected, add provider info
        if selected_provider_match:
            manga_data.update({
                "provider": selected_provider_match["provider"],
                "external_id": selected_provider_match["external_id"],
                "external_url": selected_provider_match["url"],
            })
        
        manga = Manga(**manga_data)
        db.add(manga)
        await db.flush()  # Get the ID
        
        # Create universal mapping
        mapping = UniversalMangaMapping(
            manga_id=manga.id,
            universal_entry_id=entry.id,
            confidence_score=1.0,
            mapping_source="manual",
            verified_by_user=True,
            preferred_indexer=preferred_indexer or entry.source_indexer
        )
        db.add(mapping)
        
        # Add to user's library
        from app.models.library import MangaUserLibrary
        library_item = MangaUserLibrary(
            user_id=user_id,
            manga_id=manga.id
        )
        db.add(library_item)
        
        await db.commit()
        await db.refresh(manga)
        
        logger.info(f"Added manga to library from universal entry: {manga.title}")
        return manga
    
    async def refresh_entry(
        self,
        entry_id: str,
        db: AsyncSession,
        force_refresh: bool = False
    ) -> bool:
        """Refresh a universal entry with latest data from its source indexer."""
        
        # Get the entry
        result = await db.execute(
            select(UniversalMangaEntry).where(UniversalMangaEntry.id == entry_id)
        )
        entry = result.scalars().first()
        
        if not entry:
            return False
        
        # Check if refresh is needed
        if not force_refresh and not self._needs_refresh(entry):
            return True
        
        try:
            # Get fresh data from source indexer
            fresh_data = await self.tiered_service.get_details(
                entry.source_indexer, entry.source_id
            )
            
            if fresh_data:
                # Update entry with fresh data
                self._update_entry_from_metadata(entry, fresh_data)
                entry.last_refreshed = datetime.utcnow()
                
                await db.commit()
                logger.info(f"Refreshed entry {entry_id} from {entry.source_indexer}")
                return True
            else:
                logger.warning(f"Failed to get fresh data for entry {entry_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing entry {entry_id}: {e}")
            return False
    
    async def _get_cached_results(
        self, 
        query: str, 
        db: AsyncSession, 
        page: int, 
        limit: int
    ) -> Optional[List[UniversalMangaEntry]]:
        """Get cached search results from database."""
        
        # Simple title-based search in cached entries
        # In production, you might want more sophisticated caching
        normalized_query = query.lower().strip()
        
        result = await db.execute(
            select(UniversalMangaEntry)
            .where(
                or_(
                    UniversalMangaEntry.title.ilike(f"%{normalized_query}%"),
                    UniversalMangaEntry.alternative_titles.op("@>")(f'["{normalized_query}"]')
                )
            )
            .order_by(
                UniversalMangaEntry.confidence_score.desc(),
                UniversalMangaEntry.rating.desc().nullslast(),
                UniversalMangaEntry.title
            )
            .limit(limit * 3)  # Get more for better filtering
        )
        
        entries = result.scalars().all()
        return entries if entries else None
    
    async def _process_cached_results(
        self,
        cached_entries: List[UniversalMangaEntry],
        user_id: Optional[str],
        include_provider_matches: bool,
        db: AsyncSession
    ) -> SearchResponse:
        """Process cached results into search response."""
        
        search_results = []
        for entry in cached_entries:
            search_result = await self._convert_to_search_result(
                entry, user_id, include_provider_matches, db
            )
            if search_result:
                search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            page=1,
            limit=len(search_results),
            has_next=False
        )
    
    async def _store_search_results(
        self,
        metadata_results: List[UniversalMetadata],
        db: AsyncSession
    ) -> List[UniversalMangaEntry]:
        """Store search results in database and return stored entries."""
        
        stored_entries = []
        
        for metadata in metadata_results:
            # Check if entry already exists
            result = await db.execute(
                select(UniversalMangaEntry).where(
                    and_(
                        UniversalMangaEntry.source_indexer == metadata.source_indexer,
                        UniversalMangaEntry.source_id == metadata.source_id
                    )
                )
            )
            
            existing_entry = result.scalars().first()
            
            if existing_entry:
                # Update existing entry if new data has higher confidence
                if metadata.confidence_score > existing_entry.confidence_score:
                    self._update_entry_from_metadata(existing_entry, metadata)
                    await db.flush()
                stored_entries.append(existing_entry)
            else:
                # Create new entry
                new_entry = self._create_entry_from_metadata(metadata)
                db.add(new_entry)
                await db.flush()
                stored_entries.append(new_entry)
        
        await db.commit()
        return stored_entries
    
    def _create_entry_from_metadata(self, metadata: UniversalMetadata) -> UniversalMangaEntry:
        """Create a new universal entry from metadata."""
        
        return UniversalMangaEntry(
            source_indexer=metadata.source_indexer,
            source_id=metadata.source_id,
            source_url=metadata.source_url,
            title=metadata.title,
            alternative_titles=metadata.alternative_titles,
            description=metadata.description,
            cover_image_url=metadata.cover_image_url,
            type=metadata.type,
            status=metadata.status,
            year=metadata.year,
            completed_year=metadata.completed_year,
            is_nsfw=metadata.is_nsfw,
            content_rating=metadata.content_rating,
            demographic=metadata.demographic,
            genres=metadata.genres,
            tags=metadata.tags,
            themes=metadata.themes,
            authors=metadata.authors,
            artists=metadata.artists,
            rating=metadata.rating,
            rating_count=metadata.rating_count,
            popularity_rank=metadata.popularity_rank,
            follows=metadata.follows,
            latest_chapter=metadata.latest_chapter,
            total_chapters=metadata.total_chapters,
            confidence_score=metadata.confidence_score,
            data_completeness=self._calculate_completeness(metadata),
            last_refreshed=datetime.utcnow(),
            raw_data=metadata.raw_data
        )
    
    def _update_entry_from_metadata(self, entry: UniversalMangaEntry, metadata: UniversalMetadata):
        """Update existing entry with new metadata."""
        
        # Update fields with new data
        entry.title = metadata.title or entry.title
        entry.alternative_titles = metadata.alternative_titles or entry.alternative_titles
        entry.description = metadata.description or entry.description
        entry.cover_image_url = metadata.cover_image_url or entry.cover_image_url
        entry.type = metadata.type or entry.type
        entry.status = metadata.status or entry.status
        entry.year = metadata.year or entry.year
        entry.completed_year = metadata.completed_year or entry.completed_year
        entry.is_nsfw = metadata.is_nsfw if metadata.is_nsfw is not None else entry.is_nsfw
        entry.content_rating = metadata.content_rating or entry.content_rating
        entry.demographic = metadata.demographic or entry.demographic
        entry.genres = metadata.genres or entry.genres
        entry.tags = metadata.tags or entry.tags
        entry.themes = metadata.themes or entry.themes
        entry.authors = metadata.authors or entry.authors
        entry.artists = metadata.artists or entry.artists
        entry.rating = metadata.rating or entry.rating
        entry.rating_count = metadata.rating_count or entry.rating_count
        entry.popularity_rank = metadata.popularity_rank or entry.popularity_rank
        entry.follows = metadata.follows or entry.follows
        entry.latest_chapter = metadata.latest_chapter or entry.latest_chapter
        entry.total_chapters = metadata.total_chapters or entry.total_chapters
        entry.confidence_score = max(metadata.confidence_score, entry.confidence_score)
        entry.data_completeness = self._calculate_completeness_from_entry(entry)
        entry.last_refreshed = datetime.utcnow()
        entry.raw_data = metadata.raw_data or entry.raw_data
    
    def _calculate_completeness(self, metadata: UniversalMetadata) -> float:
        """Calculate data completeness score for metadata."""
        
        fields = [
            metadata.title, metadata.description, metadata.cover_image_url,
            metadata.type, metadata.status, metadata.year, metadata.genres,
            metadata.authors, metadata.rating
        ]
        
        filled_fields = sum(1 for field in fields if field)
        return filled_fields / len(fields)
    
    def _calculate_completeness_from_entry(self, entry: UniversalMangaEntry) -> float:
        """Calculate data completeness score for entry."""
        
        fields = [
            entry.title, entry.description, entry.cover_image_url,
            entry.type, entry.status, entry.year, entry.genres,
            entry.authors, entry.rating
        ]
        
        filled_fields = sum(1 for field in fields if field)
        return filled_fields / len(fields)
    
    def _needs_refresh(self, entry: UniversalMangaEntry) -> bool:
        """Check if entry needs refreshing."""
        
        if not entry.auto_refresh_enabled or not entry.last_refreshed:
            return True
        
        hours_since_refresh = (datetime.utcnow() - entry.last_refreshed).total_seconds() / 3600
        return hours_since_refresh >= entry.refresh_interval_hours
    
    async def _convert_to_search_result(
        self,
        entry: UniversalMangaEntry,
        user_id: Optional[str],
        include_provider_matches: bool,
        db: AsyncSession
    ) -> Optional[SearchResult]:
        """Convert universal entry to search result."""
        
        # Check library status
        in_library, library_manga = await self._check_library_status(entry, user_id, db)
        
        # Get provider matches if requested
        provider_matches = []
        if include_provider_matches:
            # This would integrate with the existing provider matching system
            pass
        
        # For MangaUpdates entries, we need to use the UUID from the database
        if entry.source_indexer == "mangaupdates":
            # Look up the UUID for this MangaUpdates entry in universal_manga_entries
            from app.models.mangaupdates import UniversalMangaEntry
            stmt = select(UniversalMangaEntry.id).where(
                and_(
                    UniversalMangaEntry.source_indexer == "mangaupdates",
                    UniversalMangaEntry.source_id == entry.source_id
                )
            )
            result = await db.execute(stmt)
            uuid_result = result.scalar_one_or_none()
            entry_id = str(uuid_result) if uuid_result else entry.source_id
        else:
            entry_id = entry.source_id

        return SearchResult(
            id=entry_id,
            title=entry.title,
            alternative_titles=entry.alternative_titles or {},
            description=entry.description,
            cover_image=entry.cover_image_url,
            type=entry.type or "unknown",
            status=entry.status or "unknown",
            year=entry.year,
            is_nsfw=entry.is_nsfw,
            genres=entry.genres or [],
            authors=[author.get("name", "") for author in (entry.authors or [])],
            provider="enhanced_mangaupdates" if entry.source_indexer == "mangaupdates" else entry.source_indexer,
            url=entry.source_url or "",
            in_library=in_library,
            extra={
                "source_indexer": entry.source_indexer,
                "source_id": entry.source_id,
                "confidence_score": entry.confidence_score,
                "data_completeness": entry.data_completeness,
                "rating": entry.rating,
                "rating_count": entry.rating_count,
                "popularity_rank": entry.popularity_rank,
                "follows": entry.follows,
                "tags": entry.tags or [],
                "themes": entry.themes or [],
                "demographic": entry.demographic,
                "latest_chapter": entry.latest_chapter,
                "total_chapters": entry.total_chapters,
                "provider_matches": provider_matches,
            }
        )
    
    async def _check_library_status(
        self,
        entry: UniversalMangaEntry,
        user_id: Optional[str],
        db: AsyncSession
    ) -> Tuple[bool, Optional[Manga]]:
        """Check if universal entry is in user's library."""
        
        if not user_id:
            return False, None
        
        # Look for existing mapping
        result = await db.execute(
            select(UniversalMangaMapping, Manga)
            .join(Manga, UniversalMangaMapping.manga_id == Manga.id)
            .where(UniversalMangaMapping.universal_entry_id == entry.id)
        )
        
        mapping_and_manga = result.first()
        if mapping_and_manga:
            mapping, manga = mapping_and_manga
            
            # Check if manga is in user's library
            from app.models.library import MangaUserLibrary
            library_result = await db.execute(
                select(MangaUserLibrary).where(
                    (MangaUserLibrary.manga_id == manga.id) &
                    (MangaUserLibrary.user_id == user_id)
                )
            )
            
            if library_result.scalars().first():
                return True, manga
        
        return False, None
    
    async def _get_cross_references(
        self,
        entry: UniversalMangaEntry,
        db: AsyncSession
    ) -> Dict[str, Dict]:
        """Get cross-references for an entry."""
        
        result = await db.execute(
            select(CrossIndexerReference).where(
                CrossIndexerReference.universal_entry_id == entry.id
            )
        )
        
        cross_refs = {}
        for ref in result.scalars().all():
            cross_refs[ref.reference_indexer] = {
                "reference_id": ref.reference_id,
                "reference_url": ref.reference_url,
                "confidence_score": ref.confidence_score,
                "match_method": ref.match_method,
                "verified_by_user": ref.verified_by_user,
                "additional_metadata": ref.additional_metadata
            }
        
        return cross_refs
    
    def _entry_to_dict(self, entry: UniversalMangaEntry) -> Dict:
        """Convert entry to dictionary."""
        
        return {
            "id": str(entry.id),
            "source_indexer": entry.source_indexer,
            "source_id": entry.source_id,
            "source_url": entry.source_url,
            "title": entry.title,
            "alternative_titles": entry.alternative_titles,
            "description": entry.description,
            "cover_image_url": entry.cover_image_url,
            "type": entry.type,
            "status": entry.status,
            "year": entry.year,
            "completed_year": entry.completed_year,
            "is_nsfw": entry.is_nsfw,
            "content_rating": entry.content_rating,
            "demographic": entry.demographic,
            "genres": entry.genres,
            "tags": entry.tags,
            "themes": entry.themes,
            "authors": entry.authors,
            "artists": entry.artists,
            "rating": entry.rating,
            "rating_count": entry.rating_count,
            "popularity_rank": entry.popularity_rank,
            "follows": entry.follows,
            "latest_chapter": entry.latest_chapter,
            "total_chapters": entry.total_chapters,
            "confidence_score": entry.confidence_score,
            "data_completeness": entry.data_completeness,
            "last_refreshed": entry.last_refreshed.isoformat() if entry.last_refreshed else None,
        }
    
    def _convert_to_legacy_format(self, entry: UniversalMangaEntry):
        """Convert universal entry to legacy MangaUpdates format for compatibility."""
        # This is a compatibility shim for existing provider matching code
        class LegacyEntry:
            def __init__(self, entry):
                self.title = entry.title
                self.alternative_titles = entry.alternative_titles
                self.year = entry.year
                self.genres = entry.genres
                self.type = entry.type
        
        return LegacyEntry(entry)


# Global service instance
enhanced_tiered_search_service = EnhancedTieredSearchService()
