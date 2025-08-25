"""MangaUpdates API integration service."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mangaupdates import MangaUpdatesEntry, MangaUpdatesMapping
from app.models.manga import Manga

logger = logging.getLogger(__name__)


class MangaUpdatesAPI:
    """MangaUpdates API client."""
    
    BASE_URL = "https://api.mangaupdates.com/v1"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Kuroibara/1.0 (https://github.com/Futs/kuroibara)"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_series(self, query: str, page: int = 1, per_page: int = 50) -> Dict:
        """Search for series on MangaUpdates."""
        if not self.session:
            raise RuntimeError("MangaUpdatesAPI must be used as async context manager")
            
        url = f"{self.BASE_URL}/series/search"
        params = {
            "search": query,
            "page": page,
            "perpage": min(per_page, 100)  # API limit
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"MangaUpdates search failed: {response.status}")
                    return {"results": [], "total_hits": 0}
        except Exception as e:
            logger.error(f"Error searching MangaUpdates: {e}")
            return {"results": [], "total_hits": 0}
    
    async def get_series_details(self, series_id: int) -> Optional[Dict]:
        """Get detailed information about a series."""
        if not self.session:
            raise RuntimeError("MangaUpdatesAPI must be used as async context manager")

        url = f"{self.BASE_URL}/series/{series_id}"
        logger.info(f"MangaUpdatesAPI.get_series_details called with series_id: {series_id}")
        logger.info(f"Making HTTP GET request to: {url}")

        try:
            async with self.session.get(url) as response:
                logger.info(f"HTTP response received - status: {response.status}")
                logger.info(f"Response headers: {dict(response.headers)}")

                if response.status == 200:
                    logger.info(f"Success response, parsing JSON...")
                    result = await response.json()
                    logger.info(f"JSON parsed successfully - type: {type(result)}")

                    if isinstance(result, dict):
                        logger.info(f"Response is dict with keys: {list(result.keys())}")
                        # Log first few characters of important fields
                        if 'title' in result:
                            logger.info(f"Title: {result.get('title', 'N/A')}")
                        if 'error' in result:
                            logger.error(f"API returned error in response: {result['error']}")
                    else:
                        logger.warning(f"Response is not a dict: {result}")

                    return result
                else:
                    response_text = await response.text()
                    logger.error(f"HTTP error {response.status} for series {series_id}")
                    logger.error(f"Response body: {response_text}")
                    return response_text  # Return the error text so we can see what it is

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error getting series details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting series details: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def get_series_chapters(self, series_id: int) -> List[Dict]:
        """Get chapter list for a series."""
        if not self.session:
            raise RuntimeError("MangaUpdatesAPI must be used as async context manager")
            
        url = f"{self.BASE_URL}/series/{series_id}/chapters"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("chapters", [])
                else:
                    logger.error(f"Failed to get chapters for series {series_id}: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting series chapters: {e}")
            return []


class MangaUpdatesService:
    """Service for managing MangaUpdates integration."""
    
    def __init__(self):
        self.api = MangaUpdatesAPI()
    
    async def search_and_create_entry(
        self, 
        query: str, 
        db: AsyncSession,
        auto_select_best: bool = True
    ) -> Optional[MangaUpdatesEntry]:
        """Search MangaUpdates and create/update entry."""
        async with self.api as api:
            search_results = await api.search_series(query)
            
            if not search_results.get("results"):
                logger.info(f"No MangaUpdates results found for: {query}")
                return None
            
            # Get the best match (first result if auto_select_best)
            if auto_select_best:
                best_match = search_results["results"][0]
            else:
                # For manual selection, return the first result for now
                # In the future, this could present options to the user
                best_match = search_results["results"][0]
            
            series_id = best_match["record"]["series_id"]
            
            # Check if we already have this entry
            result = await db.execute(
                select(MangaUpdatesEntry).where(
                    MangaUpdatesEntry.mu_series_id == series_id
                )
            )
            existing_entry = result.scalars().first()
            
            if existing_entry:
                # Update existing entry
                await self._update_entry_from_api(existing_entry, api, db)
                return existing_entry
            else:
                # Create new entry
                return await self._create_entry_from_api(series_id, api, db)
    
    async def _create_entry_from_api(
        self,
        series_id: int,
        api: MangaUpdatesAPI,
        db: AsyncSession
    ) -> Optional[MangaUpdatesEntry]:
        """Create a new MangaUpdates entry from API data."""
        try:
            logger.info(f"_create_entry_from_api called with series_id: {series_id}")
            logger.info(f"API object type: {type(api)}")

            logger.info(f"Making API call to get_series_details({series_id})")
            details = await api.get_series_details(series_id)
            logger.info(f"API response received - type: {type(details)}")

            if isinstance(details, dict):
                logger.info(f"API response is dict with keys: {list(details.keys())}")
                if 'error' in details:
                    logger.error(f"API returned error response: {details}")
                    return None
            elif isinstance(details, str):
                logger.error(f"API returned string response (likely error): {details}")
                return None
            else:
                logger.info(f"API response content (first 500 chars): {str(details)[:500]}")

            if not details:
                logger.warning(f"No details returned for series ID: {series_id}")
                return None

            if not isinstance(details, dict):
                logger.error(f"Expected dict but got {type(details)}: {details}")
                return None

            # Extract data from API response
            logger.info(f"Calling _extract_entry_data with details")
            entry_data = self._extract_entry_data(details)
            logger.info(f"_extract_entry_data returned successfully")

            entry_data["mu_series_id"] = str(series_id)  # Convert to string for VARCHAR
            entry_data["last_refreshed"] = datetime.utcnow()
            entry_data["raw_data"] = details

            # Create entry
            logger.info(f"Creating MangaUpdatesEntry object")
            entry = MangaUpdatesEntry(**entry_data)
            logger.info(f"Adding entry to database session")
            db.add(entry)
            logger.info(f"Committing to database")
            await db.commit()
            await db.refresh(entry)

            logger.info(f"Successfully created MangaUpdates entry for series {series_id}: {entry.title}")
            return entry

        except Exception as e:
            logger.error(f"Error in _create_entry_from_api: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def _update_entry_from_api(
        self,
        entry: MangaUpdatesEntry,
        api: MangaUpdatesAPI,
        db: AsyncSession
    ) -> None:
        """Update existing entry with fresh API data."""
        # Convert string series ID back to integer for API call
        series_id = int(entry.mu_series_id)
        details = await api.get_series_details(series_id)
        if not details:
            return
        
        # Update entry data
        entry_data = self._extract_entry_data(details)
        for key, value in entry_data.items():
            setattr(entry, key, value)
        
        entry.last_refreshed = datetime.utcnow()
        entry.raw_data = details
        
        await db.commit()
        logger.info(f"Updated MangaUpdates entry for series {entry.mu_series_id}: {entry.title}")
    
    def _extract_entry_data(self, api_data: Dict) -> Dict:
        """Extract relevant data from MangaUpdates API response."""
        logger.info(f"_extract_entry_data called with type: {type(api_data)}, data: {api_data}")

        if not isinstance(api_data, dict):
            logger.error(f"Expected dict but got {type(api_data)}: {api_data}")
            raise ValueError(f"API returned error or invalid response: {api_data}")

        # Safely extract nested values with proper fallbacks
        type_info = api_data.get("type", {})
        type_value = type_info.get("type") if isinstance(type_info, dict) else None

        status_info = api_data.get("status", {})
        status_value = status_info.get("status") if isinstance(status_info, dict) else None

        return {
            "mu_series_id": str(api_data.get("series_id", "")),
            "mu_url": api_data.get("url"),
            "title": api_data.get("title", ""),
            "alternative_titles": self._extract_alternative_titles(api_data),
            "description": api_data.get("description", ""),
            "cover_image_url": self._extract_cover_url(api_data),
            "type": type_value,
            "status": status_value,
            "year": self._extract_year(api_data),
            "completed_year": self._extract_completed_year(api_data),
            "is_nsfw": self._is_nsfw(api_data),
            "content_rating": self._extract_content_rating(api_data),
            "genres": self._extract_genres(api_data),
            "authors": self._extract_authors(api_data),
            "publishers": self._extract_publishers(api_data),
            "rating": api_data.get("rating", {}).get("average"),
            "rating_count": api_data.get("rating", {}).get("votes"),
            "latest_chapter": self._extract_latest_chapter(api_data),
            "total_chapters": self._extract_total_chapters(api_data),
            "raw_data": api_data,
        }
    
    def _extract_alternative_titles(self, data: Dict) -> Dict:
        """Extract alternative titles from API data."""
        titles = {}
        
        # Extract associated names
        for assoc in data.get("associated", []):
            if assoc.get("title"):
                lang = assoc.get("type", "unknown")
                titles[lang] = assoc["title"]
        
        return titles if titles else None
    
    def _extract_cover_url(self, data: Dict) -> Optional[str]:
        """Extract cover image URL."""
        image = data.get("image", {})
        if isinstance(image, dict):
            return image.get("url", {}).get("original")
        return None
    
    def _extract_year(self, data: Dict) -> Optional[int]:
        """Extract publication year."""
        year_data = data.get("year")
        if isinstance(year_data, dict):
            return year_data.get("year")
        elif isinstance(year_data, int):
            return year_data
        return None
    
    def _extract_completed_year(self, data: Dict) -> Optional[int]:
        """Extract completion year."""
        # This might be in different places depending on API structure
        return None  # TODO: Implement based on actual API response
    
    def _is_nsfw(self, data: Dict) -> bool:
        """Determine if content is NSFW."""
        # Check various indicators
        genres = [g.get("genre", "").lower() for g in data.get("genres", [])]
        categories = [c.get("category", "").lower() for c in data.get("categories", [])]
        
        nsfw_indicators = ["adult", "mature", "ecchi", "hentai", "smut", "pornographic"]
        
        for indicator in nsfw_indicators:
            if any(indicator in g for g in genres) or any(indicator in c for c in categories):
                return True
        
        return False
    
    def _extract_content_rating(self, data: Dict) -> Optional[str]:
        """Extract content rating."""
        # This would need to be mapped from MangaUpdates categories/genres
        if self._is_nsfw(data):
            return "mature"
        return "safe"
    
    def _extract_genres(self, data: Dict) -> Optional[List[str]]:
        """Extract genres list."""
        genres = []
        for genre_data in data.get("genres", []):
            if genre_data.get("genre"):
                genres.append(genre_data["genre"])
        return genres if genres else None
    
    def _extract_categories(self, data: Dict) -> Optional[List[str]]:
        """Extract categories list."""
        categories = []
        for cat_data in data.get("categories", []):
            if cat_data.get("category"):
                categories.append(cat_data["category"])
        return categories if categories else None
    
    def _extract_authors(self, data: Dict) -> Optional[List[Dict]]:
        """Extract authors list."""
        authors = []
        for author_data in data.get("authors", []):
            if author_data.get("name"):
                authors.append({
                    "name": author_data["name"],
                    "type": author_data.get("type", "author")
                })
        return authors if authors else None
    
    def _extract_artists(self, data: Dict) -> Optional[List[Dict]]:
        """Extract artists list."""
        # Artists might be in the same authors array with type="artist"
        artists = []
        for author_data in data.get("authors", []):
            if author_data.get("type") == "artist" and author_data.get("name"):
                artists.append({
                    "name": author_data["name"],
                    "type": "artist"
                })
        return artists if artists else None
    
    def _extract_publishers(self, data: Dict) -> Optional[List[Dict]]:
        """Extract publishers list."""
        publishers = []
        for pub_data in data.get("publishers", []):
            if pub_data.get("publisher_name"):
                publishers.append({
                    "name": pub_data["publisher_name"],
                    "type": pub_data.get("type", "publisher")
                })
        return publishers if publishers else None
    
    def _extract_latest_chapter(self, data: Dict) -> Optional[str]:
        """Extract latest chapter number."""
        # This would need to be determined from the API structure
        return None  # TODO: Implement based on actual API response
    
    def _extract_total_chapters(self, data: Dict) -> Optional[int]:
        """Extract total chapter count."""
        # This would need to be determined from the API structure
        return None  # TODO: Implement based on actual API response
    
    async def create_manga_mapping(
        self,
        manga: Manga,
        mu_entry: MangaUpdatesEntry,
        db: AsyncSession,
        confidence_score: float = 1.0,
        mapping_source: str = "manual"
    ) -> MangaUpdatesMapping:
        """Create a mapping between local manga and MangaUpdates entry."""
        mapping = MangaUpdatesMapping(
            manga_id=manga.id,
            mu_entry_id=mu_entry.id,
            confidence_score=confidence_score,
            mapping_source=mapping_source,
            verified_by_user=mapping_source == "manual"
        )
        
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        
        logger.info(f"Created mapping: {manga.title} -> {mu_entry.title}")
        return mapping
    
    async def refresh_stale_entries(self, db: AsyncSession, batch_size: int = 10) -> int:
        """Refresh entries that need updating."""
        # Find entries that need refreshing
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Default refresh interval
        
        result = await db.execute(
            select(MangaUpdatesEntry)
            .where(
                (MangaUpdatesEntry.auto_refresh_enabled == True) &
                ((MangaUpdatesEntry.last_refreshed == None) |
                 (MangaUpdatesEntry.last_refreshed < cutoff_time))
            )
            .limit(batch_size)
        )
        
        stale_entries = result.scalars().all()
        
        if not stale_entries:
            return 0
        
        # Refresh entries
        async with self.api as api:
            for entry in stale_entries:
                try:
                    await self._update_entry_from_api(entry, api, db)
                    # Add delay to respect rate limits
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to refresh entry {entry.id}: {e}")
        
        return len(stale_entries)


# Global service instance
mangaupdates_service = MangaUpdatesService()
