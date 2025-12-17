import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from app.schemas.search import SearchResult

logger = logging.getLogger(__name__)


# ============================================================================
# Error Classes for Provider Error Handling
# ============================================================================


class ProviderError(Exception):
    """Base provider error with context and recovery information."""

    def __init__(
        self,
        message: str,
        provider: str,
        recoverable: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize provider error.

        Args:
            message: Human-readable error message
            provider: Name of the provider that raised the error
            recoverable: Whether the error is recoverable (can retry)
            context: Additional context information (URL, status code, etc.)
        """
        self.message = message
        self.provider = provider
        self.recoverable = recoverable
        self.context = context or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "provider": self.provider,
            "recoverable": self.recoverable,
            "context": self.context,
        }


class NetworkError(ProviderError):
    """Network-related errors (timeout, connection refused, DNS, SSL)."""

    def __init__(
        self,
        message: str,
        provider: str,
        error_type: str = "unknown",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize network error.

        Args:
            message: Error message
            provider: Provider name
            error_type: Type of network error (timeout, connection_refused, dns, ssl)
            context: Additional context
        """
        super().__init__(message, provider, recoverable=True, context=context)
        self.error_type = error_type


class RateLimitError(ProviderError):
    """Rate limiting errors (429 Too Many Requests)."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            provider: Provider name
            retry_after: Seconds to wait before retrying
            context: Additional context
        """
        super().__init__(message, provider, recoverable=True, context=context)
        self.retry_after = retry_after or 60  # Default 60 seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary with retry_after."""
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        result["suggestion"] = (
            f"Please wait {self.retry_after} seconds before retrying, "
            f"or try a different provider"
        )
        return result


class AntiBotError(ProviderError):
    """Anti-bot protection detected (Cloudflare, CAPTCHA, etc.)."""

    def __init__(
        self,
        message: str,
        provider: str,
        protection_type: str = "unknown",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize anti-bot error.

        Args:
            message: Error message
            provider: Provider name
            protection_type: Type of protection (cloudflare, captcha, etc.)
            context: Additional context
        """
        super().__init__(message, provider, recoverable=True, context=context)
        self.protection_type = protection_type
        self.requires_headers = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary with protection info."""
        result = super().to_dict()
        result["protection_type"] = self.protection_type
        result["suggestion"] = (
            f"This provider uses {self.protection_type} protection. "
            f"Try enabling FlareSolverr or use a different provider."
        )
        return result


class ParsingError(ProviderError):
    """Parsing errors (invalid HTML, missing elements, unexpected format)."""

    def __init__(
        self,
        message: str,
        provider: str,
        parsing_stage: str = "unknown",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize parsing error.

        Args:
            message: Error message
            provider: Provider name
            parsing_stage: Stage where parsing failed (search, details, chapters, pages)
            context: Additional context
        """
        super().__init__(message, provider, recoverable=False, context=context)
        self.parsing_stage = parsing_stage


class ContentError(ProviderError):
    """Content-related errors (not found, deleted, geo-restricted, premium)."""

    def __init__(
        self,
        message: str,
        provider: str,
        error_type: str = "not_found",
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize content error.

        Args:
            message: Error message
            provider: Provider name
            error_type: Type of content error
                (not_found, deleted, geo_restricted, premium, nsfw_blocked)
            context: Additional context
        """
        super().__init__(message, provider, recoverable=False, context=context)
        self.error_type = error_type


class AgentCapability(Enum):
    """Capabilities that an agent can support."""

    SEARCH = "search"
    MANGA_DETAILS = "manga_details"
    CHAPTERS = "chapters"
    PAGES = "pages"
    DOWNLOAD_PAGE = "download_page"
    DOWNLOAD_COVER = "download_cover"
    HEALTH_CHECK = "health_check"


class AgentStatus(Enum):
    """Status of an agent."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CIRCUIT_OPEN = "circuit_open"


class BaseProvider(ABC):
    """Base class for manga providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the provider."""

    @property
    @abstractmethod
    def url(self) -> str:
        """Get the URL of the provider."""

    @property
    @abstractmethod
    def supports_nsfw(self) -> bool:
        """Check if the provider supports NSFW content."""

    def get_user_agent(self) -> str:
        """
        Get user agent for this provider.

        Returns a realistic browser user agent to avoid anti-bot detection.
        Providers can override this for provider-specific user agents.
        """
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def get_page_headers(self, chapter_url: str) -> Dict[str, str]:
        """
        Get headers for page downloads.

        These headers are specifically for downloading page images and include
        proper referer headers to bypass anti-bot protection.

        Args:
            chapter_url: The URL of the chapter page (used as referer)

        Returns:
            Dictionary of HTTP headers for page downloads
        """
        return {
            "Referer": chapter_url,  # Critical: Match chapter page URL
            "User-Agent": self.get_user_agent(),
            "Origin": self.url,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def get_api_headers(self) -> Dict[str, str]:
        """
        Get headers for API calls.

        These headers are for API requests (different from page downloads).

        Returns:
            Dictionary of HTTP headers for API calls
        """
        return {
            "User-Agent": self.get_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def get_html_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Get headers for HTML page requests.

        Args:
            referer: Optional referer URL

        Returns:
            Dictionary of HTTP headers for HTML requests
        """
        headers = {
            "User-Agent": self.get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        }

        if referer:
            headers["Referer"] = referer

        return headers

    @abstractmethod
    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> tuple[List[SearchResult], int, bool]:
        """
        Search for manga.

        Args:
            query: The search query
            page: The page number
            limit: The number of results per page

        Returns:
            A tuple containing:
            - List of search results
            - Total number of results
            - Whether there are more results
        """

    @abstractmethod
    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """
        Get details for a manga.

        Args:
            manga_id: The ID of the manga

        Returns:
            A dictionary containing manga details
        """

    @abstractmethod
    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """
        Get chapters for a manga.

        Args:
            manga_id: The ID of the manga
            page: The page number
            limit: The number of results per page

        Returns:
            A tuple containing:
            - List of chapters
            - Total number of chapters
            - Whether there are more chapters
        """

    @abstractmethod
    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """
        Get pages for a chapter.

        Args:
            manga_id: The ID of the manga
            chapter_id: The ID of the chapter

        Returns:
            A list of page URLs
        """

    def get_chapter_url(self, manga_id: str, chapter_id: str) -> str:
        """
        Get the chapter URL for use as referer in page downloads.

        Providers should override this to return the actual chapter page URL.
        Default implementation returns the base URL.

        Args:
            manga_id: The ID of the manga
            chapter_id: The ID of the chapter

        Returns:
            The chapter URL
        """
        return self.url

    @abstractmethod
    async def download_page(
        self, page_url: str, referer: Optional[str] = None
    ) -> bytes:
        """
        Download a page.

        Args:
            page_url: The URL of the page
            referer: Optional referer URL (chapter page URL for anti-bot protection)

        Returns:
            The page content as bytes
        """

    @abstractmethod
    async def download_cover(self, manga_id: str) -> bytes:
        """
        Download a manga cover.

        Args:
            manga_id: The ID of the manga

        Returns:
            The cover content as bytes
        """

    async def get_available_manga(
        self, page: int = 1, limit: int = 20
    ) -> tuple[List[SearchResult], int, bool]:
        """
        Get available/popular manga from the provider.

        This method should return popular, trending, or recently updated manga
        instead of requiring a search query. Providers can override this method
        to implement their own logic for fetching available manga.

        Default implementation falls back to an empty search query.

        Args:
            page: The page number
            limit: The number of results per page

        Returns:
            A tuple containing:
            - List of search results
            - Total number of results
            - Whether there are more results
        """
        # Default implementation: try empty search, then popular terms
        try:
            # Try empty search first
            results, total, has_more = await self.search("", page, limit)
            if results:
                return results, total, has_more

            # If empty search fails, try common popular terms
            popular_terms = ["popular", "trending", "latest", "new", "top"]
            for term in popular_terms:
                try:
                    results, total, has_more = await self.search(term, page, limit)
                    if results:
                        return results, total, has_more
                except Exception:
                    continue

            # If all fails, return empty
            return [], 0, False

        except Exception as e:
            logger.error(f"Error getting available manga from {self.name}: {e}")
            return [], 0, False

    async def health_check(
        self, timeout: int = 30
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Perform a health check on the provider.

        Args:
            timeout: Timeout in seconds for the health check

        Returns:
            A tuple containing:
            - bool: Whether the provider is healthy
            - Optional[int]: Response time in milliseconds
            - Optional[str]: Error message if unhealthy
        """
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(self.url) as response:
                    response_time = int((time.time() - start_time) * 1000)

                    if response.status == 200:
                        logger.debug(
                            f"Health check successful for {self.name}: {response_time}ms"
                        )
                        return True, response_time, None
                    else:
                        error_msg = f"HTTP {response.status}"
                        logger.warning(
                            f"Health check failed for {self.name}: {error_msg}"
                        )
                        return False, response_time, error_msg

        except asyncio.TimeoutError:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = f"Timeout after {timeout}s"
            logger.warning(f"Health check timeout for {self.name}: {error_msg}")
            return False, response_time, error_msg

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"Health check error for {self.name}: {error_msg}")
            return False, response_time, error_msg
