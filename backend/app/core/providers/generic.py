import asyncio
import logging
import os
import random
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
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
        # Additional selectors for better metadata extraction
        search_title_selector: Optional[str] = None,
        search_cover_selector: Optional[str] = None,
        search_description_selector: Optional[str] = None,
        fallback_selectors: Optional[Dict[str, List[str]]] = None,
        use_flaresolverr: bool = False,
        flaresolverr_url: Optional[str] = None,
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
        # Enhanced anti-bot protection
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]

        self._headers = headers or self._get_random_headers()

        # FlareSolverr support
        self.use_flaresolverr = use_flaresolverr or bool(os.getenv("FLARESOLVERR_URL"))
        self.flaresolverr_url = flaresolverr_url or os.getenv("FLARESOLVERR_URL")

        if self.use_flaresolverr and self.flaresolverr_url:
            logger.info(
                f"Generic provider {name} using FlareSolverr at: {self.flaresolverr_url}"
            )

        # Search-specific selectors (fallback to main selectors if not provided)
        self._search_title_selector = search_title_selector or title_selector
        self._search_cover_selector = search_cover_selector or cover_selector
        self._search_description_selector = (
            search_description_selector or description_selector
        )

        # Fallback selectors for common patterns
        self._fallback_selectors = fallback_selectors or {
            "search_item": [
                ".manga-item",
                ".manga",
                ".series",
                ".book",
                ".comic",
                ".entry",
                ".post",
                ".item",
                ".result",
                ".card",
                "[class*='manga']",
                "[class*='series']",
                "[class*='book']",
                "[class*='comic']",
                "[class*='entry']",
                "[class*='item']",
                "article",
                ".media",
                ".thumbnail",
            ],
            "title": [
                ".manga-title",
                ".title",
                ".name",
                ".series-title",
                ".entry-title",
                ".post-title",
                ".book-title",
                "h1",
                "h2",
                "h3",
                "h4",
                ".heading",
                "[class*='title']",
                "[class*='name']",
                "[class*='heading']",
                "a[title]",
                ".link",
            ],
            "cover": [
                ".manga-cover img",
                ".cover img",
                ".thumbnail img",
                ".poster img",
                ".image img",
                ".avatar img",
                "img[class*='cover']",
                "img[class*='thumb']",
                "img[class*='poster']",
                "img[class*='image']",
                "img[class*='avatar']",
                "img[src*='cover']",
                "img[src*='thumb']",
                "img",
                ".img",
            ],
            "description": [
                ".manga-description",
                ".description",
                ".summary",
                ".synopsis",
                ".content",
                ".excerpt",
                ".abstract",
                "[class*='description']",
                "[class*='summary']",
                "[class*='synopsis']",
                "[class*='content']",
                "p",
                ".text",
            ],
            "link": [
                "a[href*='manga']",
                "a[href*='series']",
                "a[href*='book']",
                "a[href*='comic']",
                "a[href*='read']",
                "a[href*='view']",
                "a",
                ".link",
                "[href]",
            ],
            "status": [
                ".status",
                ".manga-status",
                ".publication-status",
                ".series-status",
                "[class*='status']",
                ".completed",
                ".ongoing",
                ".finished",
                ".publishing",
                ".hiatus",
                ".cancelled",
                ".dropped",
            ],
        }

    def _get_random_headers(self) -> Dict[str, str]:
        """Get randomized headers to avoid detection."""
        return {
            "User-Agent": random.choice(self._user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _make_request_with_retry(
        self, url: str, max_retries: int = 3
    ) -> Optional[str]:
        """Make HTTP request with retry logic and anti-bot protection."""
        for attempt in range(max_retries):
            try:
                # Add random delay to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    await asyncio.sleep(delay)

                # Try FlareSolverr first if available
                if self.use_flaresolverr and self.flaresolverr_url:
                    try:
                        async with httpx.AsyncClient() as client:
                            payload = {
                                "cmd": "request.get",
                                "url": url,
                                "maxTimeout": 60000,
                                "headers": self._headers,
                            }

                            response = await client.post(
                                f"{self.flaresolverr_url}/v1",
                                json=payload,
                                timeout=60.0,
                            )

                            if response.status_code == 200:
                                data = response.json()
                                if data.get("status") == "ok":
                                    return data["solution"]["response"]
                                else:
                                    logger.warning(
                                        f"FlareSolverr error for {url}: {data.get('message', 'Unknown error')}"
                                    )
                    except Exception as e:
                        logger.warning(f"FlareSolverr request failed for {url}: {e}")

                # Fallback to regular HTTP request
                async with httpx.AsyncClient() as client:
                    # Refresh headers for each attempt
                    headers = self._get_random_headers()

                    response = await client.get(
                        url, headers=headers, follow_redirects=True, timeout=30.0
                    )

                    response.raise_for_status()
                    return response.text

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.warning(
                        f"Access forbidden for {url} (attempt {attempt + 1}/{max_retries})"
                    )
                    if attempt == max_retries - 1:
                        logger.error(
                            f"All attempts failed for {url}. Site may require FlareSolverr."
                        )
                elif e.response.status_code == 404:
                    logger.error(f"URL not found: {url}")
                    break
                else:
                    logger.warning(
                        f"HTTP error {e.response.status_code} for {url} (attempt {attempt + 1}/{max_retries})"
                    )
            except Exception as e:
                logger.warning(
                    f"Request failed for {url} (attempt {attempt + 1}/{max_retries}): {e}"
                )

        return None

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
            if "{query}" in self._search_url:
                # Custom search URL format with query placeholder
                search_url = self._search_url.format(query=quote(query))
                # Add page and limit parameters if not already present
                if "?" in search_url:
                    search_url += f"&page={page}&limit={limit}"
                else:
                    search_url += f"?page={page}&limit={limit}"
            else:
                # Default search URL format
                search_url = (
                    f"{self._search_url}?q={quote(query)}&page={page}&limit={limit}"
                )

            # Make request with retry logic and anti-bot protection
            html = await self._make_request_with_retry(search_url)

            if not html:
                logger.error(f"Failed to get search results from {search_url}")
                return [], 0, False

            # Parse HTML
            soup = BeautifulSoup(html, "html.parser")

            # Find manga items using fallback selectors
            manga_items = soup.select(self._search_selector)

            # If no items found with primary selector, try fallback selectors
            if not manga_items:
                logger.warning(
                    f"No items found with primary selector '{self._search_selector}' for {self.name}"
                )
                for fallback_selector in self._fallback_selectors.get(
                    "search_item", []
                ):
                    try:
                        manga_items = soup.select(fallback_selector)
                        if manga_items:
                            logger.info(
                                f"Found {len(manga_items)} items with fallback selector '{fallback_selector}' for {self.name}"
                            )
                            break
                    except Exception as e:
                        logger.debug(
                            f"Fallback selector '{fallback_selector}' failed for {self.name}: {e}"
                        )
                        continue

            if not manga_items:
                logger.warning(
                    f"No manga items found on {self.name} for query '{query}'"
                )
                return [], 0, False

            logger.info(
                f"Found {len(manga_items)} potential manga items on {self.name}"
            )

            # Parse results
            results = []
            for item in manga_items:
                try:
                    # Get manga ID and URL using fallback selectors
                    manga_link = item.select_one("a")
                    if not manga_link:
                        # Try fallback link selectors
                        for link_selector in self._fallback_selectors.get("link", []):
                            try:
                                manga_link = item.select_one(link_selector)
                                if manga_link:
                                    break
                            except Exception:
                                continue

                    if not manga_link:
                        logger.debug(f"No link found in item for {self.name}")
                        continue

                    manga_url = manga_link.get("href", "")
                    if isinstance(manga_url, list):
                        manga_url = manga_url[0] if manga_url else ""
                    manga_id = self._extract_manga_id(manga_url)

                    if not manga_id:
                        continue

                    # Get title using fallback selectors
                    title = self._extract_text_with_fallback(
                        item, "title", self._search_title_selector
                    )
                    if not title:
                        continue

                    # Get cover using fallback selectors
                    cover_url = self._extract_image_with_fallback(
                        item, "cover", self._search_cover_selector
                    )

                    # Get description using fallback selectors
                    description = self._extract_text_with_fallback(
                        item, "description", self._search_description_selector
                    )

                    # Try to extract additional metadata from the search result
                    genres = self._extract_genres(item)
                    authors = self._extract_authors(item)
                    status = self._extract_status(item)

                    # Create search result
                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        alternative_titles={},
                        description=description or "",
                        cover_image=(
                            self._normalize_url(cover_url) if cover_url else ""
                        ),
                        type=MangaType.UNKNOWN,
                        status=status,
                        year=None,
                        is_nsfw=self._supports_nsfw,
                        genres=genres,
                        authors=authors,
                        provider=self.name,
                        url=self._manga_url_pattern.format(manga_id=manga_id),
                    )

                    results.append(result)
                except Exception as e:
                    logger.error(f"Error parsing manga item from {self.name}: {e}")

            # Determine if there are more results
            # This is a simple heuristic, might need to be adjusted for specific sites
            has_next = len(manga_items) >= limit

            return results, len(results), has_next
        except Exception as e:
            logger.error(f"Error searching for manga on {self.name}: {e}")
            # For debugging, let's also log the search URL that failed
            if "{query}" in self._search_url:
                search_url = self._search_url.format(query=quote(query))
                if "?" in search_url:
                    search_url += f"&page={page}&limit={limit}"
                else:
                    search_url += f"?page={page}&limit={limit}"
            else:
                search_url = (
                    f"{self._search_url}?q={quote(query)}&page={page}&limit={limit}"
                )
            logger.error(f"Failed search URL: {search_url}")
            logger.error(
                f"Provider {self.name} may need FlareSolverr or updated configuration"
            )
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
        """Get chapters for a manga with pagination support."""
        try:
            # Check if this provider needs multi-page chapter extraction
            all_chapters = await self._get_all_chapters_with_pagination(manga_id)

            if not all_chapters:
                return [], 0, False

            # Apply pagination to the complete chapter list
            total = len(all_chapters)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_chapters = all_chapters[start_idx:end_idx]
            has_next = end_idx < total

            return paginated_chapters, total, has_next
        except Exception as e:
            logger.error(f"Error getting chapters: {e}")
            return [], 0, False

    async def _get_all_chapters_with_pagination(
        self, manga_id: str
    ) -> List[Dict[str, Any]]:
        """Get all chapters across multiple pages if needed."""
        all_chapters = []
        current_page = 1
        max_pages = 10  # Safety limit to prevent infinite loops

        # Build base manga URL
        base_manga_url = self._manga_url_pattern.format(manga_id=manga_id)

        while current_page <= max_pages:
            try:
                # Build URL for current page
                if current_page == 1:
                    # First page usually has no page parameter
                    manga_url = base_manga_url
                else:
                    # Subsequent pages use ?page=N-1 (since page 2 is ?page=1)
                    page_param = current_page - 1
                    separator = "&" if "?" in base_manga_url else "?"
                    manga_url = f"{base_manga_url}{separator}page={page_param}"

                logger.info(f"Fetching chapters from page {current_page}: {manga_url}")

                # Make request
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        manga_url,
                        headers=self._headers,
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    html = response.text

                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")

                # Find chapter items on this page
                chapter_items = soup.select(self._chapter_selector)

                if not chapter_items:
                    logger.info(
                        f"No chapters found on page {current_page}, stopping pagination"
                    )
                    break

                logger.info(
                    f"Found {len(chapter_items)} chapters on page {current_page}"
                )

                # Parse chapters from this page
                page_chapters = []
                for item in chapter_items:
                    chapter = await self._parse_chapter_item(item, manga_id)
                    if chapter:
                        page_chapters.append(chapter)

                if not page_chapters:
                    logger.info(
                        f"No valid chapters parsed on page {current_page}, stopping"
                    )
                    break

                all_chapters.extend(page_chapters)

                # Check if there's a next page
                has_next_page = self._has_next_page(soup, current_page)
                if not has_next_page:
                    logger.info(
                        f"No next page found after page {current_page}, stopping pagination"
                    )
                    break

                current_page += 1

            except Exception as e:
                logger.error(f"Error fetching page {current_page}: {e}")
                break

        logger.info(
            f"Total chapters found across {current_page} pages: {len(all_chapters)}"
        )
        return all_chapters

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter with support for JavaScript-loaded content."""
        try:
            # Build chapter URL
            chapter_url = self._chapter_url_pattern.format(
                manga_id=manga_id, chapter_id=chapter_id
            )

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

                # First try to extract pages from Drupal.settings (for MangaSail)
                drupal_pages = self._extract_drupal_manga_pages(html)
                if drupal_pages:
                    logger.info(
                        f"Found {len(drupal_pages)} pages via Drupal.settings for {self.name}"
                    )
                    return drupal_pages

                # Fallback to standard HTML parsing
                soup = BeautifulSoup(html, "html.parser")

                # Find page images
                page_images = soup.select(self._page_selector)

                # Get page URLs
                page_urls = []
                for img in page_images:
                    src = img.get("src", "")
                    if isinstance(src, list):
                        src = src[0] if src else ""
                    if src:
                        # Make sure URL is absolute
                        src = self._normalize_url(src)
                        page_urls.append(src)

                return page_urls
        except Exception as e:
            logger.error(f"Error getting pages: {e}")
            return []

    def _extract_drupal_manga_pages(self, html: str) -> List[str]:
        """Extract manga pages from Drupal.settings JavaScript object."""
        try:
            import json

            # Find the Drupal.settings JavaScript
            pattern = r"jQuery\.extend\(Drupal\.settings,\s*({.*?})\);"
            match = re.search(pattern, html, re.DOTALL)

            if not match:
                return []

            settings_json = match.group(1)
            settings = json.loads(settings_json)

            # Extract showmanga data
            if "showmanga" in settings and "paths" in settings["showmanga"]:
                paths = settings["showmanga"]["paths"]

                # Filter out non-image entries (like ads)
                page_urls = []
                for path in paths:
                    if (
                        isinstance(path, str)
                        and path.startswith("http")
                        and any(
                            ext in path.lower()
                            for ext in [".jpg", ".jpeg", ".png", ".webp"]
                        )
                    ):
                        # Clean up URL encoding
                        clean_url = path.replace("%3F", "?")
                        page_urls.append(clean_url)

                return page_urls

            return []

        except Exception as e:
            logger.error(f"Error extracting Drupal manga pages: {e}")
            return []

    async def _parse_chapter_item(
        self, item, manga_id: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single chapter item."""
        try:
            # Handle case where the item IS the <a> tag (like OmegaScans)
            if item.name == "a":
                chapter_link = item
            else:
                # Standard case: find <a> tag inside the item
                chapter_link = item.select_one("a")
                if not chapter_link:
                    return None

            chapter_url = chapter_link.get("href", "")
            if isinstance(chapter_url, list):
                chapter_url = chapter_url[0] if chapter_url else ""
            chapter_id = self._extract_chapter_id(chapter_url)

            if not chapter_id:
                return None

            # Get chapter title - try multiple approaches
            chapter_title = ""

            # First try: direct text from the link
            if chapter_link.text.strip():
                chapter_title = chapter_link.text.strip()

            # Second try: look for span with chapter text inside the link
            if not chapter_title:
                title_span = chapter_link.select_one("span")
                if title_span:
                    chapter_title = title_span.text.strip()

            # Third try: extract from URL if no title found
            if not chapter_title:
                chapter_title = chapter_id.replace("-", " ").title()

            # Get chapter number from title or URL
            chapter_number = self._extract_chapter_number_from_text(
                chapter_title, chapter_url
            )

            # Create chapter
            return {
                "id": chapter_id,
                "title": chapter_title,
                "number": str(chapter_number) if chapter_number else "0",
                "volume": None,
                "language": "en",
                "pages_count": 0,
                "manga_id": manga_id,
                "publish_at": None,
                "readable_at": None,
                "source": self.name,
            }
        except Exception as e:
            logger.error(f"Error parsing chapter item: {e}")
            return None

    def _has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """Check if there's a next page available."""
        # Look for common pagination indicators
        next_selectors = [
            '.pagination a:contains("next")',
            '.pagination a:contains("Next")',
            '.pagination a:contains(">")',
            'a[href*="page="]:contains("next")',
            f'a[href*="page={current_page}"]',  # Look for next page number
        ]

        for selector in next_selectors:
            try:
                next_links = soup.select(selector)
                if next_links:
                    return True
            except Exception:
                continue

        # Alternative: look for page numbers higher than current
        try:
            page_links = soup.select('a[href*="page="]')
            for link in page_links:
                href = link.get("href", "")
                if f"page={current_page}" in href:
                    return True
        except Exception:
            pass

        return False

    def _extract_chapter_number_from_text(
        self, title: str, url: str
    ) -> Optional[float]:
        """Extract chapter number from title or URL."""

        # Try to extract from title first
        title_patterns = [
            r"chapter\s*(\d+(?:\.\d+)?)",
            r"ch\.?\s*(\d+(?:\.\d+)?)",
            r"#(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, title.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        # Try to extract from URL
        url_patterns = [
            r"-(\d+(?:\.\d+)?)/?$",
            r"/(\d+(?:\.\d+)?)/?$",
            r"chapter-(\d+(?:\.\d+)?)",
            r"ch-(\d+(?:\.\d+)?)",
        ]

        for pattern in url_patterns:
            match = re.search(pattern, url.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

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

    def _extract_text_with_fallback(
        self, element, field_type: str, primary_selector: str
    ) -> str:
        """Extract text using primary selector with fallback options."""
        # Try primary selector first
        if primary_selector:
            elem = element.select_one(primary_selector)
            if elem and elem.text.strip():
                return elem.text.strip()

        # Try fallback selectors
        fallback_selectors = self._fallback_selectors.get(field_type, [])
        for selector in fallback_selectors:
            try:
                elem = element.select_one(selector)
                if elem and elem.text.strip():
                    return elem.text.strip()
            except Exception:
                continue

        return ""

    def _extract_image_with_fallback(
        self, element, field_type: str, primary_selector: str
    ) -> str:
        """Extract image URL using primary selector with fallback options."""
        # Try primary selector first
        if primary_selector:
            try:
                elem = element.select_one(primary_selector)
                if elem:
                    src = elem.get("src", "")
                    if isinstance(src, str) and src:
                        logger.debug(
                            f"Found image with primary selector '{primary_selector}': {src}"
                        )
                        return src
            except Exception as e:
                logger.debug(f"Primary selector '{primary_selector}' failed: {e}")

        # Try fallback selectors
        fallback_selectors = self._fallback_selectors.get(field_type, [])
        for selector in fallback_selectors:
            try:
                elem = element.select_one(selector)
                if elem:
                    src = elem.get("src", "")
                    if isinstance(src, str) and src:
                        logger.debug(
                            f"Found image with fallback selector '{selector}': {src}"
                        )
                        return src
            except Exception as e:
                logger.debug(f"Fallback selector '{selector}' failed: {e}")
                continue

        # Special handling for MangaFox - try to find any img with cover in src
        try:
            all_imgs = element.select("img")
            for img in all_imgs:
                src = img.get("src", "")
                if src and ("cover" in src or "thumb" in src):
                    logger.debug(f"Found MangaFox cover image: {src}")
                    return src
        except Exception as e:
            logger.debug(f"MangaFox special handling failed: {e}")

        logger.debug(
            f"No image found for field_type '{field_type}' with primary selector '{primary_selector}'"
        )
        return ""

    def _extract_genres(self, element) -> List[str]:
        """Extract genres from element."""
        genres = []
        genre_selectors = [
            ".genre",
            ".genres .genre",
            ".tag",
            ".tags .tag",
            "[class*='genre']",
            "[class*='tag']",
            ".category",
        ]

        for selector in genre_selectors:
            try:
                genre_elems = element.select(selector)
                for genre_elem in genre_elems:
                    genre = genre_elem.text.strip()
                    if genre and genre not in genres:
                        genres.append(genre)
                if genres:  # If we found genres, stop trying other selectors
                    break
            except Exception:
                continue

        return genres

    def _extract_authors(self, element) -> List[str]:
        """Extract authors from element."""
        authors = []
        author_selectors = [
            ".author",
            ".authors .author",
            ".creator",
            ".artist",
            "[class*='author']",
            "[class*='creator']",
            "[class*='artist']",
        ]

        for selector in author_selectors:
            try:
                author_elems = element.select(selector)
                for author_elem in author_elems:
                    author = author_elem.text.strip()
                    if author and author not in authors:
                        authors.append(author)
                if authors:  # If we found authors, stop trying other selectors
                    break
            except Exception:
                continue

        return authors

    def _extract_status(self, element) -> "MangaStatus":
        """Extract status from element."""
        from app.schemas.manga import MangaStatus

        # First try the configured status selectors
        status_selectors = self._fallback_selectors.get("status", [])

        for selector in status_selectors:
            try:
                status_elem = element.select_one(selector)
                if status_elem:
                    status_text = status_elem.text.strip().lower()

                    # Map common status text to MangaStatus enum
                    if any(
                        word in status_text
                        for word in ["ongoing", "publishing", "serializing", "active"]
                    ):
                        return MangaStatus.ONGOING
                    elif any(
                        word in status_text
                        for word in ["completed", "finished", "ended", "complete"]
                    ):
                        return MangaStatus.COMPLETED
                    elif any(
                        word in status_text for word in ["hiatus", "on hold", "paused"]
                    ):
                        return MangaStatus.HIATUS
                    elif any(
                        word in status_text
                        for word in ["cancelled", "canceled", "dropped", "discontinued"]
                    ):
                        return MangaStatus.CANCELLED

                    # If we found status text but couldn't map it, return as ongoing (most common)
                    if status_text:
                        return MangaStatus.ONGOING
            except Exception:
                continue

        # Special handling for MangaFox - look for status in brackets like [Completed] or [Ongoing]
        try:
            # Get all text content from the element
            all_text = element.get_text()

            # Look for status patterns in brackets
            status_match = re.search(
                r"\[(completed|ongoing|finished|ended|hiatus|cancelled|dropped)\]",
                all_text,
                re.IGNORECASE,
            )
            if status_match:
                status_text = status_match.group(1).lower()
                if status_text in ["completed", "finished", "ended"]:
                    return MangaStatus.COMPLETED
                elif status_text == "ongoing":
                    return MangaStatus.ONGOING
                elif status_text == "hiatus":
                    return MangaStatus.HIATUS
                elif status_text in ["cancelled", "dropped"]:
                    return MangaStatus.CANCELLED
        except Exception:
            pass

        return MangaStatus.UNKNOWN

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to be absolute."""
        if not url:
            return ""

        # Handle list case (shouldn't happen but just in case)
        if isinstance(url, list):
            url = url[0] if url else ""

        # Already absolute URL
        if url.startswith(("http://", "https://")):
            return url

        # Protocol-relative URL
        if url.startswith("//"):
            return f"https:{url}"

        # Relative URL
        if url.startswith("/"):
            return f"{self._base_url.rstrip('/')}{url}"
        else:
            return f"{self._base_url.rstrip('/')}/{url}"
