"""
ProviderAgent - Wraps existing providers to work as agents.

This class provides the bridge between existing providers and the new agent system,
adding agent functionality like error isolation, metrics, and circuit breakers.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.providers.base import BaseProvider
from app.schemas.search import SearchResult

from .base import AgentCapability, BaseAgent

logger = logging.getLogger(__name__)


class ProviderAgent(BaseAgent):
    """
    Agent that wraps an existing provider to add agent functionality.

    This class takes any BaseProvider instance and wraps it with agent
    capabilities including error isolation, metrics tracking, circuit
    breaker patterns, and standardized error handling.
    """

    def __init__(self, provider: BaseProvider, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent with a provider.

        Args:
            provider: The provider instance to wrap
            config: Optional configuration dictionary
        """
        self.provider = provider
        self.config = config or {}

        # Determine capabilities based on provider methods
        capabilities = [
            AgentCapability.SEARCH,
            AgentCapability.MANGA_DETAILS,
            AgentCapability.CHAPTERS,
            AgentCapability.PAGES,
            AgentCapability.DOWNLOAD_PAGE,
            AgentCapability.DOWNLOAD_COVER,
            AgentCapability.HEALTH_CHECK,
        ]

        super().__init__(provider.name, capabilities)

        # Configure circuit breaker based on config
        self._circuit_breaker_threshold = self.config.get(
            "circuit_breaker_threshold", 5
        )
        self._circuit_breaker_timeout = self.config.get("circuit_breaker_timeout", 300)

        logger.debug(f"Created ProviderAgent for: {provider.name}")

    @property
    def url(self) -> str:
        """Get the URL from the wrapped provider."""
        return self.provider.url

    @property
    def supports_nsfw(self) -> bool:
        """Get NSFW support from the wrapped provider."""
        return self.provider.supports_nsfw

    @property
    def priority(self) -> int:
        """Get priority from configuration."""
        return self.config.get("priority", 999)

    @property
    def requires_flaresolverr(self) -> bool:
        """Check if provider requires FlareSolverr."""
        return self.config.get("requires_flaresolverr", False)

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search using the wrapped provider with agent error handling."""
        return await self._execute_with_error_handling(
            "search", self.provider.search, query, page, limit
        )

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get manga details using the wrapped provider with agent error handling."""
        return await self._execute_with_error_handling(
            "get_manga_details", self.provider.get_manga_details, manga_id
        )

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters using the wrapped provider with agent error handling."""
        return await self._execute_with_error_handling(
            "get_chapters", self.provider.get_chapters, manga_id, page, limit
        )

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages using the wrapped provider with agent error handling."""
        return await self._execute_with_error_handling(
            "get_pages", self.provider.get_pages, manga_id, chapter_id
        )

    async def download_page(
        self, page_url: str, referer: Optional[str] = None
    ) -> bytes:
        """
        Download page using the wrapped provider with agent error handling.

        Args:
            page_url: The URL of the page to download
            referer: Optional referer URL (chapter page URL)

        Returns:
            The page content as bytes
        """
        return await self._execute_with_error_handling(
            "download_page", self.provider.download_page, page_url, referer=referer
        )

    async def download_cover(self, manga_id: str) -> bytes:
        """Download cover using the wrapped provider with agent error handling."""
        return await self._execute_with_error_handling(
            "download_cover", self.provider.download_cover, manga_id
        )

    async def _health_check_impl(
        self, timeout: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Health check using the wrapped provider."""
        return await self.provider.health_check(timeout)

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the wrapped provider.

        Returns:
            Dictionary containing provider and agent information
        """
        return {
            "id": self.name.lower(),
            "name": self.name,
            "url": self.url,
            "supports_nsfw": self.supports_nsfw,
            "requires_flaresolverr": self.requires_flaresolverr,
            "priority": self.priority,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "provider_class": self.provider.__class__.__name__,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "average_response_time": self.metrics.average_response_time,
                "last_request_time": (
                    self.metrics.last_request_time.isoformat()
                    if self.metrics.last_request_time
                    else None
                ),
                "last_error": self.metrics.last_error,
                "last_error_time": (
                    self.metrics.last_error_time.isoformat()
                    if self.metrics.last_error_time
                    else None
                ),
                "circuit_breaker_count": self.metrics.circuit_breaker_count,
            },
            "config": self.config,
        }

    def __getattr__(self, name):
        """
        Delegate any other attribute access to the wrapped provider.

        This ensures that any provider-specific methods or properties
        are still accessible through the agent.
        """
        if hasattr(self.provider, name):
            return getattr(self.provider, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def __repr__(self):
        return f"ProviderAgent({self.provider.name}, status={self.status.value})"
