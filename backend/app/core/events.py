import logging
from typing import Callable

from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.config import settings
from app.db.session import engine
from app.db.init_db import init_db

logger = logging.getLogger(__name__)


def startup_event_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        # Set up Redis connection
        app.state.redis = Redis(
            host=settings.VALKEY_HOST,
            port=settings.VALKEY_PORT,
            password=settings.VALKEY_PASSWORD,
            db=settings.VALKEY_DB,
            decode_responses=True,
        )
        
        # Initialize database if needed
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

        logger.info("Application startup complete")

    return start_app


def shutdown_event_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        # Close Redis connection
        if hasattr(app.state, "redis"):
            await app.state.redis.close()
            logger.info("Redis connection closed")

        # Close database connections
        await engine.dispose()
        logger.info("Database connections closed")

        logger.info("Application shutdown complete")

    return stop_app
