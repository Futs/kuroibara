import logging
from typing import Any, Dict, List, Tuple

import httpx

from app.core.providers.base import BaseProvider
from app.models.manga import MangaStatus, MangaType
from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


class MangaDexProvider(BaseProvider):
    """MangaDex provider."""

    @property
    def name(self) -> str:
        return "MangaDex"

    @property
    def url(self) -> str:
        return "https://api.mangadex.org"

    @property
    def supports_nsfw(self) -> bool:
        return True

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

        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/manga",
                params=params,
            )

            # Check if request was successful
            response.raise_for_status()
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
                    provider=self.name,
                    url=f"https://mangadex.org/title/{manga['id']}",
                )

                results.append(result)

            # Determine if there are more results
            total = data["total"]
            has_next = (offset + limit) < total

            return results, total, has_next

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get details for a manga on MangaDex."""
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/manga/{manga_id}",
                params={"includes[]": ["cover_art", "author", "artist", "tag"]},
            )

            # Check if request was successful
            response.raise_for_status()
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
            "manga": manga_id,
            "limit": limit,
            "offset": offset,
            "translatedLanguage[]": ["en"],
            "order[chapter]": "asc",
        }

        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/chapter",
                params=params,
            )

            # Check if request was successful
            response.raise_for_status()
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
        """Get pages for a chapter on MangaDex."""
        async with httpx.AsyncClient() as client:
            # First check if this is an external chapter
            external_url = await self._check_external_chapter(client, chapter_id)
            if external_url:
                logger.warning(f"Chapter {chapter_id} is external-only: {external_url}")
                raise ValueError(
                    f"Chapter is external-only and redirects to: {external_url}"
                )

            # Make request to get chapter data
            response = await client.get(
                f"{self.url}/at-home/server/{chapter_id}",
            )

            # Check if request was successful
            response.raise_for_status()
            data = response.json()

            # Get base URL
            base_url = data["baseUrl"]

            # Get chapter hash
            chapter_hash = data["chapter"]["hash"]

            # Get page filenames
            page_filenames = data["chapter"]["data"]

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
            for filename in page_filenames:
                page_url = f"{base_url}/data/{chapter_hash}/{filename}"
                page_urls.append(page_url)

            return page_urls

    async def _check_external_chapter(
        self, client: httpx.AsyncClient, chapter_id: str
    ) -> str:
        """Check if a chapter is external-only and return the external URL if so."""
        try:
            response = await client.get(f"{self.url}/chapter/{chapter_id}")
            response.raise_for_status()
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
                        f"Fallback server found but page enumeration not implemented"
                    )
                    return []

            except Exception as e:
                logger.debug(f"Fallback server {server} failed: {e}")
                continue

        logger.warning(f"All fallback servers failed for chapter {chapter_id}")
        return []

    async def download_page(self, page_url: str) -> bytes:
        """Download a page from MangaDex."""
        async with httpx.AsyncClient() as client:
            response = await client.get(page_url)
            response.raise_for_status()
            return response.content

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover from MangaDex."""
        # Get manga details to get cover URL
        manga_details = await self.get_manga_details(manga_id)
        cover_url = manga_details["cover_image"]

        # Download cover
        async with httpx.AsyncClient() as client:
            response = await client.get(cover_url)
            response.raise_for_status()
            return response.content
