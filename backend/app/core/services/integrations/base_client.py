"""Base class for external integration clients."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.models.external_integration import IntegrationType, SyncStatus
from app.schemas.external_integration import ExternalMangaData, ExternalMangaList

logger = logging.getLogger(__name__)


class BaseIntegrationClient(ABC):
    """Base class for external integration clients."""
    
    def __init__(self, integration_type: IntegrationType):
        self.integration_type = integration_type
        self.logger = logging.getLogger(f"{__name__}.{integration_type.value}")
    
    @abstractmethod
    async def authenticate(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with the external service.
        
        Args:
            auth_data: Authentication data (authorization code, etc.)
            
        Returns:
            Dict containing access_token, refresh_token, expires_at, user_info
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh the access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dict containing new access_token, refresh_token, expires_at
        """
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from the external service.
        
        Args:
            access_token: The access token
            
        Returns:
            Dict containing user_id, username, and other user info
        """
        pass
    
    @abstractmethod
    async def get_manga_list(
        self, 
        access_token: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> ExternalMangaList:
        """
        Get user's manga list from the external service.
        
        Args:
            access_token: The access token
            status: Filter by status (reading, completed, etc.)
            limit: Number of items to fetch
            offset: Offset for pagination
            
        Returns:
            ExternalMangaList containing manga data
        """
        pass
    
    @abstractmethod
    async def update_manga_status(
        self, 
        access_token: str, 
        manga_id: str, 
        status: str,
        progress: Optional[int] = None,
        score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update manga status on the external service.
        
        Args:
            access_token: The access token
            manga_id: External manga ID
            status: New status
            progress: Reading progress (chapters read)
            score: User rating/score
            notes: User notes
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def search_manga(
        self, 
        access_token: str, 
        query: str, 
        limit: int = 10
    ) -> List[ExternalMangaData]:
        """
        Search for manga on the external service.
        
        Args:
            access_token: The access token
            query: Search query
            limit: Number of results to return
            
        Returns:
            List of ExternalMangaData
        """
        pass
    
    async def validate_token(self, access_token: str) -> bool:
        """
        Validate if the access token is still valid.
        
        Args:
            access_token: The access token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            await self.get_user_info(access_token)
            return True
        except Exception as e:
            self.logger.warning(f"Token validation failed: {e}")
            return False
    
    def map_status_to_external(self, internal_status: str) -> str:
        """
        Map internal status to external service status.
        Override in subclasses for service-specific mapping.
        
        Args:
            internal_status: Internal status (reading, completed, dropped, etc.)
            
        Returns:
            External service status
        """
        status_mapping = {
            "reading": "CURRENT",
            "completed": "COMPLETED", 
            "dropped": "DROPPED",
            "plan_to_read": "PLANNING",
            "on_hold": "PAUSED"
        }
        return status_mapping.get(internal_status, "CURRENT")
    
    def map_status_from_external(self, external_status: str) -> str:
        """
        Map external service status to internal status.
        Override in subclasses for service-specific mapping.
        
        Args:
            external_status: External service status
            
        Returns:
            Internal status
        """
        status_mapping = {
            "CURRENT": "reading",
            "COMPLETED": "completed",
            "DROPPED": "dropped", 
            "PLANNING": "plan_to_read",
            "PAUSED": "on_hold"
        }
        return status_mapping.get(external_status, "reading")
