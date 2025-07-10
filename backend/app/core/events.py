import asyncio
import logging
from typing import Callable

from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.config import settings
from app.core.deps import set_redis_client
from app.core.services.backup import scheduled_backup_service
from app.core.services.provider_monitor import provider_monitor
from app.db.init_db import init_db
from app.db.session import engine

logger = logging.getLogger(__name__)


def startup_event_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        # Initialize greenlet context for SQLAlchemy async operations
        try:
            import greenlet

            # Ensure greenlet context is properly initialized
            if not hasattr(greenlet.getcurrent(), "_greenlet_spawn_called"):
                greenlet.getcurrent()._greenlet_spawn_called = True
            logger.info("Greenlet context initialized")
        except ImportError:
            logger.warning("Greenlet not available - some async operations may fail")
        except Exception as e:
            logger.warning(f"Error initializing greenlet context: {e}")
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
            logger.warning(
                f"Redis connection failed: {e}. Token blacklisting will be disabled."
            )
            app.state.redis = None
            set_redis_client(None)

        # Initialize database if needed (only if enabled)
        if settings.ENABLE_DB_INIT:
            try:
                await init_db()
                logger.info("Database initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing database: {e}")
                raise
        else:
            logger.info("Database initialization disabled by configuration")

        # Initialize and test providers (only if enabled)
        if settings.ENABLE_PROVIDER_MONITORING:
            try:
                await provider_monitor.test_all_providers_on_startup()
                await provider_monitor.start_monitoring()
                logger.info("Provider monitoring initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing provider monitoring: {e}")
                # Don't raise here as provider monitoring is not critical for app startup
        else:
            logger.info("Provider monitoring disabled by configuration")

        # Start backup scheduler
        try:
            scheduled_backup_service.start()
            logger.info("Backup scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting backup scheduler: {e}")
            # Don't raise here as backup scheduling is not critical for app startup

        logger.info("Application startup complete")

    return start_app


def shutdown_event_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        # Stop backup scheduler
        try:
            scheduled_backup_service.stop()
            logger.info("Backup scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping backup scheduler: {e}")

        # Stop provider monitoring
        try:
            await provider_monitor.stop_monitoring()
            logger.info("Provider monitoring stopped")
        except Exception as e:
            logger.warning(f"Error stopping provider monitoring: {e}")

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
