import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
from app.schemas.search import SearchResult


class MangaPillProvider(BaseProvider):
    """Custom provider for MangaPill with specialized parsing."""

    def __init__(self, **kwargs):
        self._base_url = "https://mangapill.com"
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    @property
    def name(self) -> str:
        return "MangaPill"

    @property
    def url(self) -> str:
        return self._base_url

    @property
    def supports_nsfw(self) -> bool:
        return True

    async def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request with proper headers and redirect following."""
        try:
            async with httpx.AsyncClient(
                headers=self._headers, timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Request failed for {url}: {e}")
            return None

    def _extract_manga_id_from_url(self, url: str) -> str:
        """Extract manga ID from MangaPill URL format: /manga/12/title -> 12"""
        if not url:
            return ""

        # Handle relative URLs
        if url.startswith("/"):
            url = urljoin(self._base_url, url)

        # Extract ID from /manga/{id}/{title} pattern
        match = re.search(r"/manga/(\d+)/", url)
        if match:
            return match.group(1)

        # Fallback: try to extract any number from the URL
        match = re.search(r"/(\d+)/", url)
        if match:
            return match.group(1)

        return ""

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MangaPill."""
        try:
            # Build search URL with proper parameters
            search_url = f"{self._base_url}/search?q={query}&type=&status="

            html = await self._make_request(search_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find the results grid container - look for grid with manga links
            grid = None
            grids = soup.select(".grid")
            for g in grids:
                if g.select("a[href*='/manga/']"):
                    grid = g
                    break

            if not grid:
                return [], 0, False

            # Find all manga items in the grid - these are direct children with manga links
            items = []
            for child in grid.children:
                if (
                    hasattr(child, "name")
                    and child.name
                    and child.select("a[href*='/manga/']")
                ):
                    items.append(child)

            if not items:
                return [], 0, False

            results = []
            for item in items:
                try:
                    # Find the manga link
                    link_elem = item.select_one("a[href*='/manga/']")
                    if not link_elem:
                        continue

                    manga_url = link_elem.get("href", "")
                    if not manga_url:
                        continue

                    # Extract manga ID
                    manga_id = self._extract_manga_id_from_url(manga_url)
                    if not manga_id:
                        continue

                    # Get title - try multiple selectors
                    title = ""
                    title_selectors = [
                        ".font-bold",
                        ".text-truncate",
                        "a[href*='/manga/']",
                        ".title",
                    ]

                    for selector in title_selectors:
                        title_elem = item.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if title:
                                break

                    if not title:
                        title = "Unknown Title"

                    # Get cover image
                    cover_url = ""
                    img_elem = item.select_one("img")
                    if img_elem:
                        cover_url = img_elem.get("src", "") or img_elem.get(
                            "data-src", ""
                        )
                        if cover_url and not cover_url.startswith("http"):
                            cover_url = urljoin(self._base_url, cover_url)

                    # Build full manga URL
                    if manga_url.startswith("/"):
                        full_url = urljoin(self._base_url, manga_url)
                    else:
                        full_url = manga_url

                    # Create search result
                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        alternative_titles={},
                        description="",
                        cover_image=cover_url,
                        type=MangaType.MANGA,
                        status=MangaStatus.UNKNOWN,
                        year=None,
                        is_nsfw=False,
                        genres=[],
                        authors=[],
                        provider=self.name,
                        url=full_url,
                        in_library=False,
                        extra=None,
                    )

                    results.append(result)

                    # Limit results
                    if len(results) >= limit:
                        break

                except Exception as e:
                    print(f"Error parsing manga item: {e}")
                    continue

            # Calculate pagination info
            total_results = len(results)
            has_more = len(items) > len(results)

            return results, total_results, has_more

        except Exception as e:
            print(f"Search error: {e}")
            return [], 0, False

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get manga details from MangaPill."""
        try:
            # Build manga URL
            manga_url = f"{self._base_url}/manga/{manga_id}"

            html = await self._make_request(manga_url)
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title = "Unknown Title"
            title_elem = soup.select_one("h1")
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract description
            description = ""
            desc_elem = soup.select_one(".text-gray-500, .description, .summary")
            if desc_elem:
                description = desc_elem.get_text(strip=True)

            # Extract cover
            cover_url = ""
            img_elem = soup.select_one("img")
            if img_elem:
                cover_url = img_elem.get("src", "") or img_elem.get("data-src", "")
                if cover_url and not cover_url.startswith("http"):
                    cover_url = urljoin(self._base_url, cover_url)

            # Extract genres
            genres = []
            genre_elems = soup.select(".genre, .tag, .badge")
            for elem in genre_elems:
                genre = elem.get_text(strip=True)
                if genre:
                    genres.append(genre)

            return {
                "title": title,
                "description": description,
                "cover_image": cover_url,
                "genres": genres,
                "status": "Unknown",
                "year": None,
                "authors": [],
                "type": "manga",
            }

        except Exception as e:
            print(f"Error getting manga details: {e}")
            return {}

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga."""
        try:
            # Build manga URL
            manga_url = f"{self._base_url}/manga/{manga_id}"

            html = await self._make_request(manga_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find chapter links
            chapter_links = soup.select("a[href*='/chapters/']")

            chapters = []
            for link in chapter_links:
                try:
                    chapter_url = link.get("href", "")
                    if not chapter_url:
                        continue

                    # Extract chapter ID from URL like /chapters/12-10200000/title
                    chapter_match = re.search(r"/chapters/\d+-(\d+)/", chapter_url)
                    if not chapter_match:
                        continue

                    chapter_id = chapter_match.group(1)

                    # Get chapter title
                    chapter_title = link.get_text(strip=True) or f"Chapter {chapter_id}"

                    # Build full URL
                    if chapter_url.startswith("/"):
                        full_chapter_url = urljoin(self._base_url, chapter_url)
                    else:
                        full_chapter_url = chapter_url

                    chapter = {
                        "id": chapter_id,
                        "title": chapter_title,
                        "url": full_chapter_url,
                        "number": chapter_id,
                        "volume": None,
                        "date": None,
                    }

                    chapters.append(chapter)

                except Exception as e:
                    print(f"Error parsing chapter: {e}")
                    continue

            # Apply pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_chapters = chapters[start_idx:end_idx]

            total_chapters = len(chapters)
            has_more = end_idx < total_chapters

            return paginated_chapters, total_chapters, has_more

        except Exception as e:
            print(f"Error getting chapters: {e}")
            return [], 0, False

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter."""
        try:
            # Build chapter URL - need to find the actual chapter URL format
            # This might need adjustment based on actual MangaPill chapter URLs
            chapter_url = f"{self._base_url}/chapters/{manga_id}-{chapter_id}"

            html = await self._make_request(chapter_url)
            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")

            # Find page images
            page_urls = []
            img_elems = soup.select("img[src*='cdn'], img[data-src*='cdn']")

            for img in img_elems:
                img_url = img.get("src") or img.get("data-src")
                if img_url and ("cdn" in img_url or "mangap" in img_url):
                    if not img_url.startswith("http"):
                        img_url = urljoin(self._base_url, img_url)
                    page_urls.append(img_url)

            return page_urls

        except Exception as e:
            print(f"Error getting pages: {e}")
            return []

    async def download_page(self, page_url: str) -> bytes:
        """Download a page image."""
        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
                response = await client.get(page_url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"Error downloading page: {e}")
            return b""

    async def download_cover(self, manga_id: str) -> bytes:
        """Download manga cover."""
        try:
            # Get manga details to find cover URL
            details = await self.get_manga_details(manga_id)
            cover_url = details.get("cover_image", "")

            if not cover_url:
                return b""

            return await self.download_page(cover_url)

        except Exception as e:
            print(f"Error downloading cover: {e}")
            return b""
