"""Kitsu API client for external integration."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

import aiohttp
from aiohttp import ClientSession

from app.models.external_integration import IntegrationType
from .base_client import BaseIntegrationClient

logger = logging.getLogger(__name__)


class KitsuClient(BaseIntegrationClient):
    """Client for Kitsu API integration."""

    def __init__(
        self, client_id: Optional[str] = None, client_secret: Optional[str] = None
    ):
        super().__init__(IntegrationType.KITSU)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://kitsu.io/api/edge"
        self.auth_url = "https://kitsu.io/api/oauth/token"

    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with Kitsu using username/password.
        Kitsu uses OAuth2 Resource Owner Password Credentials Grant.
        """
        try:
            async with ClientSession() as session:
                auth_data = {
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                }

                headers = {
                    "Content-Type": "application/vnd.api+json",
                    "Accept": "application/vnd.api+json",
                }

                async with session.post(
                    self.auth_url, json=auth_data, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "access_token": data.get("access_token"),
                            "refresh_token": data.get("refresh_token"),
                            "token_type": data.get("token_type", "Bearer"),
                            "expires_in": data.get("expires_in"),
                            "scope": data.get("scope"),
                        }
                    else:
                        error_data = await response.text()
                        logger.error(
                            f"Kitsu authentication failed: {response.status} - {error_data}"
                        )
                        raise Exception(f"Authentication failed: {response.status}")

        except Exception as e:
            logger.error(f"Kitsu authentication error: {e}")
            raise

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        try:
            async with ClientSession() as session:
                refresh_data = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }

                headers = {
                    "Content-Type": "application/vnd.api+json",
                    "Accept": "application/vnd.api+json",
                }

                async with session.post(
                    self.auth_url, json=refresh_data, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "access_token": data.get("access_token"),
                            "refresh_token": data.get("refresh_token"),
                            "token_type": data.get("token_type", "Bearer"),
                            "expires_in": data.get("expires_in"),
                        }
                    else:
                        error_data = await response.text()
                        logger.error(
                            f"Kitsu token refresh failed: {response.status} - {error_data}"
                        )
                        raise Exception(f"Token refresh failed: {response.status}")

        except Exception as e:
            logger.error(f"Kitsu token refresh error: {e}")
            raise

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get current user information."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }

            async with ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/users?filter[self]=true", headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data") and len(data["data"]) > 0:
                            user_data = data["data"][0]
                            return {
                                "id": user_data.get("id"),
                                "username": user_data.get("attributes", {}).get("name"),
                                "slug": user_data.get("attributes", {}).get("slug"),
                                "email": user_data.get("attributes", {}).get("email"),
                            }
                        else:
                            raise Exception("No user data found")
                    else:
                        error_data = await response.text()
                        logger.error(
                            f"Kitsu get user info failed: {response.status} - {error_data}"
                        )
                        raise Exception(f"Failed to get user info: {response.status}")

        except Exception as e:
            logger.error(f"Kitsu get user info error: {e}")
            raise

    async def get_user_manga_list(
        self, access_token: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Get user's manga list from Kitsu."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }

            manga_list = []
            url = f"{self.base_url}/library-entries?filter[userId]={user_id}&filter[kind]=manga&include=manga"

            async with ClientSession() as session:
                while url:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Process library entries
                            for entry in data.get("data", []):
                                manga_info = self._extract_manga_from_entry(
                                    entry, data.get("included", [])
                                )
                                if manga_info:
                                    manga_list.append(manga_info)

                            # Check for next page
                            url = data.get("links", {}).get("next")
                        else:
                            error_data = await response.text()
                            logger.error(
                                f"Kitsu get manga list failed: {response.status} - {error_data}"
                            )
                            break

            return manga_list

        except Exception as e:
            logger.error(f"Kitsu get manga list error: {e}")
            raise

    def _extract_manga_from_entry(
        self, entry: Dict[str, Any], included: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Extract manga information from library entry and included data."""
        try:
            # Find the manga data in included resources
            manga_relationship = entry.get("relationships", {}).get("manga", {})
            manga_id = manga_relationship.get("data", {}).get("id")

            manga_data = None
            for item in included:
                if item.get("type") == "manga" and item.get("id") == manga_id:
                    manga_data = item
                    break

            if not manga_data:
                return None

            attributes = entry.get("attributes", {})
            manga_attributes = manga_data.get("attributes", {})

            return {
                "external_id": manga_id,
                "title": manga_attributes.get("canonicalTitle")
                or manga_attributes.get("titles", {}).get("en"),
                "status": self.map_status_from_kitsu(attributes.get("status")),
                "progress": attributes.get("progress", 0),
                "rating": attributes.get("ratingTwenty"),  # Kitsu uses 20-point scale
                "started_at": attributes.get("startedAt"),
                "finished_at": attributes.get("finishedAt"),
                "updated_at": attributes.get("updatedAt"),
                "notes": attributes.get("notes"),
                "manga_data": {
                    "synopsis": manga_attributes.get("synopsis"),
                    "chapter_count": manga_attributes.get("chapterCount"),
                    "volume_count": manga_attributes.get("volumeCount"),
                    "status": manga_attributes.get("status"),
                    "poster_image": manga_attributes.get("posterImage", {}).get(
                        "large"
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error extracting manga from entry: {e}")
            return None

    def map_status_to_kitsu(self, status: str) -> str:
        """Map internal status to Kitsu status."""
        status_mapping = {
            "reading": "current",
            "completed": "completed",
            "on_hold": "on_hold",
            "dropped": "dropped",
            "plan_to_read": "planned",
        }
        return status_mapping.get(status, "planned")

    def map_status_from_kitsu(self, kitsu_status: str) -> str:
        """Map Kitsu status to internal status."""
        status_mapping = {
            "current": "reading",
            "completed": "completed",
            "on_hold": "on_hold",
            "dropped": "dropped",
            "planned": "plan_to_read",
        }
        return status_mapping.get(kitsu_status, "plan_to_read")

    async def update_manga_status(
        self,
        access_token: str,
        manga_id: str,
        status: str,
        progress: Optional[int] = None,
        rating: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update manga status on Kitsu."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }

            update_data = {
                "data": {
                    "type": "libraryEntries",
                    "id": manga_id,  # This should be the library entry ID
                    "attributes": {"status": self.map_status_to_kitsu(status)},
                }
            }

            if progress is not None:
                update_data["data"]["attributes"]["progress"] = progress

            if rating is not None:
                # Convert to Kitsu's 20-point scale if needed
                update_data["data"]["attributes"]["ratingTwenty"] = rating

            if notes is not None:
                update_data["data"]["attributes"]["notes"] = notes

            async with ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/library-entries/{manga_id}",
                    json=update_data,
                    headers=headers,
                ) as response:
                    return response.status in [200, 204]

        except Exception as e:
            logger.error(f"Kitsu update manga status error: {e}")
            return False

    async def get_manga_list(
        self,
        access_token: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get user's manga list from Kitsu (implementing abstract method)."""
        try:
            # Get user info first to get user ID
            user_info = await self.get_user_info(access_token)
            user_id = user_info["id"]

            return await self.get_user_manga_list(access_token, user_id)

        except Exception as e:
            logger.error(f"Kitsu get manga list error: {e}")
            return []

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token (implementing abstract method)."""
        return await self.refresh_access_token(refresh_token)

    async def search_manga(
        self, access_token: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for manga on Kitsu."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.api+json",
                "Accept": "application/vnd.api+json",
            }

            # URL encode the query
            import urllib.parse

            encoded_query = urllib.parse.quote(query)

            async with ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/manga?filter[text]={encoded_query}&page[limit]={limit}",
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        for manga in data.get("data", []):
                            attributes = manga.get("attributes", {})
                            results.append(
                                {
                                    "id": manga.get("id"),
                                    "title": attributes.get("canonicalTitle")
                                    or attributes.get("titles", {}).get("en"),
                                    "synopsis": attributes.get("synopsis"),
                                    "chapter_count": attributes.get("chapterCount"),
                                    "volume_count": attributes.get("volumeCount"),
                                    "status": attributes.get("status"),
                                    "poster_image": attributes.get(
                                        "posterImage", {}
                                    ).get("large"),
                                    "average_rating": attributes.get("averageRating"),
                                    "start_date": attributes.get("startDate"),
                                    "end_date": attributes.get("endDate"),
                                }
                            )

                        return results
                    else:
                        logger.error(f"Kitsu search failed: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Kitsu search manga error: {e}")
            return []
