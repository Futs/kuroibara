from typing import List, Dict, Any, Optional, Tuple
import httpx
import re
import json
import logging
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.models.manga import MangaType, MangaStatus
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class GenericProvider(BaseProvider):
    """Generic provider that can be configured for various manga sites."""
    
    def __init__(
        self,
        base_url: str,
        search_url: str,
        manga_url_pattern: str,
        chapter_url_pattern: str,
        name: str = "Generic",
        supports_nsfw: bool = False,
        search_selector: str = ".manga-item",
        title_selector: str = ".manga-title",
        cover_selector: str = ".manga-cover img",
        description_selector: str = ".manga-description",
        chapter_selector: str = ".chapter-item",
        page_selector: str = ".manga-page img",
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the generic provider.
        
        Args:
            base_url: Base URL of the provider
            search_url: URL for searching manga
            manga_url_pattern: Pattern for manga URL (use {manga_id} as placeholder)
            chapter_url_pattern: Pattern for chapter URL (use {manga_id} and {chapter_id} as placeholders)
            name: Name of the provider
            supports_nsfw: Whether the provider supports NSFW content
            search_selector: CSS selector for manga items in search results
            title_selector: CSS selector for manga title
            cover_selector: CSS selector for manga cover
            description_selector: CSS selector for manga description
            chapter_selector: CSS selector for chapter items
            page_selector: CSS selector for manga pages
            headers: Custom headers for HTTP requests
        """
        self._base_url = base_url
        self._search_url = search_url
        self._manga_url_pattern = manga_url_pattern
        self._chapter_url_pattern = chapter_url_pattern
        self._name = name
        self._supports_nsfw = supports_nsfw
        self._search_selector = search_selector
        self._title_selector = title_selector
        self._cover_selector = cover_selector
        self._description_selector = description_selector
        self._chapter_selector = chapter_selector
        self._page_selector = page_selector
        self._headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def url(self) -> str:
        return self._base_url
    
    @property
    def supports_nsfw(self) -> bool:
        return self._supports_nsfw
    
    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga."""
        try:
            # Build search URL
            search_url = f"{self._search_url}?q={quote(query)}&page={page}&limit={limit}"
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url,
                    headers=self._headers,
                    follow_redirects=True,
                )
                
                # Check if request was successful
                response.raise_for_status()
                html = response.text
                
                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")
                
                # Find manga items
                manga_items = soup.select(self._search_selector)
                
                # Parse results
                results = []
                for item in manga_items:
                    try:
                        # Get manga ID and URL
                        manga_link = item.select_one("a")
                        if not manga_link:
                            continue
                        
                        manga_url = manga_link.get("href", "")
                        manga_id = self._extract_manga_id(manga_url)
                        
                        if not manga_id:
                            continue
                        
                        # Get title
                        title_elem = item.select_one(self._title_selector)
                        title = title_elem.text.strip() if title_elem else ""
                        
                        # Get cover
                        cover_elem = item.select_one(self._cover_selector)
                        cover_url = cover_elem.get("src", "") if cover_elem else ""
                        
                        # Create search result
                        result = SearchResult(
                            id=manga_id,
                            title=title,
                            alternative_titles={},
                            description="",  # We need to fetch the manga details to get the description
                            cover_image=cover_url,
                            type=MangaType.UNKNOWN,
                            status=MangaStatus.UNKNOWN,
                            year=None,
                            is_nsfw=self._supports_nsfw,
                            genres=[],
                            authors=[],
                            provider=self.name,
                            url=self._manga_url_pattern.format(manga_id=manga_id),
                        )
                        
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error parsing manga item: {e}")
                
                # Determine if there are more results
                # This is a simple heuristic, might need to be adjusted for specific sites
                has_next = len(manga_items) >= limit
                
                return results, len(results), has_next
        except Exception as e:
            logger.error(f"Error searching for manga: {e}")
            return [], 0, False
    
    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get details for a manga."""
        try:
            # Build manga URL
            manga_url = self._manga_url_pattern.format(manga_id=manga_id)
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    manga_url,
                    headers=self._headers,
                    follow_redirects=True,
                )
                
                # Check if request was successful
                response.raise_for_status()
                html = response.text
                
                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")
                
                # Get title
                title_elem = soup.select_one(self._title_selector)
                title = title_elem.text.strip() if title_elem else ""
                
                # Get cover
                cover_elem = soup.select_one(self._cover_selector)
                cover_url = cover_elem.get("src", "") if cover_elem else ""
                
                # Get description
                description_elem = soup.select_one(self._description_selector)
                description = description_elem.text.strip() if description_elem else ""
                
                # Get genres
                genres = []
                genre_elems = soup.select(".manga-genres .genre")
                for genre_elem in genre_elems:
                    genre = genre_elem.text.strip()
                    if genre:
                        genres.append(genre)
                
                # Get authors
                authors = []
                author_elems = soup.select(".manga-authors .author")
                for author_elem in author_elems:
                    author = author_elem.text.strip()
                    if author:
                        authors.append(author)
                
                # Determine manga type
                manga_type = MangaType.MANGA
                type_elem = soup.select_one(".manga-type")
                if type_elem:
                    type_text = type_elem.text.strip().lower()
                    if "manhwa" in type_text:
                        manga_type = MangaType.MANHWA
                    elif "manhua" in type_text:
                        manga_type = MangaType.MANHUA
                
                # Determine manga status
                manga_status = MangaStatus.UNKNOWN
                status_elem = soup.select_one(".manga-status")
                if status_elem:
                    status_text = status_elem.text.strip().lower()
                    if "ongoing" in status_text:
                        manga_status = MangaStatus.ONGOING
                    elif "complete" in status_text or "completed" in status_text:
                        manga_status = MangaStatus.COMPLETED
                    elif "hiatus" in status_text:
                        manga_status = MangaStatus.HIATUS
                    elif "cancelled" in status_text or "dropped" in status_text:
                        manga_status = MangaStatus.CANCELLED
                
                # Get year
                year = None
                year_elem = soup.select_one(".manga-year")
                if year_elem:
                    try:
                        year = int(year_elem.text.strip())
                    except (ValueError, TypeError):
                        pass
                
                # Return manga details
                return {
                    "id": manga_id,
                    "title": title,
                    "alternative_titles": {},
                    "description": description,
                    "cover_image": cover_url,
                    "type": manga_type,
                    "status": manga_status,
                    "year": year,
                    "is_nsfw": self._supports_nsfw,
                    "genres": genres,
                    "authors": authors,
                    "provider": self.name,
                    "url": manga_url,
                }
        except Exception as e:
            logger.error(f"Error getting manga details: {e}")
            return {}
    
    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga."""
        try:
            # Build manga URL
            manga_url = self._manga_url_pattern.format(manga_id=manga_id)
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    manga_url,
                    headers=self._headers,
                    follow_redirects=True,
                )
                
                # Check if request was successful
                response.raise_for_status()
                html = response.text
                
                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")
                
                # Find chapter items
                chapter_items = soup.select(self._chapter_selector)
                
                # Parse chapters
                chapters = []
                for item in chapter_items:
                    try:
                        # Get chapter ID and URL
                        chapter_link = item.select_one("a")
                        if not chapter_link:
                            continue
                        
                        chapter_url = chapter_link.get("href", "")
                        chapter_id = self._extract_chapter_id(chapter_url)
                        
                        if not chapter_id:
                            continue
                        
                        # Get chapter number
                        chapter_number = ""
                        chapter_number_elem = item.select_one(".chapter-number")
                        if chapter_number_elem:
                            chapter_number = chapter_number_elem.text.strip()
                        else:
                            # Try to extract chapter number from title
                            chapter_title_elem = item.select_one(".chapter-title")
                            if chapter_title_elem:
                                chapter_title = chapter_title_elem.text.strip()
                                match = re.search(r"chapter\s+(\d+(\.\d+)?)", chapter_title, re.IGNORECASE)
                                if match:
                                    chapter_number = match.group(1)
                        
                        # Get chapter title
                        chapter_title = ""
                        chapter_title_elem = item.select_one(".chapter-title")
                        if chapter_title_elem:
                            chapter_title = chapter_title_elem.text.strip()
                        
                        # Create chapter
                        chapters.append({
                            "id": chapter_id,
                            "title": chapter_title,
                            "number": chapter_number or "0",
                            "volume": None,
                            "language": "en",
                            "pages_count": 0,  # We don't know the page count yet
                            "manga_id": manga_id,
                        })
                    except Exception as e:
                        logger.error(f"Error parsing chapter item: {e}")
                
                # Apply pagination
                total = len(chapters)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_chapters = chapters[start_idx:end_idx]
                has_next = end_idx < total
                
                return paginated_chapters, total, has_next
        except Exception as e:
            logger.error(f"Error getting chapters: {e}")
            return [], 0, False
    
    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter."""
        try:
            # Build chapter URL
            chapter_url = self._chapter_url_pattern.format(manga_id=manga_id, chapter_id=chapter_id)
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    chapter_url,
                    headers=self._headers,
                    follow_redirects=True,
                )
                
                # Check if request was successful
                response.raise_for_status()
                html = response.text
                
                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")
                
                # Find page images
                page_images = soup.select(self._page_selector)
                
                # Get page URLs
                page_urls = []
                for img in page_images:
                    src = img.get("src", "")
                    if src:
                        # Make sure URL is absolute
                        if not src.startswith(("http://", "https://")):
                            if src.startswith("//"):
                                src = f"https:{src}"
                            else:
                                src = f"{self._base_url.rstrip('/')}/{src.lstrip('/')}"
                        
                        page_urls.append(src)
                
                return page_urls
        except Exception as e:
            logger.error(f"Error getting pages: {e}")
            return []
    
    async def download_page(self, page_url: str) -> bytes:
        """Download a page."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    page_url,
                    headers={
                        **self._headers,
                        "Referer": self._base_url,
                    },
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading page: {e}")
            return b""
    
    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover."""
        try:
            # Get manga details to get cover URL
            manga_details = await self.get_manga_details(manga_id)
            cover_url = manga_details.get("cover_image", "")
            
            if not cover_url:
                return b""
            
            # Download cover
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    cover_url,
                    headers={
                        **self._headers,
                        "Referer": self._base_url,
                    },
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading cover: {e}")
            return b""
    
    def _extract_manga_id(self, url: str) -> str:
        """Extract manga ID from URL."""
        # This is a simple implementation that assumes the manga ID is the last part of the URL path
        # For specific sites, this method can be overridden
        if not url:
            return ""
        
        # Remove query parameters and fragment
        url = url.split("?")[0].split("#")[0]
        
        # Get the path
        path = url.rstrip("/").split("/")
        
        # Return the last part of the path
        return path[-1] if path else ""
    
    def _extract_chapter_id(self, url: str) -> str:
        """Extract chapter ID from URL."""
        # This is a simple implementation that assumes the chapter ID is the last part of the URL path
        # For specific sites, this method can be overridden
        if not url:
            return ""
        
        # Remove query parameters and fragment
        url = url.split("?")[0].split("#")[0]
        
        # Get the path
        path = url.rstrip("/").split("/")
        
        # Return the last part of the path
        return path[-1] if path else ""
