"""
FlareSolverr integration for bypassing Cloudflare protection.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class FlareSolverrClient:
    """Client for interacting with FlareSolverr proxy."""

    def __init__(self, flaresolverr_url: str = "http://localhost:8191"):
        self.flaresolverr_url = flaresolverr_url
        self.session_id = None

    async def create_session(self) -> Optional[str]:
        """Create a new FlareSolverr session."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.flaresolverr_url}/v1",
                    json={
                        "cmd": "sessions.create",
                        "session": f"kuroibara_{asyncio.current_task().get_name() if asyncio.current_task() else 'default'}",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        self.session_id = data["session"]
                        logger.info(f"Created FlareSolverr session: {self.session_id}")
                        return self.session_id

        except Exception as e:
            logger.error(f"Failed to create FlareSolverr session: {e}")

        return None

    async def destroy_session(self):
        """Destroy the FlareSolverr session."""
        if not self.session_id:
            return

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    f"{self.flaresolverr_url}/v1",
                    json={"cmd": "sessions.destroy", "session": self.session_id},
                )
                logger.info(f"Destroyed FlareSolverr session: {self.session_id}")

        except Exception as e:
            logger.error(f"Failed to destroy FlareSolverr session: {e}")

        self.session_id = None

    async def get(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make a GET request through FlareSolverr."""
        if not self.session_id:
            await self.create_session()

        if not self.session_id:
            return None

        try:
            request_data = {
                "cmd": "request.get",
                "url": url,
                "session": self.session_id,
                "maxTimeout": 60000,
            }

            if headers:
                request_data["headers"] = headers

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.flaresolverr_url}/v1", json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        solution = data.get("solution", {})
                        return {
                            "status_code": solution.get("status"),
                            "content": solution.get("response"),
                            "cookies": solution.get("cookies", []),
                            "headers": solution.get("headers", {}),
                            "url": solution.get("url"),
                        }
                    else:
                        logger.error(f"FlareSolverr error: {data.get('message')}")

        except Exception as e:
            logger.error(f"FlareSolverr request failed: {e}")

        return None


class CloudflareBypassProvider:
    """Enhanced provider that can bypass Cloudflare protection."""

    def __init__(
        self,
        use_flaresolverr: bool = False,
        flaresolverr_url: str = "http://localhost:8191",
    ):
        self.use_flaresolverr = use_flaresolverr
        self.flaresolverr_client = (
            FlareSolverrClient(flaresolverr_url) if use_flaresolverr else None
        )

    async def make_request(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make a request, using FlareSolverr if needed."""

        # First try normal request
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url, headers=headers or {})

                # If we get Cloudflare protection, try FlareSolverr
                if (
                    response.status_code in [403, 503, 521]
                    or "cloudflare" in response.text.lower()
                ):
                    logger.info(
                        f"Cloudflare protection detected for {url}, trying FlareSolverr"
                    )

                    if self.use_flaresolverr and self.flaresolverr_client:
                        return await self.flaresolverr_client.get(url, headers)
                    else:
                        logger.warning(
                            f"Cloudflare protection detected but FlareSolverr not enabled for {url}"
                        )
                        return None

                # Normal successful response
                return {
                    "status_code": response.status_code,
                    "content": response.text,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                }

        except Exception as e:
            logger.error(f"Normal request failed for {url}: {e}")

            # Try FlareSolverr as fallback
            if self.use_flaresolverr and self.flaresolverr_client:
                logger.info(f"Trying FlareSolverr as fallback for {url}")
                return await self.flaresolverr_client.get(url, headers)

        return None

    async def cleanup(self):
        """Clean up resources."""
        if self.flaresolverr_client:
            await self.flaresolverr_client.destroy_session()


# Docker Compose addition for FlareSolverr
FLARESOLVERR_DOCKER_COMPOSE = """
  flaresolverr:
    image: ghcr.io/flaresolverr/flaresolverr:latest
    container_name: kuroibara-flaresolverr
    environment:
      - LOG_LEVEL=info
      - LOG_HTML=false
      - CAPTCHA_SOLVER=none
    ports:
      - "8191:8191"
    restart: unless-stopped
    networks:
      - kuroibara-network
"""


# Example usage in provider
async def example_usage():
    """Example of how to use the Cloudflare bypass provider."""

    # Create provider with FlareSolverr enabled
    provider = CloudflareBypassProvider(
        use_flaresolverr=True, flaresolverr_url="http://localhost:8191"
    )

    try:
        # Test with a Cloudflare-protected site
        result = await provider.make_request("https://manhuaga.com")

        if result:
            print(f"Status: {result['status_code']}")
            print(f"Content length: {len(result['content'])}")
            print(f"Final URL: {result['url']}")
        else:
            print("Request failed")

    finally:
        await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(example_usage())
