"""
JavaScript-based provider for handling dynamic content and bot protection.

This provider class is designed for modern manga sites that use:
- Heavy JavaScript for content loading
- Dynamic image loading (lazy loading, AJAX)
- Anti-bot protection (Cloudflare, custom)
- Session management and cookies
- Browser simulation requirements

Suitable for sites like:
- HiperDEX (WordPress + JS)
- Webtoons (React-based)
- Official publishers with protection
- Modern manga aggregators
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import aiohttp

from .base import AgentCapability, BaseProvider
from .enhanced_generic import FlareSolverrClient

# Rate limiting is handled by the agent system

logger = logging.getLogger(__name__)


class JavaScriptProvider(BaseProvider):
    """
    Advanced provider for JavaScript-heavy manga sites with bot protection.

    Features:
    - FlareSolverr integration for Cloudflare bypass
    - Session management with cookie persistence
    - Dynamic content extraction from JavaScript
    - Advanced rate limiting and retry logic
    - User-agent rotation and browser simulation
    - Proxy support for geo-restrictions
    """

    def __init__(
        self,
        name: str,
        url: str,
        use_flaresolverr: bool = True,
        flaresolverr_url: str = "http://localhost:8191",
        **kwargs,
    ):
        self._name = name
        self._url = url
        self._supports_nsfw = kwargs.get("supports_nsfw", False)

        # JavaScript execution capabilities
        self.use_flaresolverr = use_flaresolverr
        self.flaresolverr_client = (
            FlareSolverrClient(flaresolverr_url) if use_flaresolverr else None
        )

        # Session management
        self.session_cookies = {}
        self.session_headers = {}
        self.last_request_time = 0

        # Rate limiting (more conservative for JS sites)
        self.min_request_delay = 3.0  # 3 seconds between requests
        self.max_retries = 3
        self.retry_delay = 5.0

        # Browser simulation
        self.user_agents = [
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        ]

        # Site-specific configuration
        self.selectors = kwargs.get("selectors", {})
        self.javascript_patterns = kwargs.get("javascript_patterns", {})

    @property
    def name(self) -> str:
        """Get the name of the provider."""
        return self._name

    @property
    def url(self) -> str:
        """Get the URL of the provider."""
        return self._url

    @property
    def supports_nsfw(self) -> bool:
        """Check if the provider supports NSFW content."""
        return self._supports_nsfw

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return provider capabilities."""
        caps = [
            AgentCapability.SEARCH,
            AgentCapability.MANGA_DETAILS,
            AgentCapability.CHAPTERS,
            AgentCapability.PAGES,
            AgentCapability.DOWNLOAD_PAGE,
            AgentCapability.DOWNLOAD_COVER,
            AgentCapability.HEALTH_CHECK,
        ]

        return caps

    async def _make_request(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        use_session: bool = True,
        retry_count: int = 0,
    ) -> Optional[str]:
        """
        Make HTTP request with JavaScript execution support.

        Args:
            url: Target URL
            headers: Additional headers
            use_session: Whether to use session cookies
            retry_count: Current retry attempt

        Returns:
            Response content or None if failed
        """
        # Rate limiting
        await self._apply_rate_limit()

        # Prepare headers
        request_headers = self._get_headers(headers, use_session)

        try:
            # Try FlareSolverr first for protected sites
            if self.use_flaresolverr and self.flaresolverr_client:
                logger.debug(f"Making FlareSolverr request to {url}")
                result = await self.flaresolverr_client.get(url, request_headers)

                if result and result.get("content"):
                    # Update session cookies from FlareSolverr
                    if result.get("cookies"):
                        self._update_session_cookies(result["cookies"])
                    return result["content"]

                logger.warning(f"FlareSolverr failed for {url}, trying direct request")

            # Fallback to direct request
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60), headers=request_headers
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Update session cookies
                        if use_session:
                            self._update_session_cookies(response.cookies)

                        return content

                    elif response.status in [403, 503, 521]:
                        # Likely bot protection
                        logger.warning(
                            f"Bot protection detected (HTTP {response.status}) "
                            f"for {url}"
                        )

                        if retry_count < self.max_retries:
                            await asyncio.sleep(self.retry_delay * (retry_count + 1))
                            return await self._make_request(
                                url, headers, use_session, retry_count + 1
                            )

                    else:
                        logger.warning(f"HTTP {response.status} for {url}")

        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")

            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._make_request(
                    url, headers, use_session, retry_count + 1
                )

        return None

    async def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_delay:
            sleep_time = self.min_request_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_headers(
        self,
        additional_headers: Optional[Dict[str, str]] = None,
        use_session: bool = True,
    ) -> Dict[str, str]:
        """Get request headers with browser simulation."""
        headers = {
            "User-Agent": self.user_agents[int(time.time()) % len(self.user_agents)],
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

        # Add session headers
        if use_session:
            headers.update(self.session_headers)

        # Add additional headers
        if additional_headers:
            headers.update(additional_headers)

        return headers

    def _update_session_cookies(self, cookies):
        """Update session cookies from response."""
        if isinstance(cookies, list):
            # FlareSolverr format
            for cookie in cookies:
                if isinstance(cookie, dict):
                    self.session_cookies[cookie.get("name")] = cookie.get("value")
        else:
            # aiohttp format
            for cookie in cookies:
                self.session_cookies[cookie.key] = cookie.value

    def _extract_javascript_data(
        self, content: str, patterns: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract data from JavaScript variables and JSON objects.

        Args:
            content: HTML content
            patterns: Dictionary of pattern names to regex patterns

        Returns:
            Extracted data dictionary
        """
        data = {}

        for name, pattern in patterns.items():
            try:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    if match.groups():
                        raw_data = match.group(1)

                        # Try to parse as JSON
                        try:
                            data[name] = json.loads(raw_data)
                        except json.JSONDecodeError:
                            # Store as string if not valid JSON
                            data[name] = raw_data.strip()
                    else:
                        data[name] = match.group(0)

            except Exception as e:
                logger.warning(f"Failed to extract {name} with pattern {pattern}: {e}")

        return data

    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> tuple[List[Any], int, bool]:
        """Search for manga with JavaScript support."""
        # This method should be implemented by subclasses
        # with site-specific search logic
        raise NotImplementedError("Subclasses must implement search method")

    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get manga details with JavaScript extraction."""
        # This method should be implemented by subclasses
        # with site-specific detail extraction logic
        raise NotImplementedError("Subclasses must implement get_manga_details method")

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """Get chapter list with JavaScript support."""
        # This method should be implemented by subclasses
        # with site-specific chapter extraction logic
        raise NotImplementedError("Subclasses must implement get_chapters method")

    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get page URLs with JavaScript extraction."""
        # This method should be implemented by subclasses
        # with site-specific page extraction logic
        raise NotImplementedError("Subclasses must implement get_pages method")

    async def download_page(
        self, page_url: str, referer: Optional[str] = None
    ) -> bytes:
        """
        Download a page with JavaScript support.

        Args:
            page_url: The URL of the page to download
            referer: Optional referer URL (not used for JavaScript provider)

        Returns:
            The page content as bytes
        """
        try:
            content = await self._make_request(page_url)
            if content:
                return content.encode("utf-8")
            return b""
        except Exception as e:
            logger.error(f"Error downloading page {page_url}: {e}")
            return b""

    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover."""
        # This method should be implemented by subclasses
        # with site-specific cover download logic
        raise NotImplementedError("Subclasses must implement download_cover method")

    async def health_check(
        self, timeout: int = 30
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Enhanced health check with JavaScript execution."""
        start_time = time.time()

        try:
            content = await self._make_request(self.url)
            response_time = int((time.time() - start_time) * 1000)

            if content:
                # Check for common bot protection indicators
                if any(
                    indicator in content.lower()
                    for indicator in [
                        "cloudflare",
                        "ddos protection",
                        "checking your browser",
                        "please wait",
                        "security check",
                    ]
                ):
                    return False, response_time, "Bot protection detected"

                return True, response_time, None
            else:
                return False, response_time, "No content received"

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            return False, response_time, str(e)
