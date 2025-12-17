"""
Enhanced Generic Provider with Cloudflare bypass support.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
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
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
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
            "status": [
                ".status",
                ".manga-status",
                ".series-status",
                "[class*='status']",
                ".info .status",
                ".details .status",
                ".post-status",
                ".mg_status",
                ".summary-content .status",
                ".meta-item .status",
                ".manga-info .status",
                ".series-info .status",
                ".post-content_item:contains('Status')",
                ".summary-heading:contains('Status') + .summary-content",
                ".fmed b:contains('Status')",
                ".tsinfo .imptdt:contains('Status')",
                ".infotable tr:contains('Status') td",
                ".manga-info-table tr:contains('Status') td",
            ],
            "genres": [
                ".genres",
                ".tags",
                ".categories",
                ".genre",
                ".tag",
                ".category",
                "[class*='genre']",
                "[class*='tag']",
                "[class*='category']",
                ".manga-genres",
                ".series-genres",
                ".post-content_item:contains('Genre')",
                ".summary-heading:contains('Genre') + .summary-content",
                ".fmed:contains('Genre')",
                ".tsinfo .imptdt:contains('Genre')",
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

    def _clean_title(self, title: str) -> str:
        """Clean manga title by removing common badges and indicators."""
        if not title:
            return title

        # Remove common badges and indicators
        badges_to_remove = [
            "NEW",
            "new",
            "UPDATED",
            "updated",
            "HOT",
            "hot",
            "COMPLETE",
            "complete",
            "ONGOING",
            "ongoing",
            "LATEST",
            "latest",
            "POPULAR",
            "popular",
        ]

        cleaned_title = title
        for badge in badges_to_remove:
            # Remove badge if it appears at the end
            if cleaned_title.endswith(badge):
                cleaned_title = cleaned_title[: -len(badge)].strip()
            # Remove badge if it appears at the start
            if cleaned_title.startswith(badge):
                cleaned_title = cleaned_title[len(badge) :].strip()

        return cleaned_title

    def _detect_nsfw_from_content(
        self, title: str, genres: List[str], description: str = ""
    ) -> bool:
        """Detect if manga is NSFW based on title, genres, and description."""
        if not self._supports_nsfw:
            logger.debug(
                f"Provider {self.name} doesn't support NSFW, returning False for '{title}'"
            )
            return False

        # Providers that are primarily NSFW - mark all content as NSFW
        nsfw_only_providers = ["MangaDNA", "Manga18FX"]
        if self.name in nsfw_only_providers:
            logger.debug(
                f"Provider {self.name} is NSFW-only, marking '{title}' as NSFW"
            )
            return True

        # NSFW keywords to look for (comprehensive list)
        # Note: "mature" is NOT NSFW - it's for teen+ content with violence/action
        nsfw_keywords = {
            "hentai",
            "ecchi",
            "adult",
            "smut",
            "pornographic",
            "erotic",
            "sexual",
            "xxx",
            "18+",
            "nsfw",
            "r18",
            "r-18",
            "explicit",
            "uncensored",
            "doujin",
            "doujinshi",
            "yaoi",
            "yuri",
            "shounen-ai",
            "shoujo-ai",
            "bl",
            "gl",
            "lemon",
            "lime",
            "hardcore",
            "softcore",
            "nudity",
            "sex",
            "rape",
            "incest",
            "netorare",
            "ntr",
            "ahegao",
            "milf",
            "loli",
            "shota",
            "futanari",
            "futa",
            "tentacle",
            "monster",
            "bdsm",
            "femdom",
            "maledom",
            "gangbang",
            "orgy",
            "threesome",
            "creampie",
            "cumshot",
            "blowjob",
            "handjob",
            "footjob",
            "titjob",
            "anal",
            "oral",
            "vaginal",
            "masturbation",
            "virgin",
            "defloration",
            "impregnation",
            "pregnant",
            "lactation",
            "breast",
            "oppai",
            "big breasts",
            "huge breasts",
            "small breasts",
            "flat chest",
            "panties",
            "underwear",
            "lingerie",
            "swimsuit",
            "bikini",
            "naked",
            "nude",
            "topless",
            "bottomless",
            "upskirt",
            "pantyshot",
            "cameltoe",
            "cleavage",
            "nipples",
            "areola",
            "pussy",
            "vagina",
            "penis",
            "dick",
            "cock",
            "balls",
            "testicles",
            "semen",
            "cum",
            "orgasm",
            "climax",
            "moan",
            "panting",
            "aroused",
            "horny",
            "lust",
            "desire",
            "seduction",
            "temptation",
            "forbidden",
            "taboo",
            "kinky",
            "pervert",
            "perverted",
            "lewd",
            "dirty",
            "naughty",
            "slutty",
            "whore",
            "bitch",
            "slut",
        }

        # Check title - use word boundaries for more accurate matching
        title_lower = title.lower()
        title_words = set(title_lower.split())

        # Direct keyword matches in title
        for keyword in nsfw_keywords:
            if keyword in title_lower:
                # For single words, check if it's a complete word match
                if len(keyword.split()) == 1:
                    if keyword in title_words or keyword in title_lower:
                        logger.debug(
                            f"NSFW detected in title '{title}' (keyword: '{keyword}') for provider {self.name}"
                        )
                        return True
                else:
                    # For multi-word keywords, check substring
                    if keyword in title_lower:
                        logger.debug(
                            f"NSFW detected in title '{title}' (phrase: '{keyword}') for provider {self.name}"
                        )
                        return True

        # Check genres (be more specific about genre matching)
        genres_lower = [genre.lower() for genre in genres]
        for genre in genres_lower:
            genre_words = set(genre.split())
            for keyword in nsfw_keywords:
                if len(keyword.split()) == 1:
                    # Single word - check exact match or word boundary
                    if keyword == genre or keyword in genre_words:
                        logger.debug(
                            f"NSFW detected in genre '{genre}' (keyword: '{keyword}') "
                            f"for '{title}' from provider {self.name}"
                        )
                        return True
                else:
                    # Multi-word - check substring
                    if keyword in genre:
                        logger.debug(
                            f"NSFW detected in genre '{genre}' (phrase: '{keyword}') "
                            f"for '{title}' from provider {self.name}"
                        )
                        return True

        # Check description with context awareness
        if description:
            description_lower = description.lower()
            description_words = set(description_lower.split())

            # Count NSFW indicators
            nsfw_score = 0
            found_keywords = []

            for keyword in nsfw_keywords:
                if len(keyword.split()) == 1:
                    if keyword in description_words or keyword in description_lower:
                        nsfw_score += 1
                        found_keywords.append(keyword)
                else:
                    if keyword in description_lower:
                        nsfw_score += 2  # Multi-word phrases are stronger indicators
                        found_keywords.append(keyword)

            # If we find multiple NSFW indicators, it's likely NSFW
            if nsfw_score >= 2 or any(
                strong_keyword in found_keywords
                for strong_keyword in [
                    "hentai",
                    "pornographic",
                    "explicit",
                    "xxx",
                    "18+",
                    "adult",
                    "nsfw",
                ]
            ):
                logger.debug(
                    f"NSFW detected in description for '{title}' "
                    f"(score: {nsfw_score}, keywords: {found_keywords}) "
                    f"from provider {self.name}"
                )
                return True

        logger.debug(
            f"No NSFW detected for '{title}' from provider {self.name} - genres: {genres}"
        )
        return False

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
                        f"Found {len(items)} items with selector '{selector}' "
                        f"for {self.name}"
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
                    title = "Unknown Title"
                    if title_element:
                        # Check if it's an img element with alt attribute
                        if title_element.name == "img" and title_element.get("alt"):
                            raw_title = title_element.get("alt")
                        else:
                            # Try to get text content first
                            raw_title = title_element.get_text(strip=True)

                            # If no text content, check for img[alt] within the element
                            if not raw_title:
                                img_elem = title_element.select_one("img[alt]")
                                if img_elem:
                                    raw_title = img_elem.get("alt", "")

                        # Clean up title by removing common badges and indicators
                        if raw_title:
                            title = self._clean_title(raw_title)

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
                        # For lazy loading sites like Toonily, prioritize data-src
                        # over src
                        data_src = cover_element.get("data-src")
                        src = cover_element.get("src")

                        # Use data-src if it exists and is not a placeholder
                        if (
                            data_src
                            and "dflazy" not in data_src
                            and "placeholder" not in data_src
                        ):
                            cover_url = data_src
                        else:
                            cover_url = src or data_src

                        if cover_url and cover_url.startswith("/"):
                            cover_url = urljoin(self._base_url, cover_url)

                    # Extract description
                    desc_element = self._find_element_with_selectors(
                        item, self._selectors["description"]
                    )
                    description = (
                        desc_element.get_text(strip=True) if desc_element else ""
                    )

                    # Extract status from search results
                    status_element = self._find_element_with_selectors(
                        item, self._selectors.get("status", [])
                    )
                    status = MangaStatus.UNKNOWN
                    if status_element and hasattr(status_element, "get_text"):
                        status_text = status_element.get_text(strip=True).lower()
                        # Map status text to enum values
                        if (
                            "ongoing" in status_text
                            or "publishing" in status_text
                            or "serializing" in status_text
                        ):
                            status = MangaStatus.ONGOING
                        elif (
                            "completed" in status_text
                            or "finished" in status_text
                            or "complete" in status_text
                        ):
                            status = MangaStatus.COMPLETED
                        elif "hiatus" in status_text or "on hold" in status_text:
                            status = MangaStatus.HIATUS
                        elif (
                            "cancelled" in status_text
                            or "dropped" in status_text
                            or "discontinued" in status_text
                        ):
                            status = MangaStatus.CANCELLED

                    # If status not found in search results, fetch from detail page
                    if status == MangaStatus.UNKNOWN and href and isinstance(href, str):
                        detail_url = urljoin(self._base_url, href)
                        status = await self._fetch_status_from_detail_page(detail_url)

                    # Detect NSFW based on content
                    is_nsfw = self._detect_nsfw_from_content(
                        title, [], description or ""
                    )

                    result = SearchResult(
                        id=manga_id,
                        title=title,
                        alternative_titles={},
                        description=description or "",
                        cover_image=str(cover_url) if cover_url else "",
                        type=MangaType.UNKNOWN,
                        status=status,
                        year=None,
                        is_nsfw=is_nsfw,
                        genres=[],
                        authors=[],
                        provider=self.name,
                        url=str(href) if href else "",
                        in_library=False,
                        extra=None,
                    )
                    results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing search result item: {e}")
                    continue

            return results, len(results), len(items) > limit

        except Exception as e:
            logger.error(f"Error searching on {self.name}: {e}")
            return [], 0, False

    async def get_available_manga(
        self, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Get available/popular manga from the provider."""
        try:
            # Try to get popular/latest manga from the homepage or popular page
            popular_urls = [
                f"{self._base_url}/popular",
                f"{self._base_url}/latest",
                f"{self._base_url}/trending",
                f"{self._base_url}/manga",
                f"{self._base_url}/series",
                f"{self._base_url}/",  # Homepage
            ]

            for url in popular_urls:
                try:
                    html = await self._make_request(url)
                    if not html:
                        continue

                    soup = BeautifulSoup(html, "html.parser")

                    # Find manga items using search selectors
                    items = None
                    for selector in self._selectors["search_items"]:
                        items = soup.select(selector)
                        if (
                            items and len(items) >= 3
                        ):  # Need at least 3 items to be useful
                            logger.info(
                                f"Found {len(items)} manga items on {url} with selector '{selector}'"
                            )
                            break

                    if items and len(items) >= 3:
                        # Parse the items using the same logic as search
                        results = []
                        for item in items[:limit]:
                            try:
                                # Extract title
                                title = self._extract_title(item)
                                if not title or title == "Unknown Title":
                                    continue

                                # Extract link and manga ID
                                href = self._extract_link(item)
                                if not href:
                                    continue

                                manga_id = self._extract_manga_id_from_url(href)
                                if not manga_id:
                                    continue

                                # Extract cover image
                                cover_url = self._extract_cover_image(item)

                                # Extract description
                                description = self._extract_description(item)

                                # Extract status (basic)
                                status = MangaStatus.UNKNOWN

                                # Detect NSFW based on content
                                is_nsfw = self._detect_nsfw_from_content(
                                    title, [], description or ""
                                )

                                result = SearchResult(
                                    id=manga_id,
                                    title=title,
                                    alternative_titles={},
                                    description=description or "",
                                    cover_image=str(cover_url) if cover_url else "",
                                    type=MangaType.UNKNOWN,
                                    status=status,
                                    year=None,
                                    is_nsfw=is_nsfw,
                                    genres=[],
                                    authors=[],
                                    provider=self.name,
                                    url=str(href) if href else "",
                                    in_library=False,
                                    extra=None,
                                )
                                results.append(result)

                            except Exception as e:
                                logger.debug(f"Error parsing manga item: {e}")
                                continue

                        if results:
                            total = len(results)
                            has_more = len(items) > limit
                            logger.info(
                                f"{self.name} get_available_manga returned {len(results)} results from {url}"
                            )
                            return results, total, has_more

                except Exception as e:
                    logger.debug(f"Error trying URL {url}: {e}")
                    continue

            # If no popular pages work, fallback to default implementation
            logger.info(
                f"{self.name} falling back to default get_available_manga implementation"
            )
            return await super().get_available_manga(page, limit)

        except Exception as e:
            logger.error(f"Error getting available manga from {self.name}: {e}")
            return await super().get_available_manga(page, limit)

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
            title = "Unknown Title"
            if title_element and hasattr(title_element, "get_text"):
                raw_title = title_element.get_text(strip=True)
                # Clean up title by removing common badges and indicators
                title = self._clean_title(raw_title)

            # Extract description
            desc_element = self._find_element_with_selectors(
                soup, self._selectors["description"]
            )
            description = desc_element.get_text(strip=True) if desc_element else ""

            # Extract status
            status_element = self._find_element_with_selectors(
                soup, self._selectors.get("status", [])
            )
            status = "unknown"
            if status_element:
                status_text = status_element.get_text(strip=True).lower()
                # Map status text to proper values (handle formats like "StatusOnGoing")
                if (
                    "ongoing" in status_text
                    or "publishing" in status_text
                    or "serializing" in status_text
                ):
                    status = "ongoing"
                elif (
                    "completed" in status_text
                    or "finished" in status_text
                    or "complete" in status_text
                ):
                    status = "completed"
                elif "hiatus" in status_text or "on hold" in status_text:
                    status = "hiatus"
                elif (
                    "cancelled" in status_text
                    or "dropped" in status_text
                    or "discontinued" in status_text
                ):
                    status = "cancelled"

            # Extract cover
            cover_element = self._find_element_with_selectors(
                soup, self._selectors["cover"]
            )
            cover_url = None
            if cover_element:
                # For lazy loading sites like Toonily, prioritize data-src over src
                data_src = cover_element.get("data-src")
                src = cover_element.get("src")

                # Use data-src if it exists and is not a placeholder
                if (
                    data_src
                    and "dflazy" not in data_src
                    and "placeholder" not in data_src
                ):
                    cover_url = data_src
                else:
                    cover_url = src or data_src

                if cover_url and cover_url.startswith("/"):
                    cover_url = urljoin(self._base_url, cover_url)

            # Extract genres/tags
            genres = self._extract_genres(soup)

            # Extract authors
            authors = self._extract_authors(soup)

            # Detect NSFW based on content
            is_nsfw = self._detect_nsfw_from_content(title, genres, description)

            return {
                "id": manga_id,
                "title": title,
                "description": description,
                "cover_image": cover_url,
                "provider": self.name,
                "url": manga_url,
                "type": "manga",
                "status": status,
                "is_nsfw": is_nsfw,
                "genres": genres,
                "authors": authors,
            }

        except Exception as e:
            logger.error(f"Error getting manga details for {manga_id}: {e}")
            return {}

    def _extract_genres(self, soup: BeautifulSoup) -> List[str]:
        """Extract genres/tags from the manga page."""
        genres = []

        # Try different selectors for genres/tags
        genre_selectors = self._selectors.get("genres", []) + self._selectors.get(
            "tags", []
        )
        if not genre_selectors:
            # Default selectors for common genre/tag patterns
            genre_selectors = [
                ".genres a",
                ".genre a",
                ".tags a",
                ".tag a",
                ".wp-manga-tags-list a",
                ".manga-tags a",
                ".post-content_item .summary-content a",
                ".summary-content a[rel='tag']",
                ".genre-list a",
                ".tag-list a",
                "[class*='genre'] a",
                "[class*='tag'] a",
                ".categories a",
                ".category a",
            ]

        for selector in genre_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    genre = element.get_text(strip=True)
                    if genre and genre not in genres and len(genre) > 1:
                        genres.append(genre)
                if genres:  # If we found genres, stop trying other selectors
                    break
            except Exception:
                continue

        return genres[:10]  # Limit to 10 genres to avoid clutter

    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract authors from the manga page."""
        authors = []

        # Try different selectors for authors
        author_selectors = self._selectors.get("authors", [])
        if not author_selectors:
            # Default selectors for common author patterns
            author_selectors = [
                ".author a",
                ".authors a",
                ".manga-author a",
                ".post-content_item .summary-content a",
                ".summary-content .author a",
                ".artist a",
                ".writer a",
                "[class*='author'] a",
                "[class*='artist'] a",
            ]

        for selector in author_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    author = element.get_text(strip=True)
                    if author and author not in authors and len(author) > 1:
                        authors.append(author)
                if authors:  # If we found authors, stop trying other selectors
                    break
            except Exception:
                continue

        return authors[:5]  # Limit to 5 authors

    def _extract_chapter_number(self, title: str, url: str) -> float:
        """Extract chapter number from title or URL."""
        import re

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
            r"/chapter-(\d+(?:\.\d+)?)",
            r"/ch-(\d+(?:\.\d+)?)",
            r"/c(\d+(?:\.\d+)?)",
            r"/(\d+(?:\.\d+)?)/?$",
        ]

        for pattern in url_patterns:
            match = re.search(pattern, url.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return 0.0

    async def _fetch_status_from_detail_page(self, manga_url: str) -> MangaStatus:
        """Fetch status from manga detail page when not available in search results."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(manga_url, headers=self._headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Try to find status on detail page
                status_element = self._find_element_with_selectors(
                    soup, self._selectors.get("status", [])
                )

                if status_element and hasattr(status_element, "get_text"):
                    status_text = status_element.get_text(strip=True).lower()
                    # Map status text to enum values
                    if (
                        "ongoing" in status_text
                        or "publishing" in status_text
                        or "serializing" in status_text
                    ):
                        return MangaStatus.ONGOING
                    elif (
                        "completed" in status_text
                        or "finished" in status_text
                        or "complete" in status_text
                    ):
                        return MangaStatus.COMPLETED
                    elif "hiatus" in status_text or "on hold" in status_text:
                        return MangaStatus.HIATUS
                    elif (
                        "cancelled" in status_text
                        or "dropped" in status_text
                        or "discontinued" in status_text
                    ):
                        return MangaStatus.CANCELLED

                return MangaStatus.UNKNOWN

        except Exception as e:
            logger.warning(f"Failed to fetch status from detail page {manga_url}: {e}")
            return MangaStatus.UNKNOWN

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters with enhanced selector support."""
        try:
            manga_url = self._manga_url_pattern.format(manga_id=manga_id)
            html = await self._make_request(manga_url)

            if not html:
                return [], 0, False

            soup = BeautifulSoup(html, "html.parser")

            # Find chapter elements using multiple selectors
            chapter_elements = []
            chapter_selectors = self._selectors.get("chapters", [])

            # Default chapter selectors if none provided
            if not chapter_selectors:
                chapter_selectors = [
                    ".wp-manga-chapter a",
                    ".chapter-list a",
                    ".chapters a",
                    ".listing-chapters_wrap a",
                    ".version-chap a",
                    "li.wp-manga-chapter a",
                    ".chapter-item a",
                    "a[href*='chapter']",
                    ".chapter a",
                ]

            for selector in chapter_selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(
                            f"Found {len(elements)} chapters with selector '{selector}' for {self.name}"
                        )
                        chapter_elements = elements
                        break
                except Exception:
                    continue

            if not chapter_elements:
                logger.warning(f"No chapters found for {manga_id} on {self.name}")
                return [], 0, False

            # Parse chapter information
            chapters = []
            for element in chapter_elements:
                try:
                    # Extract chapter URL
                    chapter_url = element.get("href", "")
                    if not chapter_url:
                        continue

                    # Skip chapters with template variables or malformed URLs
                    if (
                        "{{" in chapter_url
                        or "}}" in chapter_url
                        or chapter_url.startswith("#")
                    ):
                        continue

                    # Make URL absolute
                    if chapter_url.startswith("/"):
                        chapter_url = urljoin(self._base_url, chapter_url)

                    # Extract chapter ID from URL
                    chapter_id = (
                        chapter_url.split("/")[-1] or chapter_url.split("/")[-2]
                    )
                    if not chapter_id:
                        continue

                    # Extract chapter title
                    chapter_title = element.get_text(strip=True)

                    # Skip chapters with template variables in title
                    if "{{" in chapter_title or "}}" in chapter_title:
                        continue

                    # Extract chapter number from title or URL
                    chapter_number = self._extract_chapter_number(
                        chapter_title, chapter_url
                    )

                    # Create chapter dict
                    chapter = {
                        "id": chapter_id,
                        "title": chapter_title,
                        "number": chapter_number,
                        "volume": None,
                        "language": "en",
                        "pages_count": 0,
                        "manga_id": manga_id,
                        "publish_at": None,
                        "readable_at": None,
                        "source": self.name,
                        "url": chapter_url,
                    }

                    chapters.append(chapter)

                except Exception as e:
                    logger.error(f"Error parsing chapter element: {e}")
                    continue

            # Apply pagination
            total = len(chapters)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_chapters = chapters[start_idx:end_idx]
            has_next = end_idx < total

            return paginated_chapters, total, has_next

        except Exception as e:
            logger.error(f"Error getting chapters for {manga_id}: {e}")
            return [], 0, False

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages with enhanced selector support."""
        try:
            # Build chapter URL
            # Check if chapter_id is already a full slug (contains manga_id)
            if manga_id in chapter_id and chapter_id.startswith(manga_id):
                # chapter_id is already a full slug like "manga-name-chapter-123"
                # Use it directly in the pattern
                chapter_url = f"{self._base_url}/{chapter_id}/"
            else:
                # chapter_id is just the chapter number, use the pattern
                chapter_url = self._chapter_url_pattern.format(
                    manga_id=manga_id, chapter_id=chapter_id
                )

            html = await self._make_request(chapter_url)
            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")

            # Find page images using multiple selectors
            page_images = []
            page_selectors = self._selectors.get("pages", [])

            # Default page selectors if none provided
            if not page_selectors:
                page_selectors = [
                    ".reading-content img",
                    ".page-break img",
                    ".wp-manga-chapter-img",
                    ".chapter-content img",
                    ".chapter-images img",
                    ".manga-page img",
                    ".page img",
                    "img[data-src*='chapter']",
                    "img[src*='chapter']",
                    ".reader img",
                ]

            for selector in page_selectors:
                try:
                    elements = soup.select(selector)
                    if elements:
                        logger.info(
                            f"Found {len(elements)} page images with selector '{selector}' for {self.name}"
                        )
                        page_images = elements
                        break
                except Exception:
                    continue

            if not page_images:
                logger.warning(
                    f"No page images found for {manga_id}/{chapter_id} on {self.name}"
                )
                return []

            # Extract page URLs
            page_urls = []
            for img in page_images:
                try:
                    # Priority: data-src > src (for lazy loading sites)
                    img_url = None

                    # Check data-src first (common for lazy loading)
                    data_src = img.get("data-src", "").strip()
                    if data_src and not any(
                        placeholder in data_src.lower()
                        for placeholder in [
                            "default.jpg",
                            "placeholder",
                            "loading",
                            "lazy",
                        ]
                    ):
                        img_url = data_src

                    # Fallback to src
                    if not img_url:
                        src = img.get("src", "").strip()
                        if src and not any(
                            placeholder in src.lower()
                            for placeholder in [
                                "default.jpg",
                                "placeholder",
                                "loading",
                                "lazy",
                            ]
                        ):
                            img_url = src

                    if img_url:
                        # Make URL absolute
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            img_url = urljoin(self._base_url, img_url)

                        # Validate URL
                        if (
                            img_url.startswith(("http://", "https://"))
                            and img_url not in page_urls
                        ):
                            page_urls.append(img_url)

                except Exception as e:
                    logger.error(f"Error processing page image: {e}")
                    continue

            logger.info(
                f"Extracted {len(page_urls)} page URLs for {manga_id}/{chapter_id} on {self.name}"
            )
            return page_urls

        except Exception as e:
            logger.error(f"Error getting pages for {manga_id}/{chapter_id}: {e}")
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
