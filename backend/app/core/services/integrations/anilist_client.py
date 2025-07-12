"""Anilist API client for manga list integration."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import json
from urllib.parse import urlencode

from app.core.config import settings
from app.models.external_integration import IntegrationType
from app.schemas.external_integration import ExternalMangaData, ExternalMangaList
from .base_client import BaseIntegrationClient

logger = logging.getLogger(__name__)


class AnilistClient(BaseIntegrationClient):
    """Anilist API client for GraphQL integration."""

    BASE_URL = "https://graphql.anilist.co"
    AUTH_URL = "https://anilist.co/api/v2/oauth/token"

    def __init__(
        self, client_id: Optional[str] = None, client_secret: Optional[str] = None
    ):
        super().__init__(IntegrationType.ANILIST)
        # Use provided credentials or fall back to environment variables
        self.client_id = client_id or getattr(settings, "ANILIST_CLIENT_ID", None)
        self.client_secret = client_secret or getattr(
            settings, "ANILIST_CLIENT_SECRET", None
        )

    async def authenticate(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with Anilist using authorization code."""
        if not self.client_id or not self.client_secret:
            raise ValueError("Anilist client credentials not configured")

        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": auth_data["redirect_uri"],
            "code": auth_data["authorization_code"],
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.AUTH_URL, data=urlencode(token_data), headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(
                        f"Anilist auth failed - Status: {response.status}, Response: {error_text}"
                    )
                    self.logger.error(f"Request data: {token_data}")
                    raise Exception(f"Anilist authentication failed: {error_text}")

                data = await response.json()

                # Get user info
                user_info = await self.get_user_info(data["access_token"])

                return {
                    "access_token": data["access_token"],
                    "refresh_token": data.get("refresh_token"),
                    "expires_at": datetime.utcnow()
                    + timedelta(seconds=data.get("expires_in", 3600)),
                    "user_info": user_info,
                }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Anilist access token."""
        # Anilist tokens don't expire, so this is a no-op
        # But we can validate the token is still working
        return {"access_token": refresh_token, "refresh_token": refresh_token}

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Anilist."""
        query = """
        query {
            Viewer {
                id
                name
                avatar {
                    large
                }
                statistics {
                    manga {
                        count
                        chaptersRead
                        meanScore
                    }
                }
            }
        }
        """

        result = await self._make_graphql_request(access_token, query)
        viewer = result["data"]["Viewer"]

        return {
            "user_id": str(viewer["id"]),
            "username": viewer["name"],
            "avatar_url": viewer["avatar"]["large"] if viewer["avatar"] else None,
            "manga_count": viewer["statistics"]["manga"]["count"],
            "chapters_read": viewer["statistics"]["manga"]["chaptersRead"],
            "mean_score": viewer["statistics"]["manga"]["meanScore"],
        }

    async def get_manga_list(
        self,
        access_token: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ExternalMangaList:
        """Get user's manga list from Anilist."""
        # Map internal status to Anilist status
        anilist_status = None
        if status:
            status_map = {
                "reading": "CURRENT",
                "completed": "COMPLETED",
                "dropped": "DROPPED",
                "plan_to_read": "PLANNING",
                "on_hold": "PAUSED",
            }
            anilist_status = status_map.get(status)

        query = """
        query ($userId: Int, $status: MediaListStatus, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    lastPage
                }
                mediaList(userId: $userId, status: $status, type: MANGA) {
                    id
                    status
                    score
                    progress
                    startedAt {
                        year
                        month
                        day
                    }
                    completedAt {
                        year
                        month
                        day
                    }
                    notes
                    media {
                        id
                        title {
                            romaji
                            english
                            native
                        }
                        coverImage {
                            large
                        }
                        siteUrl
                        status
                        chapters
                    }
                }
            }
        }
        """

        # Get user ID first
        user_info = await self.get_user_info(access_token)
        user_id = int(user_info["user_id"])

        variables = {
            "userId": user_id,
            "status": anilist_status,
            "page": (offset // limit) + 1,
            "perPage": limit,
        }

        result = await self._make_graphql_request(access_token, query, variables)
        page_data = result["data"]["Page"]

        manga_list = []
        for item in page_data["mediaList"]:
            media = item["media"]

            # Format dates
            start_date = self._format_anilist_date(item["startedAt"])
            finish_date = self._format_anilist_date(item["completedAt"])

            manga_data = ExternalMangaData(
                id=str(media["id"]),
                title=media["title"]["romaji"]
                or media["title"]["english"]
                or media["title"]["native"],
                status=item["status"],
                score=item["score"] if item["score"] else None,
                progress=item["progress"],
                start_date=start_date,
                finish_date=finish_date,
                notes=item["notes"],
                url=media["siteUrl"],
                cover_image=(
                    media["coverImage"]["large"] if media["coverImage"] else None
                ),
            )
            manga_list.append(manga_data)

        return ExternalMangaList(
            manga=manga_list,
            total_count=len(manga_list),  # Anilist doesn't provide total count easily
            has_next_page=page_data["pageInfo"]["hasNextPage"],
        )

    async def update_manga_status(
        self,
        access_token: str,
        manga_id: str,
        status: str,
        progress: Optional[int] = None,
        score: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update manga status on Anilist."""
        mutation = """
        mutation ($mediaId: Int, $status: MediaListStatus, $progress: Int, $score: Float, $notes: String) {
            SaveMediaListEntry(mediaId: $mediaId, status: $status, progress: $progress, score: $score, notes: $notes) {
                id
                status
                progress
                score
                notes
            }
        }
        """

        variables = {
            "mediaId": int(manga_id),
            "status": self.map_status_to_external(status),
            "progress": progress,
            "score": score,
            "notes": notes,
        }

        try:
            await self._make_graphql_request(access_token, mutation, variables)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update manga status on Anilist: {e}")
            return False

    async def search_manga(
        self, access_token: str, query: str, limit: int = 10
    ) -> List[ExternalMangaData]:
        """Search for manga on Anilist."""
        search_query = """
        query ($search: String, $perPage: Int) {
            Page(perPage: $perPage) {
                media(search: $search, type: MANGA) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    coverImage {
                        large
                    }
                    siteUrl
                    status
                    chapters
                }
            }
        }
        """

        variables = {"search": query, "perPage": limit}

        result = await self._make_graphql_request(access_token, search_query, variables)
        media_list = result["data"]["Page"]["media"]

        manga_list = []
        for media in media_list:
            manga_data = ExternalMangaData(
                id=str(media["id"]),
                title=media["title"]["romaji"]
                or media["title"]["english"]
                or media["title"]["native"],
                url=media["siteUrl"],
                cover_image=(
                    media["coverImage"]["large"] if media["coverImage"] else None
                ),
            )
            manga_list.append(manga_data)

        return manga_list

    async def _make_graphql_request(
        self, access_token: str, query: str, variables: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a GraphQL request to Anilist."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.BASE_URL, json=payload, headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anilist API request failed: {error_text}")

                data = await response.json()

                if "errors" in data:
                    raise Exception(f"Anilist GraphQL errors: {data['errors']}")

                return data

    def _format_anilist_date(self, date_obj: Optional[Dict]) -> Optional[str]:
        """Format Anilist date object to ISO string."""
        if not date_obj or not all(date_obj.get(k) for k in ["year", "month", "day"]):
            return None

        try:
            date = datetime(date_obj["year"], date_obj["month"], date_obj["day"])
            return date.isoformat()
        except (ValueError, TypeError):
            return None
