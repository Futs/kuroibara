"""
MangaSail provider implementation.
"""

import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class MangaSailProvider(BaseProvider):
    """Provider for MangaSail."""

    def __init__(self):
        self._base_url = "https://www.sailmg.com"
        self._search_url = "https://www.sailmg.com/search/node/{query}"
        self._manga_url_pattern = "https://www.sailmg.com/content/{manga_id}"
        self._chapter_url_pattern = "https://www.sailmg.com/content/{chapter_id}"
        self._name = "MangaSail"
        self._supports_nsfw = False

    async def _make_request(self, url: str, timeout: int = 30) -> str:
        """Make an HTTP request and return the response text."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return ""
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            return ""

    def _clean_manga_title(self, raw_title: str) -> str:
        """Clean manga title by removing chapter numbers and extra info."""
        import re

        if not raw_title:
            return ""

        # Remove chapter numbers at the end (e.g., "Mercenary Enrollment 251" -> "Mercenary Enrollment")
        # Pattern matches: space + number(s) at the end
        cleaned = re.sub(r"\s+\d+(\.\d+)?$", "", raw_title.strip())

        # Remove common chapter indicators
        cleaned = re.sub(
            r"\s+(ch|chapter|ep|episode)\s*\d+.*$", "", cleaned, flags=re.IGNORECASE
        )

        # Remove extra whitespace
        cleaned = " ".join(cleaned.split())

        return cleaned if cleaned else raw_title

    def _extract_base_manga_id(self, url: str) -> str:
        """Extract base manga ID from URL, removing chapter-specific parts."""
        import re

        # Extract the last part of the URL
        url_parts = url.rstrip("/").split("/")
        if not url_parts:
            return ""

        manga_id = url_parts[-1]

        # Remove chapter numbers from the ID (e.g., "mercenary-enrollment-251" -> "mercenary-enrollment")
        # Pattern matches: dash + number(s) at the end
        base_id = re.sub(r"-\d+(\.\d+)?$", "", manga_id)

        return base_id if base_id else manga_id

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MangaSail."""
        try:
            search_url = self._search_url.format(query=query)
            html = await self._make_request(search_url)

            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find manga items using content links selector
            manga_items = soup.select("a[href*='/content/']")

            # Filter out navigation links
            manga_items = [
                item
                for item in manga_items
                if item.get_text(strip=True)
                and "skip to main content" not in item.get_text(strip=True).lower()
            ]

            if not manga_items:
                logger.warning(f"No manga items found for query '{query}' on MangaSail")
                return [], 0, False

            results = []
            for item in manga_items[:limit]:
                try:
                    # Extract title from link text
                    raw_title = item.get_text(strip=True)
                    if not raw_title:
                        continue

                    # Clean title by removing chapter numbers
                    title = self._clean_manga_title(raw_title)
                    if not title:
                        continue

                    # Extract link and manga ID
                    href = item.get("href")
                    if not href:
                        continue

                    if not href.startswith("http"):
                        href = urljoin(self._base_url, href)

                    # Extract base manga ID from URL (remove chapter-specific parts)
                    manga_id = self._extract_base_manga_id(
                        href.split("/")[-1] or href.split("/")[-2]
                    )
                    if not manga_id:
                        continue

                    # Look for cover image (might be in parent or sibling elements)
                    cover_url = ""
                    # Try to find image in parent container
                    parent = item.parent
                    if parent:
                        img_elem = parent.find("img")
                        if img_elem:
                            cover_url = (
                                img_elem.get("src") or img_elem.get("data-src") or ""
                            )
                            if cover_url and not cover_url.startswith("http"):
                                cover_url = urljoin(self._base_url, cover_url)

                    # Construct base manga URL using the cleaned manga ID
                    base_manga_url = f"{self._base_url}/content/{manga_id}"

                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        alternative_titles={},
                        description="",
                        cover_image=cover_url,
                        type=MangaType.UNKNOWN,
                        status=MangaStatus.UNKNOWN,
                        year=None,
                        is_nsfw=False,  # MangaSail is generally safe
                        genres=[],
                        authors=[],
                        provider=self.name,
                        url=base_manga_url,
                        in_library=False,
                        extra=None,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing manga item on MangaSail: {e}")
                    continue

            total = len(results)
            has_more = len(manga_items) > limit

            logger.info(
                f"MangaSail search for '{query}' returned {len(results)} results"
            )
            return results, total, has_more

        except Exception as e:
            logger.error(f"Error searching for manga on MangaSail: {e}")
            return [], 0, False

    async def get_available_manga(
        self, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Get available/popular manga from MangaSail."""
        try:
            # MangaSail homepage has popular manga
            popular_url = f"{self._base_url}/"

            html = await self._make_request(popular_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find manga items using content links selector
            manga_items = soup.select("a[href*='/content/']")

            # Filter out navigation links
            manga_items = [
                item
                for item in manga_items
                if item.get_text(strip=True)
                and "skip to main content" not in item.get_text(strip=True).lower()
            ]

            if not manga_items:
                logger.warning("No manga items found on MangaSail homepage")
                return [], 0, False

            results = []
            for item in manga_items[:limit]:
                try:
                    # Extract title from link text
                    raw_title = item.get_text(strip=True)
                    if not raw_title:
                        continue

                    # Clean title by removing chapter numbers
                    title = self._clean_manga_title(raw_title)
                    if not title:
                        continue

                    # Extract link and manga ID
                    href = item.get("href")
                    if not href:
                        continue

                    if not href.startswith("http"):
                        href = urljoin(self._base_url, href)

                    # Extract base manga ID from URL (remove chapter-specific parts)
                    manga_id = self._extract_base_manga_id(
                        href.split("/")[-1] or href.split("/")[-2]
                    )
                    if not manga_id:
                        continue

                    # Look for cover image (might be in parent or sibling elements)
                    cover_url = ""
                    # Try to find image in parent container
                    parent = item.parent
                    if parent:
                        img_elem = parent.find("img")
                        if img_elem:
                            cover_url = (
                                img_elem.get("src") or img_elem.get("data-src") or ""
                            )
                            if cover_url and not cover_url.startswith("http"):
                                cover_url = urljoin(self._base_url, cover_url)

                    # Construct base manga URL using the cleaned manga ID
                    base_manga_url = f"{self._base_url}/content/{manga_id}"

                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        alternative_titles={},
                        description="",
                        cover_image=cover_url,
                        type=MangaType.UNKNOWN,
                        status=MangaStatus.UNKNOWN,
                        year=None,
                        is_nsfw=False,  # MangaSail is generally safe
                        genres=[],
                        authors=[],
                        provider=self.name,
                        url=base_manga_url,
                        in_library=False,
                        extra=None,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing manga item on MangaSail: {e}")
                    continue

            total = len(results)
            has_more = len(manga_items) > limit

            logger.info(
                f"MangaSail get_available_manga returned {len(results)} results"
            )
            return results, total, has_more

        except Exception as e:
            logger.error(f"Error getting available manga from MangaSail: {e}")
            return [], 0, False

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get detailed information about a manga."""
        try:
            manga_url = self._manga_url_pattern.format(manga_id=manga_id)
            html = await self._make_request(manga_url)

            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            # Extract basic details
            title = ""
            title_elem = soup.select_one("h1, .title, .manga-title")
            if title_elem:
                title = title_elem.get_text(strip=True)

            description = ""
            desc_elem = soup.select_one(".description, .summary, .synopsis")
            if desc_elem:
                description = desc_elem.get_text(strip=True)

            return {
                "title": title,
                "description": description,
                "status": MangaStatus.UNKNOWN,
                "type": MangaType.UNKNOWN,
                "year": None,
                "genres": [],
                "authors": [],
                "alternative_titles": {},
                "is_nsfw": False,
            }

        except Exception as e:
            logger.error(f"Error getting manga details for {manga_id}: {e}")
            return {}

    async def get_chapters(self, manga_id: str) -> List[Dict[str, Any]]:
        """Get chapters for a manga."""
        try:
            manga_url = self._manga_url_pattern.format(manga_id=manga_id)
            html = await self._make_request(manga_url)

            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")

            chapters = []
            # Look for chapter links
            chapter_links = soup.select("a[href*='/content/']")

            for i, link in enumerate(chapter_links):
                href = link.get("href")
                if href:
                    chapter_id = href.split("/")[-1] or href.split("/")[-2]
                    title = link.get_text(strip=True) or f"Chapter {i + 1}"

                    chapters.append(
                        {
                            "id": chapter_id,
                            "title": title,
                            "url": (
                                urljoin(self._base_url, href)
                                if not href.startswith("http")
                                else href
                            ),
                            "number": i + 1,
                        }
                    )

            return chapters

        except Exception as e:
            logger.error(f"Error getting chapters for {manga_id}: {e}")
            return []

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover."""
        try:
            # Get manga details to find cover URL
            details = await self.get_manga_details(manga_id)
            cover_url = details.get("cover_image", "")

            if not cover_url:
                return b""

            async with aiohttp.ClientSession() as session:
                async with session.get(cover_url) as response:
                    if response.status == 200:
                        return await response.read()
                    return b""

        except Exception as e:
            logger.error(f"Error downloading cover for {manga_id}: {e}")
            return b""

    async def get_pages(self, chapter_id: str) -> List[str]:
        """Get pages for a chapter."""
        try:
            chapter_url = self._chapter_url_pattern.format(chapter_id=chapter_id)
            html = await self._make_request(chapter_url)

            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")

            # Look for page images
            page_images = []
            img_elements = soup.select(
                "img[src*='sailmg.com'], img[data-src*='sailmg.com']"
            )

            for img in img_elements:
                src = img.get("src") or img.get("data-src")
                if src:
                    if not src.startswith("http"):
                        src = urljoin(self._base_url, src)
                    page_images.append(src)

            return page_images

        except Exception as e:
            logger.error(f"Error getting pages for chapter {chapter_id}: {e}")
            return []

    async def download_page(self, page_url: str) -> bytes:
        """Download a page image."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(page_url) as response:
                    if response.status == 200:
                        return await response.read()
                    return b""

        except Exception as e:
            logger.error(f"Error downloading page {page_url}: {e}")
            return b""

    @property
    def name(self) -> str:
        """Provider name."""
        return "MangaSail"

    @property
    def supports_nsfw(self) -> bool:
        """Whether provider supports NSFW content."""
        return False

    @property
    def url(self) -> str:
        """Provider URL."""
        return self._base_url
