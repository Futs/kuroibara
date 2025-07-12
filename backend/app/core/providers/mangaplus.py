import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class MangaPlusProvider(BaseProvider):
    """MangaPlus provider with improved error handling."""

    def __init__(self):
        # Note: The original API endpoint appears to be deprecated/broken
        # This provider is currently disabled until a working implementation is found
        self._api_working = False
        logger.warning("MangaPlus provider is currently disabled due to API issues")

    @property
    def name(self) -> str:
        return "MangaPlus"

    @property
    def url(self) -> str:
        # Keep the original URL for reference, but mark as non-functional
        return "https://jumpg-webapi.tokyo-cdn.com/api"

    @property
    def supports_nsfw(self) -> bool:
        return False

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MangaPlus."""
        if not self._api_working:
            logger.error(
                "MangaPlus API is currently not working. Provider is disabled."
            )
            return [], 0, False

        # Calculate offset
        offset = (page - 1) * limit

        try:
            # Make request to get all titles
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/title_list/all",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                    timeout=30.0,
                )

                # Check if request was successful
                if response.status_code == 404:
                    logger.error(
                        "MangaPlus API endpoint not found (404). The API may have changed."
                    )
                    self._api_working = False
                    return [], 0, False

                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"MangaPlus API HTTP error: {e.response.status_code}")
            if e.response.status_code == 404:
                self._api_working = False
            return [], 0, False
        except Exception as e:
            logger.error(f"MangaPlus API request failed: {e}")
            return [], 0, False

            # Filter titles by query
            all_titles = []
            if "success" in data and data["success"]:
                for title_group in data.get("titleGroups", []):
                    for title in title_group.get("titles", []):
                        title_name = title.get("name", "").lower()
                        if query.lower() in title_name:
                            all_titles.append(title)

            # Apply pagination
            total = len(all_titles)
            paginated_titles = all_titles[offset : offset + limit]
            has_next = (offset + limit) < total

            # Parse results
            results = []
            for title in paginated_titles:
                # Get manga ID
                manga_id = str(title.get("titleId", ""))

                # Get title
                title_name = title.get("name", "")

                # Get author
                author = title.get("author", "")

                # Get cover
                cover_url = title.get("portraitImageUrl", "")

                # Get description
                description = title.get("overview", "")

                # Determine manga status
                manga_status = MangaStatus.UNKNOWN
                if title.get("isCompleted", False):
                    manga_status = MangaStatus.COMPLETED
                else:
                    manga_status = MangaStatus.ONGOING

                # Create search result
                result = SearchResult(
                    id=manga_id,
                    title=title_name,
                    alternative_titles={},
                    description=description,
                    cover_image=cover_url,
                    type=MangaType.MANGA,
                    status=manga_status,
                    year=None,
                    is_nsfw=False,
                    genres=[],
                    authors=[author] if author else [],
                    provider=self.name,
                    url=f"https://mangaplus.shueisha.co.jp/titles/{manga_id}",
                )

                results.append(result)

            return results, total, has_next

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get details for a manga on MangaPlus."""
        if not self._api_working:
            logger.error(
                "MangaPlus API is currently not working. Provider is disabled."
            )
            return {}

        try:
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.url}/title_detail?title_id={manga_id}",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    },
                    timeout=30.0,
                )

                # Check if request was successful
                if response.status_code == 404:
                    logger.error(
                        "MangaPlus API endpoint not found (404). The API may have changed."
                    )
                    self._api_working = False
                    return {}

                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error(f"MangaPlus API request failed for manga {manga_id}: {e}")
            return {}

            # Parse manga details
            manga_details = {}
            if "success" in data and data["success"] and "titleDetail" in data:
                title_detail = data["titleDetail"]
                title = title_detail.get("title", {})

                # Get title
                title_name = title.get("name", "")

                # Get author
                author = title.get("author", "")

                # Get cover
                cover_url = title.get("portraitImageUrl", "")

                # Get description
                description = title.get("overview", "")

                # Determine manga status
                manga_status = MangaStatus.UNKNOWN
                if title.get("isCompleted", False):
                    manga_status = MangaStatus.COMPLETED
                else:
                    manga_status = MangaStatus.ONGOING

                # Return manga details
                manga_details = {
                    "id": manga_id,
                    "title": title_name,
                    "alternative_titles": {},
                    "description": description,
                    "cover_image": cover_url,
                    "type": MangaType.MANGA,
                    "status": manga_status,
                    "year": None,
                    "is_nsfw": False,
                    "genres": [],
                    "authors": [author] if author else [],
                    "provider": self.name,
                    "url": f"https://mangaplus.shueisha.co.jp/titles/{manga_id}",
                }

            return manga_details

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga on MangaPlus."""
        # Calculate offset
        offset = (page - 1) * limit

        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/title_detail?title_id={manga_id}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            )

            # Check if request was successful
            response.raise_for_status()
            data = response.json()

            # Parse chapters
            chapters = []
            if "success" in data and data["success"] and "titleDetail" in data:
                title_detail = data["titleDetail"]

                # Get chapters
                for chapter_list in title_detail.get("chapterList", []):
                    for chapter in chapter_list.get("chapters", []):
                        # Get chapter ID
                        chapter_id = str(chapter.get("chapterId", ""))

                        # Get chapter name
                        chapter_name = chapter.get("name", "")

                        # Get chapter number
                        chapter_number = chapter.get("number", "")

                        # Create chapter
                        chapters.append(
                            {
                                "id": chapter_id,
                                "title": chapter_name,
                                "number": chapter_number,
                                "volume": None,
                                "language": "en",
                                "pages_count": 0,  # We don't know the page count yet
                                "manga_id": manga_id,
                            }
                        )

            # Apply pagination
            total = len(chapters)
            paginated_chapters = chapters[offset : offset + limit]
            has_next = (offset + limit) < total

            return paginated_chapters, total, has_next

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter on MangaPlus."""
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/manga_viewer?chapter_id={chapter_id}&split=yes&img_quality=high",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            )

            # Check if request was successful
            response.raise_for_status()
            data = response.json()

            # Parse pages
            page_urls = []
            if "success" in data and data["success"] and "mangaViewer" in data:
                manga_viewer = data["mangaViewer"]

                # Get pages
                for page in manga_viewer.get("pages", []):
                    if "imageUrl" in page:
                        page_urls.append(page["imageUrl"])

            return page_urls

    async def download_page(self, page_url: str) -> bytes:
        """Download a page from MangaPlus."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                page_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": "https://mangaplus.shueisha.co.jp/",
                },
            )
            response.raise_for_status()
            return response.content

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover from MangaPlus."""
        # Get manga details to get cover URL
        manga_details = await self.get_manga_details(manga_id)
        cover_url = manga_details["cover_image"]

        # Download cover
        async with httpx.AsyncClient() as client:
            response = await client.get(
                cover_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": "https://mangaplus.shueisha.co.jp/",
                },
            )
            response.raise_for_status()
            return response.content
