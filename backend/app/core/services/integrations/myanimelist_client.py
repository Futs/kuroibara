"""MyAnimeList API client for manga list integration."""

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


class MyAnimeListClient(BaseIntegrationClient):
    """MyAnimeList API client for REST API integration."""
    
    BASE_URL = "https://api.myanimelist.net/v2"
    AUTH_URL = "https://myanimelist.net/v1/oauth2/token"
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        super().__init__(IntegrationType.MYANIMELIST)
        # Use provided credentials or fall back to environment variables
        self.client_id = client_id or getattr(settings, 'MAL_CLIENT_ID', None)
        self.client_secret = client_secret or getattr(settings, 'MAL_CLIENT_SECRET', None)
    
    async def authenticate(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate with MyAnimeList using authorization code."""
        if not self.client_id or not self.client_secret:
            raise ValueError("MyAnimeList client credentials not configured")
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_data['authorization_code'],
            'code_verifier': auth_data['code_verifier'],
            'grant_type': 'authorization_code',
            'redirect_uri': auth_data['redirect_uri']
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.AUTH_URL, 
                data=urlencode(token_data), 
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"MyAnimeList authentication failed: {error_text}")
                
                data = await response.json()
                
                # Get user info
                user_info = await self.get_user_info(data['access_token'])
                
                return {
                    'access_token': data['access_token'],
                    'refresh_token': data['refresh_token'],
                    'expires_at': datetime.utcnow() + timedelta(seconds=data['expires_in']),
                    'user_info': user_info
                }
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh MyAnimeList access token."""
        if not self.client_id or not self.client_secret:
            raise ValueError("MyAnimeList client credentials not configured")
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.AUTH_URL, 
                data=urlencode(token_data), 
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"MyAnimeList token refresh failed: {error_text}")
                
                data = await response.json()
                
                return {
                    'access_token': data['access_token'],
                    'refresh_token': data['refresh_token'],
                    'expires_at': datetime.utcnow() + timedelta(seconds=data['expires_in'])
                }
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from MyAnimeList."""
        url = f"{self.BASE_URL}/users/@me"
        
        result = await self._make_api_request(access_token, url)
        
        return {
            'user_id': str(result['id']),
            'username': result['name'],
            'avatar_url': result.get('picture'),
            'joined_at': result.get('joined_at')
        }
    
    async def get_manga_list(
        self, 
        access_token: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> ExternalMangaList:
        """Get user's manga list from MyAnimeList."""
        url = f"{self.BASE_URL}/users/@me/mangalist"
        
        params = {
            'fields': 'list_status{status,score,num_chapters_read,is_rereading,start_date,finish_date,tags,comments}',
            'limit': limit,
            'offset': offset
        }
        
        if status:
            # Map internal status to MAL status
            status_map = {
                'reading': 'reading',
                'completed': 'completed',
                'dropped': 'dropped',
                'plan_to_read': 'plan_to_read',
                'on_hold': 'on_hold'
            }
            mal_status = status_map.get(status)
            if mal_status:
                params['status'] = mal_status
        
        result = await self._make_api_request(access_token, url, params)
        
        manga_list = []
        for item in result['data']:
            manga = item['node']
            list_status = item.get('list_status', {})
            
            manga_data = ExternalMangaData(
                id=str(manga['id']),
                title=manga['title'],
                status=list_status.get('status'),
                score=list_status.get('score') if list_status.get('score', 0) > 0 else None,
                progress=list_status.get('num_chapters_read'),
                start_date=list_status.get('start_date'),
                finish_date=list_status.get('finish_date'),
                notes=list_status.get('comments'),
                url=f"https://myanimelist.net/manga/{manga['id']}",
                cover_image=manga.get('main_picture', {}).get('large')
            )
            manga_list.append(manga_data)
        
        return ExternalMangaList(
            manga=manga_list,
            total_count=len(manga_list),  # MAL doesn't provide total count in this endpoint
            has_next_page=len(manga_list) == limit  # Assume there's more if we got a full page
        )
    
    async def update_manga_status(
        self, 
        access_token: str, 
        manga_id: str, 
        status: str,
        progress: Optional[int] = None,
        score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update manga status on MyAnimeList."""
        url = f"{self.BASE_URL}/manga/{manga_id}/my_list_status"
        
        data = {
            'status': self.map_status_to_mal(status)
        }
        
        if progress is not None:
            data['num_chapters_read'] = progress
        
        if score is not None:
            # MAL uses 1-10 scale
            data['score'] = int(score) if 1 <= score <= 10 else 0
        
        if notes:
            data['comments'] = notes
        
        try:
            await self._make_api_request(
                access_token, 
                url, 
                method='PUT', 
                data=urlencode(data),
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to update manga status on MyAnimeList: {e}")
            return False
    
    async def search_manga(
        self, 
        access_token: str, 
        query: str, 
        limit: int = 10
    ) -> List[ExternalMangaData]:
        """Search for manga on MyAnimeList."""
        url = f"{self.BASE_URL}/manga"
        
        params = {
            'q': query,
            'limit': limit,
            'fields': 'title,main_picture,status,num_chapters'
        }
        
        result = await self._make_api_request(access_token, url, params)
        
        manga_list = []
        for item in result['data']:
            manga = item['node']
            
            manga_data = ExternalMangaData(
                id=str(manga['id']),
                title=manga['title'],
                url=f"https://myanimelist.net/manga/{manga['id']}",
                cover_image=manga.get('main_picture', {}).get('large')
            )
            manga_list.append(manga_data)
        
        return manga_list
    
    async def _make_api_request(
        self, 
        access_token: str, 
        url: str, 
        params: Optional[Dict] = None,
        method: str = 'GET',
        data: Optional[str] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an API request to MyAnimeList."""
        request_headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        if headers:
            request_headers.update(headers)
        
        async with aiohttp.ClientSession() as session:
            kwargs = {'headers': request_headers}
            
            if params:
                kwargs['params'] = params
            
            if data:
                kwargs['data'] = data
            
            async with session.request(method, url, **kwargs) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"MyAnimeList API request failed: {response.status} - {error_text}")
                
                return await response.json()
    
    def map_status_to_mal(self, internal_status: str) -> str:
        """Map internal status to MyAnimeList status."""
        status_mapping = {
            "reading": "reading",
            "completed": "completed", 
            "dropped": "dropped",
            "plan_to_read": "plan_to_read",
            "on_hold": "on_hold"
        }
        return status_mapping.get(internal_status, "reading")
    
    def map_status_from_mal(self, mal_status: str) -> str:
        """Map MyAnimeList status to internal status."""
        status_mapping = {
            "reading": "reading",
            "completed": "completed",
            "dropped": "dropped", 
            "plan_to_read": "plan_to_read",
            "on_hold": "on_hold"
        }
        return status_mapping.get(mal_status, "reading")
