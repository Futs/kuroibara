import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.providers.base import (
    AntiBotError,
    BaseProvider,
    ContentError,
    NetworkError,
    ProviderError,
    RateLimitError,
)
from app.models.manga import MangaStatus, MangaType
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class MangaDexProvider(BaseProvider):
    """MangaDex provider with improved rate limiting and error handling."""

    def __init__(self, **kwargs):
        self._base_url = "https://api.mangadex.org"
        self._timeout = httpx.Timeout(30.0)
        self._data_saver = kwargs.get(
            "data_saver", False
        )  # Option for compressed images
        self._max_retries = 4
        self._retry_delay = 1.0  # 1 second base delay (more conservative)
        self._request_delay = 0.5  # Minimum delay between requests
        self._provider_id = "mangadex"  # Provider ID for API calls
        self._last_rate_limit = None  # Track last rate limit time
        self._rate_limit_reset = None  # Track when rate limit resets

    @property
    def name(self) -> str:
        return "MangaDex"

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def url(self) -> str:
        return self._base_url

    @property
    def supports_nsfw(self) -> bool:
        return True

    def get_rate_limit_status(self) -> dict:
        """Get current rate limit status."""
        import time

        if not self._last_rate_limit:
            return {
                "is_rate_limited": False,
                "reset_time": None,
                "seconds_remaining": 0,
            }

        current_time = time.time()
        if self._rate_limit_reset and current_time < self._rate_limit_reset:
            return {
                "is_rate_limited": True,
                "reset_time": self._rate_limit_reset,
                "seconds_remaining": int(self._rate_limit_reset - current_time),
            }
        else:
            # Rate limit has expired
            self._last_rate_limit = None
            self._rate_limit_reset = None
            return {
                "is_rate_limited": False,
                "reset_time": None,
                "seconds_remaining": 0,
            }

    async def _make_request_with_retry(
        self, client: httpx.AsyncClient, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Make HTTP request with rate limiting and retry logic."""
        # Add delay before each request to respect rate limits
        await asyncio.sleep(self._request_delay)

        for attempt in range(self._max_retries):
            try:
                response = await client.request(
                    method, url, timeout=self._timeout, **kwargs
                )

                # Handle rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    self._last_rate_limit = time.time()

                    # Get retry-after header or use default
                    retry_after = response.headers.get("X-Ratelimit-Retry-After")
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                            self._rate_limit_reset = time.time() + wait_time
                            logger.warning(
                                f"Rate limited. Waiting {wait_time} seconds..."
                            )
                            await asyncio.sleep(wait_time)
                        except ValueError:
                            # Fallback to longer wait for rate limits
                            wait_time = 60  # Wait 1 minute on rate limit
                            self._rate_limit_reset = time.time() + wait_time
                            logger.warning(
                                f"Rate limited. Waiting {wait_time} seconds..."
                            )
                            await asyncio.sleep(wait_time)
                    else:
                        # Wait longer for rate limits
                        wait_time = 60  # Wait 1 minute on rate limit
                        self._rate_limit_reset = time.time() + wait_time
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    continue

                # For other errors, raise immediately
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    continue  # Retry on rate limit
                raise  # Re-raise other HTTP errors
            except Exception as e:
                if attempt == self._max_retries - 1:
                    logger.error(
                        f"Request failed after {self._max_retries} attempts: {e}"
                    )
                    raise
                # Wait before retry
                wait_time = self._retry_delay * (2**attempt)
                await asyncio.sleep(wait_time)

        raise Exception(f"Request failed after {self._max_retries} attempts")

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MangaDex."""
        # Calculate offset
        offset = (page - 1) * limit

        # Build query parameters
        params = {
            "title": query,
            "limit": limit,
            "offset": offset,
            "includes[]": ["cover_art", "author", "artist", "tag"],
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
        }

        # Make request with retry logic
        async with httpx.AsyncClient() as client:
            response = await self._make_request_with_retry(
                client, "GET", f"{self.url}/manga", params=params
            )
            data = response.json()

            # Parse results
            results = []
            for manga in data["data"]:
                # Get manga attributes
                attributes = manga["attributes"]

                # Get cover
                cover_url = None
                for relationship in manga["relationships"]:
                    if relationship["type"] == "cover_art":
                        cover_filename = relationship["attributes"]["fileName"]
                        cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover_filename}"
                        break

                # Get authors
                authors = []
                for relationship in manga["relationships"]:
                    if relationship["type"] in ["author", "artist"]:
                        if (
                            "attributes" in relationship
                            and "name" in relationship["attributes"]
                        ):
                            authors.append(relationship["attributes"]["name"])

                # Get genres
                genres = []
                if "tags" in attributes:
                    for tag in attributes["tags"]:
                        # MangaDex uses type "tag" for all tags, not "genre"
                        if (
                            tag["type"] == "tag"
                            and "attributes" in tag
                            and "name" in tag["attributes"]
                            and "en" in tag["attributes"]["name"]
                        ):
                            genres.append(tag["attributes"]["name"]["en"])

                # Determine manga type
                manga_type = MangaType.MANGA
                if "publicationDemographic" in attributes:
                    demographic = attributes["publicationDemographic"]
                    if demographic == "josei" or demographic == "shoujo":
                        manga_type = MangaType.MANGA
                    elif demographic == "seinen" or demographic == "shounen":
                        manga_type = MangaType.MANGA

                # Determine manga status
                manga_status = MangaStatus.UNKNOWN
                if "status" in attributes:
                    status = attributes["status"]
                    if status == "ongoing":
                        manga_status = MangaStatus.ONGOING
                    elif status == "completed":
                        manga_status = MangaStatus.COMPLETED
                    elif status == "hiatus":
                        manga_status = MangaStatus.HIATUS
                    elif status == "cancelled":
                        manga_status = MangaStatus.CANCELLED

                # Determine if manga is NSFW
                is_nsfw = False
                if "contentRating" in attributes:
                    content_rating = attributes["contentRating"]
                    if content_rating in ["erotica", "pornographic"]:
                        is_nsfw = True

                # Get title
                title = ""
                if "title" in attributes:
                    if "en" in attributes["title"]:
                        title = attributes["title"]["en"]
                    elif attributes["title"]:
                        # Get first available title
                        title = next(iter(attributes["title"].values()))

                # Get alternative titles
                alternative_titles = {}
                if "altTitles" in attributes:
                    for alt_title in attributes["altTitles"]:
                        for lang, title_text in alt_title.items():
                            alternative_titles[lang] = title_text

                # Get description
                description = ""
                if "description" in attributes:
                    if "en" in attributes["description"]:
                        description = attributes["description"]["en"]
                    elif attributes["description"]:
                        # Get first available description
                        description = next(iter(attributes["description"].values()))

                # Get year
                year = None
                if "year" in attributes:
                    year = attributes["year"]

                # Create search result
                result = SearchResult(
                    id=manga["id"],
                    title=title,
                    alternative_titles=alternative_titles,
                    description=description,
                    cover_image=cover_url,
                    type=manga_type,
                    status=manga_status,
                    year=year,
                    is_nsfw=is_nsfw,
                    genres=genres,
                    authors=authors,
                    provider=self.provider_id,
                    url=f"https://mangadex.org/title/{manga['id']}",
                )

                results.append(result)

            # Determine if there are more results
            total = data["total"]
            has_next = (offset + limit) < total

            return results, total, has_next

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get details for a manga on MangaDex."""
        # Make request with retry logic
        async with httpx.AsyncClient() as client:
            response = await self._make_request_with_retry(
                client,
                "GET",
                f"{self.url}/manga/{manga_id}",
                params={"includes[]": ["cover_art", "author", "artist", "tag"]},
            )
            data = response.json()

            # Parse manga details
            manga = data["data"]
            attributes = manga["attributes"]

            # Get cover
            cover_url = None
            for relationship in manga["relationships"]:
                if relationship["type"] == "cover_art":
                    cover_filename = relationship["attributes"]["fileName"]
                    cover_url = f"https://uploads.mangadex.org/covers/{manga['id']}/{cover_filename}"
                    break

            # Get authors
            authors = []
            for relationship in manga["relationships"]:
                if relationship["type"] in ["author", "artist"]:
                    if (
                        "attributes" in relationship
                        and "name" in relationship["attributes"]
                    ):
                        authors.append(relationship["attributes"]["name"])

            # Get genres
            genres = []
            if "tags" in attributes:
                for tag in attributes["tags"]:
                    # MangaDex uses type "tag" for all tags, not "genre"
                    if (
                        tag["type"] == "tag"
                        and "attributes" in tag
                        and "name" in tag["attributes"]
                        and "en" in tag["attributes"]["name"]
                    ):
                        genres.append(tag["attributes"]["name"]["en"])

            # Determine manga type
            manga_type = MangaType.MANGA
            if "publicationDemographic" in attributes:
                demographic = attributes["publicationDemographic"]
                if demographic == "josei" or demographic == "shoujo":
                    manga_type = MangaType.MANGA
                elif demographic == "seinen" or demographic == "shounen":
                    manga_type = MangaType.MANGA

            # Determine manga status
            manga_status = MangaStatus.UNKNOWN
            if "status" in attributes:
                status = attributes["status"]
                if status == "ongoing":
                    manga_status = MangaStatus.ONGOING
                elif status == "completed":
                    manga_status = MangaStatus.COMPLETED
                elif status == "hiatus":
                    manga_status = MangaStatus.HIATUS
                elif status == "cancelled":
                    manga_status = MangaStatus.CANCELLED

            # Determine if manga is NSFW
            is_nsfw = False
            if "contentRating" in attributes:
                content_rating = attributes["contentRating"]
                if content_rating in ["erotica", "pornographic"]:
                    is_nsfw = True

            # Get title
            title = ""
            if "title" in attributes:
                if "en" in attributes["title"]:
                    title = attributes["title"]["en"]
                elif attributes["title"]:
                    # Get first available title
                    title = next(iter(attributes["title"].values()))

            # Get alternative titles
            alternative_titles = {}
            if "altTitles" in attributes:
                for alt_title in attributes["altTitles"]:
                    for lang, title_text in alt_title.items():
                        alternative_titles[lang] = title_text

            # Get description
            description = ""
            if "description" in attributes:
                if "en" in attributes["description"]:
                    description = attributes["description"]["en"]
                elif attributes["description"]:
                    # Get first available description
                    description = next(iter(attributes["description"].values()))

            # Get year
            year = None
            if "year" in attributes:
                year = attributes["year"]

            # Return manga details
            return {
                "id": manga["id"],
                "title": title,
                "alternative_titles": alternative_titles,
                "description": description,
                "cover_image": cover_url,
                "type": manga_type,
                "status": manga_status,
                "year": year,
                "is_nsfw": is_nsfw,
                "genres": genres,
                "authors": authors,
                "provider": self.name,
                "url": f"https://mangadex.org/title/{manga['id']}",
            }

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga on MangaDex."""
        # Calculate offset
        offset = (page - 1) * limit

        # Build query parameters
        params = {
            "limit": limit,
            "offset": offset,
            "translatedLanguage[]": ["en"],
            "order[chapter]": "asc",
        }

        # Make request with retry logic
        async with httpx.AsyncClient() as client:
            response = await self._make_request_with_retry(
                client, "GET", f"{self.url}/manga/{manga_id}/feed", params=params
            )
            data = response.json()

            # Parse chapters
            chapters = []
            for chapter in data["data"]:
                attributes = chapter["attributes"]

                # Get chapter number
                chapter_number = attributes.get("chapter", "")

                # Get chapter title
                chapter_title = attributes.get("title", "")

                # Get volume
                volume = attributes.get("volume", "")

                # Get language
                language = attributes.get("translatedLanguage", "en")

                # Get dates
                publish_at = attributes.get("publishAt")
                readable_at = attributes.get("readableAt")

                # Create chapter
                chapters.append(
                    {
                        "id": chapter["id"],
                        "title": chapter_title,
                        "number": chapter_number,
                        "volume": volume,
                        "language": language,
                        "pages_count": attributes.get("pages", 0),
                        "manga_id": manga_id,
                        "publish_at": publish_at,
                        "readable_at": readable_at,
                        "source": "MangaDex",
                    }
                )

            # Determine if there are more chapters
            total = data["total"]
            has_next = (offset + limit) < total

            return chapters, total, has_next

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter on MangaDex with improved error handling."""
        try:
            async with httpx.AsyncClient() as client:
                # First check if this is an external chapter
                external_url = await self._check_external_chapter(client, chapter_id)
                if external_url:
                    logger.warning(
                        f"Chapter {chapter_id} is external-only: {external_url}"
                    )
                    raise ValueError(
                        f"Chapter is external-only and redirects to: {external_url}"
                    )

                # Make request to get chapter data with retry logic
                logger.info(f"Fetching at-home server data for chapter {chapter_id}")
                response = await self._make_request_with_retry(
                    client, "GET", f"{self.url}/at-home/server/{chapter_id}"
                )
                data = response.json()

                # Validate response structure
                if "result" in data and data["result"] != "ok":
                    error_msg = data.get("errors", [{}])[0].get(
                        "detail", "Unknown error"
                    )
                    logger.error(
                        f"MangaDex API error for chapter {chapter_id}: {error_msg}"
                    )
                    raise ValueError(f"MangaDex API error: {error_msg}")

                # Get base URL
                base_url = data.get("baseUrl")
                if not base_url:
                    logger.error(f"No baseUrl in response for chapter {chapter_id}")
                    raise ValueError("No baseUrl in MangaDex response")

                # Get chapter data
                chapter_data = data.get("chapter", {})
                chapter_hash = chapter_data.get("hash")
                if not chapter_hash:
                    logger.error(
                        f"No chapter hash in response for chapter {chapter_id}"
                    )
                    raise ValueError("No chapter hash in MangaDex response")

                # Get page filenames - use data saver if configured
                if self._data_saver and "dataSaver" in chapter_data:
                    page_filenames = chapter_data["dataSaver"]
                    quality = "data-saver"
                    logger.info(f"Using data saver quality for chapter {chapter_id}")
                else:
                    page_filenames = chapter_data.get("data", [])
                    quality = "data"

                # Check if chapter has no pages (external-only)
                if not page_filenames:
                    logger.warning(
                        f"Chapter {chapter_id} has 0 pages - trying fallback servers"
                    )
                    return await self._try_fallback_servers(
                        client, chapter_hash, chapter_id
                    )

                # Build page URLs
                page_urls = []
                for i, filename in enumerate(page_filenames):
                    page_url = f"{base_url}/{quality}/{chapter_hash}/{filename}"
                    page_urls.append(page_url)

                logger.info(
                    f"Successfully extracted {len(page_urls)} pages for chapter {chapter_id}"
                )
                return page_urls

        except Exception as e:
            logger.error(f"Error getting pages for chapter {chapter_id}: {e}")
            raise

    async def _check_external_chapter(
        self, client: httpx.AsyncClient, chapter_id: str
    ) -> str:
        """Check if a chapter is external-only and return the external URL if so."""
        try:
            response = await self._make_request_with_retry(
                client, "GET", f"{self.url}/chapter/{chapter_id}"
            )
            data = response.json()

            chapter_data = data.get("data", {})
            attributes = chapter_data.get("attributes", {})
            external_url = attributes.get("externalUrl")

            return external_url
        except Exception as e:
            logger.debug(f"Could not check external URL for chapter {chapter_id}: {e}")
            return None

    async def _try_fallback_servers(
        self, client: httpx.AsyncClient, chapter_hash: str, chapter_id: str
    ) -> List[str]:
        """Try fallback servers when official at-home server has no pages (like HakuNeko does)."""
        fallback_servers = [
            "https://uploads.mangadex.org/data/",  # MangaDx upload server
            "https://cache.ayaya.red/mdah/data/",  # Third-party cache server
        ]

        logger.info(f"Trying fallback servers for chapter {chapter_id}")

        for server in fallback_servers:
            try:
                # Try to access the chapter directory on fallback server
                test_url = f"{server}{chapter_hash}/"
                response = await client.get(test_url, timeout=10)

                if response.status_code == 200:
                    logger.info(f"Fallback server accessible: {server}")
                    # For now, return empty list since we don't have page filenames
                    # In a full implementation, we'd need to parse the directory listing
                    # or get page filenames from another source
                    logger.warning(
                        "Fallback server found but page enumeration not implemented"
                    )
                    return []

            except Exception as e:
                logger.debug(f"Fallback server {server} failed: {e}")
                continue

        logger.warning(f"All fallback servers failed for chapter {chapter_id}")
        return []

    async def download_page(
        self, page_url: str, referer: Optional[str] = None
    ) -> bytes:
        """
        Download a page from MangaDex with retry logic.

        Args:
            page_url: The URL of the page to download
            referer: Optional referer URL (not used for MangaDex API)

        Returns:
            The page content as bytes
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await self._make_request_with_retry(client, "GET", page_url)
                return response.content
        except Exception as e:
            logger.error(f"Error downloading page {page_url}: {e}")
            raise

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover from MangaDex with retry logic."""
        try:
            # Get manga details to get cover URL
            manga_details = await self.get_manga_details(manga_id)
            cover_url = manga_details["cover_image"]

            if not cover_url:
                raise ValueError(f"No cover image found for manga {manga_id}")

            # Download cover
            async with httpx.AsyncClient() as client:
                response = await self._make_request_with_retry(client, "GET", cover_url)
                return response.content
        except Exception as e:
            logger.error(f"Error downloading cover for manga {manga_id}: {e}")
            raise
