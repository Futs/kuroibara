"""
Adapter to make existing providers work as agents.

This adapter allows existing BaseProvider instances to work seamlessly
with the new agent system without requiring any changes to existing code.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.providers.base import BaseProvider
from app.schemas.search import SearchResult

from .base import AgentCapability, BaseAgent

logger = logging.getLogger(__name__)


class ProviderToAgentAdapter(BaseAgent):
    """
    Adapter that wraps existing BaseProvider instances to work as agents.

    This ensures 100% backward compatibility - existing providers continue
    to work exactly as before, but now also benefit from agent features
    like error isolation, metrics tracking, and circuit breaker patterns.
    """

    def __init__(self, provider: BaseProvider):
        """
        Initialize the adapter with an existing provider.

        Args:
            provider: An existing BaseProvider instance
        """
        self.provider = provider

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

        logger.debug(f"Created agent adapter for provider: {provider.name}")

    @property
    def url(self) -> str:
        """Get the URL from the wrapped provider."""
        return self.provider.url

    @property
    def supports_nsfw(self) -> bool:
        """Get NSFW support from the wrapped provider."""
        return self.provider.supports_nsfw

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search using the wrapped provider with error handling."""
        return await self._execute_with_error_handling(
            "search", self.provider.search, query, page, limit
        )

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get manga details using the wrapped provider with error handling."""
        return await self._execute_with_error_handling(
            "get_manga_details", self.provider.get_manga_details, manga_id
        )

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters using the wrapped provider with error handling."""
        return await self._execute_with_error_handling(
            "get_chapters", self.provider.get_chapters, manga_id, page, limit
        )

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages using the wrapped provider with error handling."""
        return await self._execute_with_error_handling(
            "get_pages", self.provider.get_pages, manga_id, chapter_id
        )

    async def download_page(self, page_url: str) -> bytes:
        """Download page using the wrapped provider with error handling."""
        return await self._execute_with_error_handling(
            "download_page", self.provider.download_page, page_url
        )

    async def download_cover(self, manga_id: str) -> bytes:
        """Download cover using the wrapped provider with error handling."""
        return await self._execute_with_error_handling(
            "download_cover", self.provider.download_cover, manga_id
        )

    async def _health_check_impl(
        self, timeout: int
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """Health check using the wrapped provider."""
        return await self.provider.health_check(timeout)

    def __getattr__(self, name):
        """
        Delegate any other attribute access to the wrapped provider.

        This ensures that any provider-specific methods or properties
        are still accessible through the adapter.
        """
        return getattr(self.provider, name)

    def __repr__(self):
        return f"ProviderToAgentAdapter({self.provider.name})"
