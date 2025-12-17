"""
HiperDEX provider implementation using JavaScriptProvider base class.

HiperDEX (https://hiperdex.com) is a WordPress/Madara-based NSFW manga site
that uses JavaScript for dynamic content loading and has bot protection.

Features:
- NSFW content support
- WordPress/Madara theme structure
- JavaScript-based image loading
- Anti-bot protection
- CDN-based image serving
"""

import logging
import re
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .base import AgentCapability
from .javascript_provider import JavaScriptProvider

logger = logging.getLogger(__name__)


class HiperDexProvider(JavaScriptProvider):
    """HiperDEX provider with JavaScript and bot protection support."""

    def __init__(self):
        super().__init__(
            name="HiperDEX",
            url="https://hiperdex.com",
            supports_nsfw=True,
            selectors={
                "search_results": ".c-tabs-item__content .tab-thumb a",
                "manga_title": ".post-title h1, .manga-title h1",
                "manga_description": (
                    ".summary__content .description-summary p, .manga-excerpt p"
                ),
                "manga_cover": ".summary_image img, .manga-cover img",
                "manga_genres": ".genres-content a, .manga-genres a",
                "manga_status": ".post-status .summary-content, .manga-status",
                "chapters": ".wp-manga-chapter a, .listing-chapters_wrap a",
                "chapter_title": ".wp-manga-chapter a, .chapter-link",
                "pages": (
                    'img[id^="image-"], .wp-manga-chapter-img, .reading-content img'
                ),
                "page_image": (
                    'img[src*="mdg.hiperdex.com"], img[data-src*="mdg.hiperdex.com"]'
                ),
            },
            javascript_patterns={
                "chapter_data": r"var\s+chapter_data\s*=\s*({[^}]+})",
                "manga_data": r"var\s+manga_data\s*=\s*({[^}]+})",
                "image_urls": r"var\s+images\s*=\s*(\[[^\]]+\])",
                "page_data": r"var\s+page_data\s*=\s*({[^}]+})",
            },
        )

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return HiperDEX capabilities."""
        return [
            AgentCapability.SEARCH,
            AgentCapability.MANGA_DETAILS,
            AgentCapability.CHAPTERS,
            AgentCapability.PAGES,
            AgentCapability.DOWNLOAD_PAGE,
            AgentCapability.DOWNLOAD_COVER,
            AgentCapability.HEALTH_CHECK,
        ]

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """
        Search for manga on HiperDEX.

        Args:
            query: Search query
            page: Page number (default: 1)

        Returns:
            List of manga search results
        """
        search_url = f"{self.url}/?s={query}&post_type=wp-manga"
        if page > 1:
            search_url += f"&paged={page}"

        logger.info(f"Searching HiperDEX for '{query}' (page {page})")

        content = await self._make_request(search_url)
        if not content:
            logger.error(f"Failed to get search results for query: {query}")
            return []

        soup = BeautifulSoup(content, "html.parser")
        results = []

        # Find search result items
        search_items = soup.select(".c-tabs-item__content .tab-thumb")

        for item in search_items:
            try:
                # Get manga link
                link_elem = item.find("a")
                if not link_elem:
                    continue

                manga_url = urljoin(self.url, link_elem.get("href", ""))

                # Get title
                title_elem = item.find(".tab-thumb-title, .manga-title, h3, h4")
                title = (
                    title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                )

                # Get cover image
                img_elem = item.find("img")
                cover_url = None
                if img_elem:
                    cover_url = img_elem.get("src") or img_elem.get("data-src")
                    if cover_url:
                        cover_url = urljoin(self.url, cover_url)

                # Get description/summary
                desc_elem = item.find(".tab-summary, .manga-excerpt, .summary")
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                # Get latest chapter info
                latest_elem = item.find(".latest-chap, .chapter-item")
                latest_chapter = latest_elem.get_text(strip=True) if latest_elem else ""

                result = {
                    "title": title,
                    "url": manga_url,
                    "cover_url": cover_url,
                    "description": (
                        description[:200] + "..."
                        if len(description) > 200
                        else description
                    ),
                    "latest_chapter": latest_chapter,
                    "provider": self.name,
                    "nsfw": True,  # HiperDEX is NSFW-focused
                }

                results.append(result)
                logger.debug(f"Found manga: {title}")

            except Exception as e:
                logger.warning(f"Error parsing search result: {e}")
                continue

        logger.info(f"Found {len(results)} manga for query '{query}'")
        # Return tuple format: (results, total, has_more)
        has_more = len(results) >= limit  # Simple heuristic
        return results, len(results), has_more

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """
        Get detailed manga information.

        Args:
            manga_id: ID or URL of the manga page

        Returns:
            Manga details dictionary
        """
        # For HiperDEX, manga_id is actually the full URL
        manga_url = (
            manga_id if manga_id.startswith("http") else f"{self.url}/manga/{manga_id}"
        )
        logger.info(f"Getting manga details from: {manga_url}")

        content = await self._make_request(manga_url)
        if not content:
            logger.error(f"Failed to get manga details from: {manga_url}")
            return {}

        soup = BeautifulSoup(content, "html.parser")

        try:
            # Extract JavaScript data if available
            js_data = self._extract_javascript_data(content, self.javascript_patterns)

            # Get title
            title_elem = soup.select_one(self.selectors["manga_title"])
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

            # Get description
            desc_elem = soup.select_one(self.selectors["manga_description"])
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Get cover image
            cover_elem = soup.select_one(self.selectors["manga_cover"])
            cover_url = None
            if cover_elem:
                cover_url = cover_elem.get("src") or cover_elem.get("data-src")
                if cover_url:
                    cover_url = urljoin(self.url, cover_url)

            # Get genres
            genre_elems = soup.select(self.selectors["manga_genres"])
            genres = [elem.get_text(strip=True) for elem in genre_elems]

            # Get status
            status_elem = soup.select_one(self.selectors["manga_status"])
            status = status_elem.get_text(strip=True) if status_elem else "Unknown"

            # Get author/artist info
            author_elem = soup.select_one(".author-content, .manga-author")
            author = author_elem.get_text(strip=True) if author_elem else ""

            # Get rating
            rating_elem = soup.select_one(".post-rating, .manga-rating")
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r"(\d+\.?\d*)", rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))

            manga_details = {
                "title": title,
                "url": manga_url,
                "description": description,
                "cover_url": cover_url,
                "genres": genres,
                "status": status,
                "author": author,
                "rating": rating,
                "provider": self.name,
                "nsfw": True,
                "javascript_data": js_data,
            }

            logger.info(f"Successfully extracted details for: {title}")
            return manga_details

        except Exception as e:
            logger.error(f"Error extracting manga details from {manga_url}: {e}")
            return {}

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """
        Get chapter list for a manga.

        Args:
            manga_id: ID or URL of the manga page
            page: Page number (not used for HiperDEX)
            limit: Limit of chapters (not used for HiperDEX)

        Returns:
            Tuple of (chapters, total, has_more)
        """
        # For HiperDEX, manga_id is actually the full URL
        manga_url = (
            manga_id if manga_id.startswith("http") else f"{self.url}/manga/{manga_id}"
        )
        logger.info(f"Getting chapters from: {manga_url}")

        content = await self._make_request(manga_url)
        if not content:
            logger.error(f"Failed to get chapters from: {manga_url}")
            return [], 0, False

        soup = BeautifulSoup(content, "html.parser")
        chapters = []

        try:
            # Find chapter links
            chapter_elems = soup.select(self.selectors["chapters"])

            for elem in chapter_elems:
                try:
                    chapter_url = urljoin(self.url, elem.get("href", ""))
                    chapter_title = elem.get_text(strip=True)

                    # Extract chapter number
                    chapter_num_match = re.search(
                        r"chapter[- ]?(\d+)", chapter_title.lower()
                    )
                    chapter_number = (
                        int(chapter_num_match.group(1)) if chapter_num_match else 0
                    )

                    # Get upload date if available
                    date_elem = elem.find_parent().find(
                        ".chapter-release-date, .post-on"
                    )
                    upload_date = date_elem.get_text(strip=True) if date_elem else ""

                    chapter = {
                        "title": chapter_title,
                        "url": chapter_url,
                        "chapter_number": chapter_number,
                        "upload_date": upload_date,
                        "provider": self.name,
                    }

                    chapters.append(chapter)

                except Exception as e:
                    logger.warning(f"Error parsing chapter: {e}")
                    continue

            # Sort chapters by number (descending - newest first)
            chapters.sort(key=lambda x: x["chapter_number"], reverse=True)

            logger.info(f"Found {len(chapters)} chapters")
            return chapters, len(chapters), False  # HiperDEX loads all chapters at once

        except Exception as e:
            logger.error(f"Error extracting chapters from {manga_url}: {e}")
            return [], 0, False

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """
        Get page image URLs for a chapter.

        Args:
            manga_id: ID of the manga (not used for HiperDEX)
            chapter_id: ID or URL of the chapter page

        Returns:
            List of image URLs
        """
        # For HiperDEX, chapter_id is actually the full URL
        chapter_url = (
            chapter_id
            if chapter_id.startswith("http")
            else f"{self.url}/manga/{manga_id}/{chapter_id}"
        )
        logger.info(f"Getting pages from: {chapter_url}")

        content = await self._make_request(chapter_url)
        if not content:
            logger.error(f"Failed to get pages from: {chapter_url}")
            return []

        soup = BeautifulSoup(content, "html.parser")
        page_urls = []

        try:
            # Extract JavaScript image data first
            js_data = self._extract_javascript_data(content, self.javascript_patterns)

            if "image_urls" in js_data:
                # Use JavaScript-extracted URLs if available
                page_urls.extend(js_data["image_urls"])

            # Find page images in HTML
            img_elems = soup.select(self.selectors["pages"])

            for img in img_elems:
                img_url = img.get("src") or img.get("data-src")
                if img_url:
                    # Ensure full URL
                    if not img_url.startswith("http"):
                        img_url = urljoin(self.url, img_url)

                    # Filter for HiperDEX CDN images - use proper URL parsing
                    # to prevent URL injection attacks
                    try:
                        parsed = urlparse(img_url)
                        # Check if hostname ends with hiperdex.com (includes subdomains)
                        if parsed.hostname and (
                            parsed.hostname == "hiperdex.com"
                            or parsed.hostname.endswith(".hiperdex.com")
                        ):
                            page_urls.append(img_url)
                    except Exception:
                        # Skip malformed URLs
                        continue

            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in page_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)

            logger.info(f"Found {len(unique_urls)} pages")
            return unique_urls

        except Exception as e:
            logger.error(f"Error extracting pages from {chapter_url}: {e}")
            return []

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover."""
        try:
            # Get manga details to find cover URL
            details = await self.get_manga_details(manga_id)
            cover_url = details.get("cover_url")

            if not cover_url:
                logger.warning(f"No cover URL found for manga {manga_id}")
                return b""

            # Download the cover image
            content = await self._make_request(cover_url)
            if content:
                return content.encode("utf-8")
            return b""

        except Exception as e:
            logger.error(f"Error downloading cover for {manga_id}: {e}")
            return b""
