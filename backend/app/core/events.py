import logging
from typing import Callable

from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.config import settings
from app.core.deps import set_redis_client
from app.db.session import engine
from app.db.init_db import init_db

logger = logging.getLogger(__name__)


def startup_event_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        # Set up Redis connection
        try:
            redis_kwargs = {
                "host": settings.VALKEY_HOST,
                "port": settings.VALKEY_PORT,
                "db": settings.VALKEY_DB,
                "decode_responses": True,
            }

            # Only add password if it's configured
            if settings.VALKEY_PASSWORD:
                redis_kwargs["password"] = settings.VALKEY_PASSWORD

            redis = Redis(**redis_kwargs)

            # Test the connection
            await redis.ping()

            app.state.redis = redis
            # Set global Redis client for dependencies
            set_redis_client(redis)
            logger.info("Redis connection established successfully")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Token blacklisting will be disabled.")
            app.state.redis = None
            set_redis_client(None)

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
        if hasattr(app.state, "redis") and app.state.redis:
            try:
                await app.state.redis.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")

        # Close database connections
        await engine.dispose()
        logger.info("Database connections closed")

        logger.info("Application shutdown complete")

    return stop_app
