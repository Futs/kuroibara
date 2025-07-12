"""
Enhanced Generic Provider with Cloudflare bypass support.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class FlareSolverrClient:
    """Simplified FlareSolverr client for the enhanced provider."""

    def __init__(self, flaresolverr_url: str = "http://flaresolverr:8191"):
        self.flaresolverr_url = flaresolverr_url
        self.session_id = None

    async def get(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make a GET request through FlareSolverr."""
        try:
            request_data = {"cmd": "request.get", "url": url, "maxTimeout": 60000}

            if headers:
                request_data["headers"] = headers

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.flaresolverr_url}/v1", json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        solution = data.get("solution", {})
                        return {
                            "status_code": solution.get("status"),
                            "content": solution.get("response"),
                            "url": solution.get("url"),
                        }

        except Exception as e:
            logger.error(f"FlareSolverr request failed for {url}: {e}")

        return None


class EnhancedGenericProvider(BaseProvider):
    """Enhanced generic provider with Cloudflare bypass and better selectors."""

    def __init__(
        self,
        base_url: str,
        search_url: str,
        manga_url_pattern: str,
        chapter_url_pattern: str,
        name: str = "Enhanced Generic",
        supports_nsfw: bool = False,
        use_flaresolverr: bool = False,
        flaresolverr_url: str = "http://flaresolverr:8191",
        headers: Optional[Dict[str, str]] = None,
        # Enhanced selector configuration
        selectors: Optional[Dict[str, Any]] = None,
    ):
        self._base_url = base_url
        self._search_url = search_url
        self._manga_url_pattern = manga_url_pattern
        self._chapter_url_pattern = chapter_url_pattern
        self._name = name
        self._supports_nsfw = supports_nsfw
        self._use_flaresolverr = use_flaresolverr

        # Default headers
        self._headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Enhanced selectors with fallbacks
        self._selectors = selectors or {
            "search_items": [
                ".manga-item",
                ".search-result",
                ".item",
                ".result",
                "[class*='manga']",
                "[class*='item']",
                "[class*='result']",
                "[class*='book']",
                "[class*='comic']",
                "[class*='series']",
            ],
            "title": [
                ".title",
                ".manga-title",
                ".name",
                ".series-title",
                "h1",
                "h2",
                "h3",
                "h4",
                "a[title]",
                "[class*='title']",
                "[class*='name']",
            ],
            "cover": [
                ".cover img",
                ".thumbnail img",
                ".poster img",
                ".image img",
                "img[src*='cover']",
                "img[src*='thumb']",
                "img[src*='poster']",
                ".manga-cover img",
                "[class*='cover'] img",
                "[class*='thumb'] img",
            ],
            "description": [
                ".description",
                ".summary",
                ".synopsis",
                ".overview",
                "[class*='desc']",
                "[class*='summary']",
                "[class*='synopsis']",
            ],
            "link": [
                "a[href*='manga']",
                "a[href*='series']",
                "a[href*='comic']",
                "a[href*='read']",
                ".title a",
                ".name a",
                "h3 a",
                "h4 a",
            ],
        }

        # Initialize FlareSolverr client if needed
        self._flaresolverr = (
            FlareSolverrClient(flaresolverr_url) if use_flaresolverr else None
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._base_url

    @property
    def supports_nsfw(self) -> bool:
        return self._supports_nsfw

    async def _make_request(self, url: str) -> Optional[str]:
        """Make a request with Cloudflare bypass if needed."""

        # Try normal request first
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url, headers=self._headers)

                # Check for Cloudflare protection
                if (
                    response.status_code in [403, 503, 521]
                    or "cloudflare" in response.text.lower()
                    or "checking your browser" in response.text.lower()
                ):

                    logger.info(f"Cloudflare protection detected for {url}")

                    if self._use_flaresolverr and self._flaresolverr:
                        logger.info(f"Using FlareSolverr for {url}")
                        result = await self._flaresolverr.get(url, self._headers)
                        if result and result.get("status_code") == 200:
                            return result.get("content")

                    return None

                if response.status_code == 200:
                    return response.text

        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")

            # Try FlareSolverr as fallback
            if self._use_flaresolverr and self._flaresolverr:
                logger.info(f"Using FlareSolverr as fallback for {url}")
                result = await self._flaresolverr.get(url, self._headers)
                if result and result.get("status_code") == 200:
                    return result.get("content")

        return None

    def _find_element_with_selectors(
        self, soup: BeautifulSoup, selector_list: List[str], attribute: str = None
    ):
        """Find element using multiple selectors as fallbacks."""
        for selector in selector_list:
            try:
                elements = soup.select(selector)
                if elements:
                    element = elements[0]
                    if attribute:
                        value = element.get(attribute)
                        if value:
                            return value
                    else:
                        return element
            except Exception:
                continue
        return None

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga with enhanced selector support."""
        try:
            # Build search URL
            search_url = self._search_url.format(query=query, page=page, limit=limit)
            if "?" not in search_url:
                search_url += f"?q={query}"

            # Make request
            html = await self._make_request(search_url)
            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find search result items using multiple selectors
            items = None
            for selector in self._selectors["search_items"]:
                items = soup.select(selector)
                if items:
                    logger.info(
                        f"Found {len(items)} items with selector '{selector}' for {self.name}"
                    )
                    break

            if not items:
                logger.warning(f"No search results found for {self.name}")
                return [], 0, False

            results = []
            for item in items[:limit]:
                try:
                    # Extract title
                    title_element = self._find_element_with_selectors(
                        item, self._selectors["title"]
                    )
                    title = (
                        title_element.get_text(strip=True)
                        if title_element
                        else "Unknown Title"
                    )

                    # Extract link
                    link_element = self._find_element_with_selectors(
                        item, self._selectors["link"]
                    )
                    if link_element:
                        href = link_element.get("href")
                        if href:
                            if href.startswith("/"):
                                href = urljoin(self._base_url, href)
                            # Extract manga ID from URL
                            manga_id = href.split("/")[-1] or href.split("/")[-2]
                        else:
                            continue
                    else:
                        continue

                    # Extract cover image
                    cover_element = self._find_element_with_selectors(
                        item, self._selectors["cover"]
                    )
                    cover_url = None
                    if cover_element:
                        cover_url = cover_element.get("src") or cover_element.get(
                            "data-src"
                        )
                        if cover_url and cover_url.startswith("/"):
                            cover_url = urljoin(self._base_url, cover_url)

                    # Extract description
                    desc_element = self._find_element_with_selectors(
                        item, self._selectors["description"]
                    )
                    description = (
                        desc_element.get_text(strip=True) if desc_element else ""
                    )

                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        cover_image=cover_url,
                        description=description,
                        provider=self.name,
                        url=href,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing search result item: {e}")
                    continue

            return results, len(results), len(items) > limit

        except Exception as e:
            logger.error(f"Error searching on {self.name}: {e}")
            return [], 0, False

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get manga details with enhanced extraction."""
        try:
            manga_url = self._manga_url_pattern.format(manga_id=manga_id)
            html = await self._make_request(manga_url)

            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_element = self._find_element_with_selectors(
                soup, self._selectors["title"]
            )
            title = (
                title_element.get_text(strip=True) if title_element else "Unknown Title"
            )

            # Extract description
            desc_element = self._find_element_with_selectors(
                soup, self._selectors["description"]
            )
            description = desc_element.get_text(strip=True) if desc_element else ""

            # Extract cover
            cover_element = self._find_element_with_selectors(
                soup, self._selectors["cover"]
            )
            cover_url = None
            if cover_element:
                cover_url = cover_element.get("src") or cover_element.get("data-src")
                if cover_url and cover_url.startswith("/"):
                    cover_url = urljoin(self._base_url, cover_url)

            return {
                "id": manga_id,
                "title": title,
                "description": description,
                "cover_image": cover_url,
                "provider": self.name,
                "url": manga_url,
                "type": "manga",
                "status": "unknown",
                "is_nsfw": self._supports_nsfw,
                "genres": [],
                "authors": [],
            }

        except Exception as e:
            logger.error(f"Error getting manga details for {manga_id}: {e}")
            return {}

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters (basic implementation)."""
        # This would need to be implemented based on site structure
        return [], 0, False

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages (basic implementation)."""
        # This would need to be implemented based on site structure
        return []

    async def download_page(self, page_url: str) -> bytes:
        """Download a page."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(page_url, headers=self._headers)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Error downloading page {page_url}: {e}")
            return b""

    async def download_cover(self, manga_id: str) -> bytes:
        """Download manga cover."""
        try:
            manga_details = await self.get_manga_details(manga_id)
            cover_url = manga_details.get("cover_image")

            if cover_url:
                return await self.download_page(cover_url)

        except Exception as e:
            logger.error(f"Error downloading cover for {manga_id}: {e}")

        return b""
