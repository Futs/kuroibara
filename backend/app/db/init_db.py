import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, Base, engine
from app.core.config import settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize the database with required tables and initial data."""
    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create initial data if needed
        async with AsyncSessionLocal() as session:
            await create_initial_data(session)
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def create_initial_data(db: AsyncSession) -> None:
    """Create initial data in the database."""
    # Create default categories
    from app.models.category import Category
    from sqlalchemy import select
    
    # Check if we already have categories
    result = await db.execute(select(Category).limit(1))
    if result.scalars().first() is None:
        # Create default categories
        default_categories = [
            Category(name="Favorites", description="Your favorite manga", is_default=True),
            Category(name="Reading", description="Manga you are currently reading", is_default=True),
            Category(name="Completed", description="Manga you have completed", is_default=True),
            Category(name="On Hold", description="Manga you have put on hold", is_default=True),
            Category(name="Dropped", description="Manga you have dropped", is_default=True),
            Category(name="Plan to Read", description="Manga you plan to read", is_default=True),
        ]
        
        db.add_all(default_categories)
        await db.flush()
        
        logger.info("Created default categories")
