# Progress tracking system for Kuroibara
from .events import (
    OperationType,
    ProgressEvent,
    ProgressEventType,
    ProgressOperation,
    ProgressStatus,
)
from .persistence import ProgressPersistenceService, persistence_service
from .setup import (
    ensure_initialized,
    get_progress_system_status,
    initialize_progress_system,
    shutdown_progress_system,
)
from .tracker import ProgressTracker, progress_tracker
from .websocket import WebSocketManager, websocket_manager

# Auto-initialize the system
ensure_initialized()

__all__ = [
    "ProgressEvent",
    "ProgressOperation",
    "ProgressEventType",
    "OperationType",
    "ProgressStatus",
    "ProgressTracker",
    "progress_tracker",
    "WebSocketManager",
    "websocket_manager",
    "ProgressPersistenceService",
    "persistence_service",
    "initialize_progress_system",
    "shutdown_progress_system",
    "get_progress_system_status",
    "ensure_initialized",
]
