import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal, Base, engine
from app.models.library import (
    Bookmark,
    LibraryCategory,
    MangaUserLibrary,
    ReadingList,
    ReadingProgress,
)
from app.models.manga import Chapter, Manga
from app.models.provider import ProviderStatus

# Import all models to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.user_provider_preference import UserProviderPreference

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize the database with required tables and initial data."""
    try:
        logger.info("Creating database tables...")

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Tables created successfully")

        # Wait a moment to ensure transaction is fully committed
        import asyncio

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
