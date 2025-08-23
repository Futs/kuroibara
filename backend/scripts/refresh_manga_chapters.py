#!/usr/bin/env python3
"""
Script to refresh chapters for a specific manga from its provider.
This will update the chapter IDs to current valid ones.
"""

import asyncio
import logging
import sys
from pathlib import Path

import httpx

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000/api/v1"


async def refresh_manga_chapters(manga_id: str, token: str):
    """Refresh chapters for a specific manga."""
    logger.info(f"🔄 Refreshing chapters for manga: {manga_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Set authorization header
        client.headers.update({"Authorization": f"Bearer {token}"})

        try:
            # Call the refresh chapters endpoint
            response = await client.post(
                f"{API_BASE}/manga/{manga_id}/refresh-chapters"
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Successfully refreshed chapters!")
                logger.info(f"📊 Chapters added: {result.get('chapters_added', 0)}")
                logger.info(f"📊 Total chapters: {result.get('total_chapters', 0)}")
                return True
            else:
                logger.error(
                    f"❌ Failed to refresh chapters: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error refreshing chapters: {e}")
            return False


async def authenticate_user():
    """Authenticate and get a token."""
    logger.info("🔐 Authenticating...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
        login_data = {"username": "testuser", "password": "password123"}

        response = await client.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("access_token")
            if token:
                logger.info("✅ Authentication successful")
                return token
            else:
                logger.error("❌ No access token in login response")
                return None
        else:
            logger.error(f"❌ Login failed: {response.status_code} - {response.text}")
            return None


async def main():
    """Main function."""
    logger.info("🚀 Starting Chapter Refresh Script")

    # Authenticate
    token = await authenticate_user()
    if not token:
        logger.error("❌ Authentication failed")
        return False

    # The manga ID we want to refresh (Naruto)
    manga_id = "e14e6c74-e1be-4e77-b1a8-74ed6f15ac47"  # Local manga ID

    # Refresh chapters
    success = await refresh_manga_chapters(manga_id, token)

    if success:
        logger.info("🎉 Chapter refresh completed successfully!")
        logger.info("💡 Try downloading chapters again - they should work now!")
    else:
        logger.error("❌ Chapter refresh failed")

    return success


if __name__ == "__main__":
    asyncio.run(main())
