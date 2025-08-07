import asyncio
import logging
import time
from typing import Optional

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, Base, engine
from app.models.library import (
    LibraryCategory,
)

# Import all models to ensure they are registered with Base.metadata

logger = logging.getLogger(__name__)


async def wait_for_database(max_retries: int = 30, retry_delay: float = 2.0) -> bool:
    """
    Wait for the database to become available.

    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retry attempts in seconds

    Returns:
        True if database is available, False otherwise
    """
    from sqlalchemy import text

    for attempt in range(max_retries):
        try:
            # Try to establish a connection
            async with engine.begin() as conn:
                # Simple query to test connection
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
            return True
        except (OperationalError, ConnectionRefusedError, OSError) as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {retry_delay} seconds..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"Failed to connect to database after {max_retries} attempts: {e}"
                )
                return False
        except Exception as e:
            logger.error(f"Unexpected error while connecting to database: {e}")
            return False

    return False


async def init_db() -> None:
    """Initialize the database with required tables and initial data."""
    try:
        # Wait for database to be available
        logger.info("Waiting for database to become available...")
        if not await wait_for_database():
            raise RuntimeError("Database is not available after maximum retry attempts")

        logger.info("Creating database tables...")

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Tables created successfully")

        # Wait a moment to ensure transaction is fully committed
        await asyncio.sleep(0.1)

        # Create initial data if needed
        logger.info("Creating initial data...")
        async with AsyncSessionLocal() as session:
            await create_initial_data(session)
            await session.commit()

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        import traceback

        traceback.print_exc()
        raise


async def create_initial_data(db: AsyncSession) -> None:
    """Create initial data in the database."""
    try:
        # Create default categories
        from sqlalchemy import select

        # Check if we already have categories
        logger.info("Checking for existing categories...")
        result = await db.execute(select(LibraryCategory).limit(1))
        if result.scalars().first() is None:
            logger.info("No categories found, creating default categories...")
            # Create default categories
            default_categories = [
                LibraryCategory(
                    name="Favorites", description="Your favorite manga", is_default=True
                ),
                LibraryCategory(
                    name="Reading",
                    description="Manga you are currently reading",
                    is_default=True,
                ),
                LibraryCategory(
                    name="Completed",
                    description="Manga you have completed",
                    is_default=True,
                ),
                LibraryCategory(
                    name="On Hold",
                    description="Manga you have put on hold",
                    is_default=True,
                ),
                LibraryCategory(
                    name="Dropped",
                    description="Manga you have dropped",
                    is_default=True,
                ),
                LibraryCategory(
                    name="Plan to Read",
                    description="Manga you plan to read",
                    is_default=True,
                ),
            ]

            db.add_all(default_categories)
            await db.flush()

            logger.info("Created default categories")
        else:
            logger.info("Categories already exist, skipping creation")
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        import traceback

        traceback.print_exc()
        raise
