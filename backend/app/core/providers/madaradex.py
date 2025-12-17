"""
MadaraDex provider for Kuroibara.

MadaraDex is a WordPress Madara-based manga aggregator site.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.schemas.manga import MangaStatus
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class MadaraDexProvider(BaseProvider):
    """Provider for MadaraDex - a WordPress Madara-based manga aggregator."""

    def __init__(self, **kwargs):
        self._base_url = "https://madaradex.org"
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
            "x-referer": self._base_url,
        }

    @property
    def name(self) -> str:
        return "MadaraDex"

    @property
    def url(self) -> str:
        return self._base_url

    @property
    def supports_nsfw(self) -> bool:
        return True

    async def _make_request(self, url: str, **kwargs) -> Optional[str]:
        """Make HTTP request with error handling."""
        try:
            async with aiohttp.ClientSession(
                headers=self._headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, **kwargs) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def _extract_manga_id_from_url(self, url: str) -> Optional[str]:
        """Extract manga ID from URL."""
        # URL format: https://madaradex.org/title/manga-name/
        match = re.search(r"/title/([^/]+)/?", url)
        return match.group(1) if match else None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text.strip())

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MadaraDex."""
        try:
            # Build search URL
            search_url = f"{self._base_url}/?s={query}&post_type=wp-manga"
            if page > 1:
                search_url += f"&paged={page}"

            html = await self._make_request(search_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Find search result items
            # Based on the search page structure
            search_items = soup.select(".c-tabs-item__content")

            for item in search_items:
                try:
                    # Extract title and URL
                    title_elem = item.select_one(".post-title h3 a, .post-title h4 a")
                    if not title_elem:
                        continue

                    title = self._clean_text(title_elem.get_text())
                    manga_url = title_elem.get("href")
                    if not manga_url:
                        continue
                    manga_url = str(manga_url)  # Ensure string type

                    manga_id = self._extract_manga_id_from_url(manga_url)
                    if not manga_id:
                        continue

                    # Extract cover image
                    cover_elem = item.select_one(".tab-thumb img")
                    cover_url = None
                    if cover_elem:
                        cover_url = cover_elem.get("src") or cover_elem.get("data-src")
                        if cover_url:
                            cover_url = str(cover_url)  # Ensure string type
                            if not cover_url.startswith("http"):
                                cover_url = urljoin(self._base_url, cover_url)

                    # Extract description
                    desc_elem = item.select_one(".tab-summary .post-content")
                    description = ""
                    if desc_elem:
                        description = self._clean_text(desc_elem.get_text())

                    # Extract genres
                    genres = []
                    genre_elems = item.select(".mg_genres .summary-content a")
                    if genre_elems:
                        genres = [self._clean_text(g.get_text()) for g in genre_elems]

                    # Extract status
                    status = MangaStatus.UNKNOWN
                    status_elem = item.select_one(".mg_status .summary-content")
                    if status_elem:
                        status_text = self._clean_text(status_elem.get_text()).lower()
                        if "ongoing" in status_text:
                            status = MangaStatus.ONGOING
                        elif "completed" in status_text:
                            status = MangaStatus.COMPLETED
                        elif "hiatus" in status_text:
                            status = MangaStatus.HIATUS

                    # Extract latest chapter for extra metadata
                    extra = {}
                    chapter_elem = item.select_one(".latest-chap .chapter a")
                    if chapter_elem:
                        extra["latest_chapter"] = self._clean_text(
                            chapter_elem.get_text()
                        )

                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        url=manga_url,
                        cover_image=cover_url,
                        description=description,
                        genres=genres,
                        status=status,
                        provider=self.name,
                        extra=extra if extra else None,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing search result item: {e}")
                    continue

            # Check if there are more results
            has_more = len(results) >= limit

            return results[:limit], len(results), has_more

        except Exception as e:
            logger.error(f"Error searching on {self.name}: {e}")
            return [], 0, False

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get detailed information about a manga."""
        try:
            manga_url = f"{self._base_url}/title/{manga_id}"
            html = await self._make_request(manga_url)
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")
            details = {}

            # Extract title
            title_elem = soup.select_one(".post-title h1, .post-title h2")
            if title_elem:
                details["title"] = self._clean_text(title_elem.get_text())

            # Extract cover image
            cover_elem = soup.select_one(".summary_image img")
            if cover_elem:
                cover_url = cover_elem.get("src") or cover_elem.get("data-src")
                if cover_url and not cover_url.startswith("http"):
                    cover_url = urljoin(self._base_url, cover_url)
                details["cover_url"] = cover_url

            # Extract description
            desc_elem = soup.select_one(".summary__content")
            if desc_elem:
                details["description"] = self._clean_text(desc_elem.get_text())

            # Extract metadata from summary content
            summary_items = soup.select(".post-content_item")
            for item in summary_items:
                label_elem = item.select_one(".summary-heading h5")
                content_elem = item.select_one(".summary-content")

                if not label_elem or not content_elem:
                    continue

                label = self._clean_text(label_elem.get_text()).lower()
                content = self._clean_text(content_elem.get_text())

                if "author" in label:
                    details["authors"] = [a.strip() for a in content.split(",")]
                elif "artist" in label:
                    details["artists"] = [a.strip() for a in content.split(",")]
                elif "genre" in label:
                    genre_links = content_elem.select("a")
                    if genre_links:
                        details["genres"] = [
                            self._clean_text(g.get_text()) for g in genre_links
                        ]
                    else:
                        details["genres"] = [g.strip() for g in content.split(",")]
                elif "status" in label:
                    details["status"] = content
                elif "alternative" in label:
                    details["alternative_titles"] = [
                        a.strip() for a in content.split(",")
                    ]

            # Extract rating
            rating_elem = soup.select_one(".total_votes")
            if rating_elem:
                try:
                    rating_text = self._clean_text(rating_elem.get_text())
                    rating_match = re.search(r"(\d+(?:\.\d+)?)", rating_text)
                    if rating_match:
                        details["rating"] = float(rating_match.group(1))
                except (ValueError, AttributeError):
                    pass

            return details

        except Exception as e:
            logger.error(f"Error getting manga details for {manga_id}: {e}")
            return {}

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga."""
        try:
            manga_url = f"{self._base_url}/title/{manga_id}"
            html = await self._make_request(manga_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")
            chapters = []

            # Find chapter links
            chapter_links = soup.select(".wp-manga-chapter a")

            for link in chapter_links:
                try:
                    chapter_url = link.get("href")
                    if not chapter_url:
                        continue

                    # Extract chapter ID from URL
                    # URL format: https://madaradex.org/title/manga-name/chapter-number
                    chapter_id_match = re.search(r"/chapter-([^/]+)/?", chapter_url)
                    if not chapter_id_match:
                        continue

                    chapter_id = chapter_id_match.group(1)
                    chapter_title = self._clean_text(link.get_text())

                    # Extract chapter number
                    chapter_num_match = re.search(
                        r"chapter\s*(\d+(?:\.\d+)?)", chapter_title.lower()
                    )
                    chapter_number = None
                    if chapter_num_match:
                        try:
                            chapter_number = float(chapter_num_match.group(1))
                        except ValueError:
                            pass

                    # Extract release date
                    date_elem = link.find_next(".chapter-release-date")
                    release_date = None
                    if date_elem:
                        release_date = self._clean_text(date_elem.get_text())

                    chapter = {
                        "id": chapter_id,
                        "title": chapter_title,
                        "url": chapter_url,
                        "number": chapter_number,
                        "release_date": release_date,
                    }
                    chapters.append(chapter)

                except Exception as e:
                    logger.error(f"Error parsing chapter: {e}")
                    continue

            # Sort chapters by number (descending - newest first)
            # Handle None values by treating them as 0
            chapters.sort(key=lambda x: x.get("number") or 0, reverse=True)

            # Apply pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_chapters = chapters[start_idx:end_idx]

            has_more = end_idx < len(chapters)

            return paginated_chapters, len(chapters), has_more

        except Exception as e:
            logger.error(f"Error getting chapters for {manga_id}: {e}")
            return [], 0, False

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter."""
        try:
            # Build chapter URL
            chapter_url = f"{self._base_url}/title/{manga_id}/chapter-{chapter_id}"

            html = await self._make_request(chapter_url)
            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")
            page_urls = []

            # Look for manga chapter images
            # MadaraDex uses the standard Madara theme structure
            img_selectors = [
                ".wp-manga-chapter-img",
                ".reading-content img",
                ".page-break img",
                "img[id^='image-']",
                ".entry-content img",
            ]

            for selector in img_selectors:
                img_elems = soup.select(selector)
                if img_elems:
                    for img in img_elems:
                        img_url = (
                            img.get("src")
                            or img.get("data-src")
                            or img.get("data-lazy-src")
                        )
                        if img_url:
                            # Ensure absolute URL
                            if not img_url.startswith("http"):
                                img_url = urljoin(self._base_url, img_url)

                            # Filter out non-manga images (ads, logos, etc.)
                            if any(
                                skip in img_url.lower()
                                for skip in ["logo", "banner", "ad", "advertisement"]
                            ):
                                continue

                            page_urls.append(img_url)
                    break  # Use first successful selector

            # If no images found in HTML, try to find them in JavaScript
            if not page_urls:
                # Look for image URLs in script tags
                script_tags = soup.find_all("script")
                for script in script_tags:
                    script_content = script.string or ""

                    # Look for common patterns in Madara themes
                    img_patterns = [
                        r'"(https?://[^"]*\.(?:jpg|jpeg|png|gif|webp))"',
                        r"'(https?://[^']*\.(?:jpg|jpeg|png|gif|webp))'",
                        r'src:\s*["\']([^"\']*\.(?:jpg|jpeg|png|gif|webp))["\']',
                    ]

                    for pattern in img_patterns:
                        matches = re.findall(pattern, script_content, re.IGNORECASE)
                        for match in matches:
                            if not match.startswith("http"):
                                match = urljoin(self._base_url, match)

                            # Filter out non-manga images
                            if any(
                                skip in match.lower()
                                for skip in ["logo", "banner", "ad", "advertisement"]
                            ):
                                continue

                            page_urls.append(match)

            # Remove duplicates while preserving order
            seen = set()
            unique_pages = []
            for url in page_urls:
                if url not in seen:
                    seen.add(url)
                    unique_pages.append(url)

            logger.info(
                f"Found {len(unique_pages)} pages for {manga_id} chapter {chapter_id}"
            )
            return unique_pages

        except Exception as e:
            logger.error(
                f"Error getting pages for {manga_id} chapter {chapter_id}: {e}"
            )
            return []

    async def download_page(self, page_url: str) -> bytes:
        """Download a page image."""
        try:
            async with aiohttp.ClientSession(
                headers=self._headers, timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                async with session.get(page_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.warning(f"HTTP {response.status} for page {page_url}")
                        return b""
        except Exception as e:
            logger.error(f"Error downloading page {page_url}: {e}")
            return b""

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover."""
        try:
            # Get manga details to find cover URL
            details = await self.get_manga_details(manga_id)
            cover_url = details.get("cover_url")

            if not cover_url:
                logger.warning(f"No cover URL found for {manga_id}")
                return b""

            return await self.download_page(cover_url)

        except Exception as e:
            logger.error(f"Error downloading cover for {manga_id}: {e}")
            return b""

    async def get_available_manga(
        self, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Get available/popular manga from MadaraDex."""
        try:
            # Try to get popular manga from the homepage
            html = await self._make_request(f"{self._base_url}/")
            if not html:
                return await super().get_available_manga(page, limit)

            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Look for manga items on the homepage
            manga_selectors = [
                ".page-item-detail",
                ".manga-item",
                ".item-summary",
                ".slider__item",
            ]

            manga_items = []
            for selector in manga_selectors:
                manga_items = soup.select(selector)
                if manga_items:
                    break

            for item in manga_items[:limit]:
                try:
                    # Extract title and URL
                    title_elem = item.select_one("h3 a, h4 a, .post-title a")
                    if not title_elem:
                        continue

                    title = self._clean_text(title_elem.get_text())
                    manga_url = title_elem.get("href")
                    if not manga_url:
                        continue

                    manga_id = self._extract_manga_id_from_url(manga_url)
                    if not manga_id:
                        continue

                    # Extract cover image
                    cover_elem = item.select_one("img")
                    cover_url = None
                    if cover_elem:
                        cover_url = cover_elem.get("src") or cover_elem.get("data-src")
                        if cover_url and not cover_url.startswith("http"):
                            cover_url = urljoin(self._base_url, cover_url)

                    # Extract latest chapter if available
                    metadata = {}
                    chapter_elem = item.select_one(".chapter a, .latest-chap a")
                    if chapter_elem:
                        metadata["latest_chapter"] = self._clean_text(
                            chapter_elem.get_text()
                        )

                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        url=manga_url,
                        cover_image=cover_url,
                        description="",
                        provider=self.name,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing manga item: {e}")
                    continue

            if not results:
                # Fallback to search-based approach
                return await super().get_available_manga(page, limit)

            return results, len(results), len(manga_items) > limit

        except Exception as e:
            logger.error(f"Error getting available manga from {self.name}: {e}")
            return await super().get_available_manga(page, limit)
