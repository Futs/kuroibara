"""
Progress tracking system setup and initialization.

This module handles the initialization and configuration of the progress
tracking system including connecting persistence and WebSocket services.
"""

import logging

from .persistence import persistence_service
from .tracker import progress_tracker
from .websocket import websocket_manager

logger = logging.getLogger(__name__)


def initialize_progress_system() -> bool:
    """
    Initialize the progress tracking system.

    This function connects all the components of the progress tracking system:
    - Progress tracker
    - WebSocket manager
    - Persistence service

    Returns:
        True if initialization was successful
    """
    try:
        # Connect persistence service to progress tracker
        progress_tracker.set_persistence_service(persistence_service)
        logger.info("Connected persistence service to progress tracker")

        # Connect WebSocket manager to progress tracker
        progress_tracker.set_websocket_manager(websocket_manager)
        logger.info("Connected WebSocket manager to progress tracker")

        # Start cleanup tasks
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule cleanup task
                loop.create_task(progress_tracker.start_cleanup_task())
                logger.info("Scheduled progress tracker cleanup task")
        except RuntimeError:
            # No event loop running, cleanup will be started later
            logger.debug("No event loop running, cleanup task will be started later")

        logger.info("Progress tracking system initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Error initializing progress tracking system: {e}")
        return False


def shutdown_progress_system() -> bool:
    """
    Shutdown the progress tracking system.

    This function gracefully shuts down all components of the progress
    tracking system.

    Returns:
        True if shutdown was successful
    """
    try:
        # Stop cleanup tasks
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(progress_tracker.stop_cleanup_task())
                loop.create_task(websocket_manager._stop_heartbeat())
                logger.info("Stopped progress tracking background tasks")
        except RuntimeError:
            logger.debug("No event loop running during shutdown")

        logger.info("Progress tracking system shutdown successfully")
        return True

    except Exception as e:
        logger.error(f"Error shutting down progress tracking system: {e}")
        return False


def get_progress_system_status() -> dict:
    """
    Get the status of the progress tracking system.

    Returns:
        Dictionary containing system status information
    """
    try:
        # Get progress tracker status
        all_operations = progress_tracker.get_operations()
        active_operations = progress_tracker.get_operations(active_only=True)

        # Get WebSocket status
        websocket_connections = websocket_manager.get_connection_count()

        return {
            "progress_tracker": {
                "total_operations": len(all_operations),
                "active_operations": len(active_operations),
                "event_handlers": len(progress_tracker._event_handlers),
                "websocket_handlers": len(progress_tracker._websocket_handlers),
            },
            "websocket_manager": {
                "active_connections": websocket_connections,
                "heartbeat_running": (
                    websocket_manager._heartbeat_task is not None
                    and not websocket_manager._heartbeat_task.done()
                ),
            },
            "persistence_service": {
                "available": persistence_service is not None,
                "cleanup_interval": (
                    persistence_service._cleanup_interval
                    if persistence_service
                    else None
                ),
            },
            "system_status": "operational",
        }

    except Exception as e:
        logger.error(f"Error getting progress system status: {e}")
        return {"system_status": "error", "error": str(e)}


# Auto-initialize when module is imported
_initialized = False


def ensure_initialized():
    """Ensure the progress system is initialized."""
    global _initialized
    if not _initialized:
        _initialized = initialize_progress_system()
    return _initialized
