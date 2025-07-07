#!/usr/bin/env python3
"""
Test script for the new provider monitoring and favorites enhancements.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.provider import ProviderStatus, ProviderStatusEnum
from app.models.user import User
from app.models.library import MangaUserLibrary
from app.core.providers.registry import provider_registry
from app.core.services.provider_monitor import provider_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_provider_monitoring():
    """Test provider monitoring functionality."""
    logger.info("Testing provider monitoring...")

    async with AsyncSessionLocal() as db:
        # Initialize provider statuses
        await provider_monitor.initialize_provider_statuses(db)

        # Get all provider statuses
        result = await db.execute(select(ProviderStatus))
        statuses = result.scalars().all()

        logger.info(f"Found {len(statuses)} provider statuses:")
        for status in statuses:
            logger.info(f"  - {status.provider_name}: {status.status} (enabled: {status.is_enabled})")

        # Test a single provider
        if statuses:
            test_status = statuses[0]
            provider = provider_registry.get_provider(test_status.provider_id)

            if provider:
                logger.info(f"Testing provider: {provider.name}")
                is_healthy, response_time, error_message = await provider.health_check(timeout=10)

                logger.info(f"Health check result: healthy={is_healthy}, "
                           f"response_time={response_time}ms, error={error_message}")

                # Update status
                test_status.update_status(is_healthy, response_time, error_message)
                await db.commit()

                logger.info(f"Updated status: {test_status.status}, "
                           f"consecutive_failures={test_status.consecutive_failures}")


async def test_favorites_functionality():
    """Test favorites functionality."""
    logger.info("Testing favorites functionality...")

    async with AsyncSessionLocal() as db:
        # Get a test user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("No users found in database. Skipping favorites test.")
            return

        logger.info(f"Testing favorites for user: {user.username}")

        # Get user's favorites
        result = await db.execute(
            select(MangaUserLibrary).where(
                MangaUserLibrary.user_id == user.id,
                MangaUserLibrary.is_favorite == True
            )
        )
        favorites = result.scalars().all()

        logger.info(f"User has {len(favorites)} favorites")

        for favorite in favorites[:3]:  # Show first 3
            logger.info(f"  - Favorite manga ID: {favorite.manga_id}")


async def test_provider_registry_info():
    """Test enhanced provider registry info."""
    logger.info("Testing enhanced provider registry info...")

    async with AsyncSessionLocal() as db:
        # Get provider info from registry
        provider_info_list = provider_registry.get_provider_info()

        # Get provider statuses from database
        result = await db.execute(select(ProviderStatus))
        provider_statuses = {ps.provider_id: ps for ps in result.scalars().all()}

        logger.info(f"Found {len(provider_info_list)} providers in registry")
        logger.info(f"Found {len(provider_statuses)} provider statuses in database")

        # Show enhanced provider info
        for provider_info in provider_info_list[:5]:  # Show first 5
            provider_id = provider_info["id"]
            status_record = provider_statuses.get(provider_id)

            status = status_record.status if status_record else "unknown"
            is_healthy = status_record.is_healthy if status_record else True
            uptime = status_record.uptime_percentage if status_record else 100

            logger.info(f"  - {provider_info['name']}: status={status}, "
                       f"healthy={is_healthy}, uptime={uptime}%")


async def test_provider_statistics():
    """Test provider statistics functionality."""
    logger.info("Testing provider statistics...")

    async with AsyncSessionLocal() as db:
        # Get provider statistics
        result = await db.execute(select(ProviderStatus))
        statuses = result.scalars().all()

        if not statuses:
            logger.warning("No provider statuses found. Skipping statistics test.")
            return

        total_providers = len(statuses)
        active_providers = len([s for s in statuses if s.status == "active"])
        down_providers = len([s for s in statuses if s.status == "down"])
        unknown_providers = len([s for s in statuses if s.status == "unknown"])
        enabled_providers = len([s for s in statuses if s.is_enabled])

        # Calculate average uptime
        avg_uptime = sum(s.uptime_percentage for s in statuses) / total_providers if total_providers > 0 else 0

        logger.info(f"Provider Statistics:")
        logger.info(f"  Total: {total_providers}")
        logger.info(f"  Active: {active_providers}")
        logger.info(f"  Down: {down_providers}")
        logger.info(f"  Unknown: {unknown_providers}")
        logger.info(f"  Enabled: {enabled_providers}")
        logger.info(f"  Average Uptime: {avg_uptime:.2f}%")


async def test_favorites_search_and_sort():
    """Test favorites search and sorting functionality."""
    logger.info("Testing favorites search and sorting...")

    async with AsyncSessionLocal() as db:
        # Get a test user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("No users found in database. Skipping favorites search test.")
            return

        # Test different sorting options
        sort_options = ["updated_at", "created_at", "title", "rating"]

        for sort_by in sort_options:
            try:
                # Build query with sorting
                query = select(MangaUserLibrary).where(
                    MangaUserLibrary.user_id == user.id,
                    MangaUserLibrary.is_favorite == True
                )

                # Add sorting
                sort_column = getattr(MangaUserLibrary, sort_by, None)
                if sort_by == "title":
                    # Would need to join with Manga table
                    logger.info(f"  Sort by {sort_by}: Would require Manga join")
                    continue
                elif sort_column is None:
                    sort_column = MangaUserLibrary.updated_at

                query = query.order_by(sort_column.desc()).limit(5)
                result = await db.execute(query)
                favorites = result.scalars().all()

                logger.info(f"  Sort by {sort_by}: Found {len(favorites)} favorites")

            except Exception as e:
                logger.warning(f"  Sort by {sort_by}: Error - {e}")


async def main():
    """Main test function."""
    logger.info("Starting comprehensive enhancement tests...")

    try:
        await test_provider_monitoring()
        await test_favorites_functionality()
        await test_provider_registry_info()
        await test_provider_statistics()
        await test_favorites_search_and_sort()

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
