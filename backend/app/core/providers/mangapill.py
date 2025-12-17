import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


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

    def _extract_title_from_element(self, element, link_elem=None):
        """Extract title from element using multiple strategies."""
        title = "Unknown Title"

        # Try title from link element first if provided
        if link_elem:
            if link_elem.get("title"):
                return link_elem.get("title").strip()
            elif link_elem.get("aria-label"):
                return link_elem.get("aria-label").strip()

        # Try multiple selectors within the element
        title_selectors = [
            ".font-bold",
            ".text-truncate",
            ".title",
            "a[href*='/manga/']",
            ".manga-title",
            ".name",
            "h3",
            "h4",
            ".text-sm",
            ".text-base",
        ]

        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                candidate_title = title_elem.get_text(strip=True)
                if (
                    candidate_title
                    and len(candidate_title) > 1
                    and not candidate_title.isdigit()
                ):
                    return candidate_title

        # Try image alt text
        img_elem = element.select_one("img")
        if img_elem and img_elem.get("alt"):
            alt_text = img_elem.get("alt").strip()
            if alt_text and len(alt_text) > 1:
                return alt_text

        return title

    def _extract_cover_url(self, element):
        """Extract cover image URL from element."""
        img_elem = element.select_one("img")
        if not img_elem:
            return ""

        # Try different image source attributes
        cover_url = (
            img_elem.get("src")
            or img_elem.get("data-src")
            or img_elem.get("data-lazy")
            or img_elem.get("data-original")
            or ""
        )

        if not cover_url:
            return ""

        # Make URL absolute
        if not cover_url.startswith("http"):
            cover_url = urljoin(self._base_url, cover_url)

        # Handle lazy loading placeholders
        if "placeholder" in cover_url.lower() or "loading" in cover_url.lower():
            for attr in ["data-src", "data-lazy", "data-original"]:
                real_url = img_elem.get(attr)
                if real_url and "placeholder" not in real_url.lower():
                    return (
                        real_url
                        if real_url.startswith("http")
                        else urljoin(self._base_url, real_url)
                    )

        return cover_url

    def _clean_title(self, title):
        """Clean up extracted title."""
        if not title or title == "Unknown Title":
            return "Unknown Title"

        title = title.replace("Manga", "").replace("Read", "").strip()
        return title if len(title) >= 2 else "Unknown Title"

    def _create_search_result(self, manga_id, title, cover_url, manga_url):
        """Create a SearchResult object."""
        full_url = (
            urljoin(self._base_url, manga_url)
            if manga_url.startswith("/")
            else manga_url
        )

        return SearchResult(
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

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MangaPill."""
        try:
            search_url = f"{self._base_url}/search?q={query}&type=&status="
            html = await self._make_request(search_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find the results grid container
            grid = None
            for g in soup.select(".grid"):
                if g.select("a[href*='/manga/']"):
                    grid = g
                    break

            if not grid:
                return [], 0, False

            # Find manga items in the grid
            items = [
                child
                for child in grid.children
                if hasattr(child, "name")
                and child.name
                and child.select("a[href*='/manga/']")
            ]

            if not items:
                return [], 0, False

            results = []
            for item in items:
                try:
                    link_elem = item.select_one("a[href*='/manga/']")
                    if not link_elem:
                        continue

                    manga_url = link_elem.get("href", "")
                    manga_id = self._extract_manga_id_from_url(manga_url)
                    if not manga_id:
                        continue

                    # Extract title and cover using helper methods
                    title = self._extract_title_from_element(item, link_elem)
                    if title == "Unknown Title" and manga_url:
                        # Last resort: extract from URL
                        url_part = (
                            manga_url.split("/manga/")[-1].split("/")[0]
                            if "/manga/" in manga_url
                            else ""
                        )
                        if url_part:
                            title = url_part.replace("-", " ").replace("_", " ").title()

                    title = self._clean_title(title)
                    cover_url = self._extract_cover_url(item)

                    result = self._create_search_result(
                        manga_id, title, cover_url, manga_url
                    )
                    results.append(result)

                    if len(results) >= limit:
                        break

                except Exception as e:
                    print(f"Error parsing manga item: {e}")
                    continue

            return results, len(results), len(items) > len(results)

        except Exception as e:
            print(f"Search error: {e}")
            return [], 0, False

    def _extract_title_from_link(self, item):
        """Extract title from link element using multiple strategies."""
        # Try title attribute first
        if item.get("title"):
            return item.get("title").strip()
        elif item.get("aria-label"):
            return item.get("aria-label").strip()

        # Try finding title in child elements
        title_selectors = [
            ".font-bold",
            ".text-truncate",
            ".title",
            ".manga-title",
            ".name",
            "h3",
            "h4",
            ".text-sm",
            ".text-base",
            "span",
            "div",
        ]

        for selector in title_selectors:
            title_elem = item.find(selector)
            if title_elem:
                candidate_title = title_elem.get_text(strip=True)
                if (
                    candidate_title
                    and len(candidate_title) > 1
                    and not candidate_title.isdigit()
                ):
                    return candidate_title

        # Try image alt/title text
        img_elem = item.find("img")
        if img_elem:
            for attr in ["alt", "title"]:
                text = img_elem.get(attr, "").strip()
                if text and len(text) > 1:
                    return text

        # Try text content as fallback
        text_content = item.get_text(strip=True)
        if text_content and len(text_content) > 1 and not text_content.isdigit():
            lines = [line.strip() for line in text_content.split("\n") if line.strip()]
            for line in lines:
                if len(line) > 1 and not line.isdigit():
                    return line

        return "Unknown Title"

    def _find_manga_items(self, soup):
        """Find manga items using multiple selectors."""
        selectors = [
            "a[href*='/manga/']",  # Any manga links (most general)
            ".grid a[href*='/manga/']",  # Direct links in grid
            ".manga-item",
            ".grid .item",
            ".flex a[href*='/manga/']",  # Flex layout links
            ".space-y-2 a[href*='/manga/']",  # Spaced layout links
        ]

        for selector in selectors:
            manga_items = soup.select(selector)
            if manga_items:
                logger.info(
                    f"Found {len(manga_items)} manga items with selector '{selector}'"
                )
                return manga_items

        return []

    async def get_available_manga(
        self, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Get available/popular manga from MangaPill."""
        try:
            html = await self._make_request(f"{self._base_url}/")
            if not html:
                return await super().get_available_manga(page, limit)

            soup = BeautifulSoup(html, "html.parser")
            manga_items = self._find_manga_items(soup)

            if not manga_items:
                logger.warning("No manga items found on MangaPill popular page")
                return await super().get_available_manga(page, limit)

            results = []
            for item in manga_items[:limit]:
                try:
                    href = item.get("href")
                    if not href:
                        continue

                    if not href.startswith("http"):
                        href = urljoin(self._base_url, href)

                    manga_id = (
                        href.split("/manga/")[-1].split("/")[0]
                        if "/manga/" in href
                        else ""
                    )
                    if not manga_id:
                        continue

                    # Extract title using helper method
                    title = self._extract_title_from_link(item)
                    if title == "Unknown Title" and href and "/manga/" in href:
                        url_part = href.split("/manga/")[-1].split("/")[0]
                        if url_part:
                            title = url_part.replace("-", " ").replace("_", " ").title()

                    title = self._clean_title(title)

                    # Extract cover image using existing helper
                    cover_url = ""
                    img_elem = item.find("img")
                    if img_elem:
                        cover_url = (
                            img_elem.get("src")
                            or img_elem.get("data-src")
                            or img_elem.get("data-lazy")
                            or img_elem.get("data-original")
                            or ""
                        )
                        if cover_url and not cover_url.startswith("http"):
                            cover_url = urljoin(self._base_url, cover_url)

                    # Create result
                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        alternative_titles={},
                        description="",
                        cover_image=cover_url,
                        type=MangaType.UNKNOWN,
                        status=MangaStatus.UNKNOWN,
                        year=None,
                        is_nsfw=False,
                        genres=[],
                        authors=[],
                        provider=self.name,
                        url=href,
                        in_library=False,
                        extra=None,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing manga item on MangaPill: {e}")
                    continue

            logger.info(
                f"MangaPill get_available_manga returned {len(results)} results"
            )
            return results, len(results), len(manga_items) > limit

        except Exception as e:
            logger.error(f"Error getting available manga from MangaPill: {e}")
            return await super().get_available_manga(page, limit)

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

    async def download_page(
        self, page_url: str, referer: Optional[str] = None
    ) -> bytes:
        """
        Download a page image with proper headers.

        Args:
            page_url: The URL of the page to download
            referer: Optional referer URL (chapter page URL)

        Returns:
            The page content as bytes
        """
        try:
            # Use provided referer or fall back to base URL
            headers = dict(self._headers)
            if referer:
                headers["Referer"] = referer
            else:
                headers["Referer"] = self._base_url

            async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
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
