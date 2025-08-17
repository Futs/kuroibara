"""
Progress event system for real-time tracking.

This module defines the core data structures for progress tracking including
events, operations, and status types.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class ProgressEventType(Enum):
    """Types of progress events."""

    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    STATUS_UPDATE = "status_update"
    STEP_COMPLETED = "step_completed"
    WARNING = "warning"
    INFO = "info"


class OperationType(Enum):
    """Types of operations that can be tracked."""

    # Search operations
    SEARCH = "search"
    SEARCH_PROVIDER = "search_provider"

    # Download operations
    DOWNLOAD_CHAPTER = "download_chapter"
    DOWNLOAD_MANGA = "download_manga"
    DOWNLOAD_COVER = "download_cover"
    DOWNLOAD_PAGE = "download_page"
    BULK_DOWNLOAD = "bulk_download"

    # Metadata operations
    METADATA_FETCH = "metadata_fetch"
    CHAPTER_LIST_FETCH = "chapter_list_fetch"
    MANGA_DETAILS_FETCH = "manga_details_fetch"

    # Library operations
    LIBRARY_SCAN = "library_scan"
    LIBRARY_IMPORT = "library_import"
    LIBRARY_ORGANIZE = "library_organize"
    LIBRARY_CLEANUP = "library_cleanup"

    # Agent operations
    AGENT_HEALTH_CHECK = "agent_health_check"
    AGENT_RATE_LIMIT_TEST = "agent_rate_limit_test"

    # System operations
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    DATABASE_MIGRATION = "database_migration"


class ProgressStatus(Enum):
    """Status of a progress operation."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WARNING = "warning"


@dataclass
class ProgressEvent:
    """
    A single progress event with detailed information.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_id: str = ""
    operation_type: OperationType = OperationType.SEARCH
    event_type: ProgressEventType = ProgressEventType.PROGRESS

    # Progress information
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: Optional[int] = None
    current_step_number: Optional[int] = None

    # Messages and metadata
    message: str = ""
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing information
    timestamp: datetime = field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None

    # Additional context
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "event_type": self.event_type.value,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "message": self.message,
            "error_message": self.error_message,
            "warning_message": self.warning_message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "user_id": self.user_id,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressEvent":
        """Create event from dictionary."""
        event = cls()
        event.id = data.get("id", str(uuid.uuid4()))
        event.operation_id = data.get("operation_id", "")
        event.operation_type = OperationType(data.get("operation_type", "search"))
        event.event_type = ProgressEventType(data.get("event_type", "progress"))
        event.progress_percentage = data.get("progress_percentage", 0.0)
        event.current_step = data.get("current_step", "")
        event.total_steps = data.get("total_steps")
        event.current_step_number = data.get("current_step_number")
        event.message = data.get("message", "")
        event.error_message = data.get("error_message")
        event.warning_message = data.get("warning_message")
        event.metadata = data.get("metadata", {})
        event.timestamp = datetime.fromisoformat(
            data.get("timestamp", datetime.utcnow().isoformat())
        )

        if data.get("estimated_completion"):
            event.estimated_completion = datetime.fromisoformat(
                data["estimated_completion"]
            )

        event.user_id = data.get("user_id")
        event.session_id = data.get("session_id")

        return event


@dataclass
class ProgressOperation:
    """
    A complete operation being tracked with progress.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: OperationType = OperationType.SEARCH
    title: str = ""
    description: str = ""

    # Status and progress
    status: ProgressStatus = ProgressStatus.PENDING
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: Optional[int] = None
    current_step_number: Optional[int] = None

    # Timing information
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    last_update: datetime = field(default_factory=datetime.utcnow)

    # Error and warning information
    error_message: Optional[str] = None
    warning_messages: List[str] = field(default_factory=list)

    # Metadata and context
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Hierarchical operations
    parent_operation_id: Optional[str] = None
    child_operations: List[str] = field(default_factory=list)

    # Performance metrics
    total_items: Optional[int] = None
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0

    # Cancellation support
    is_cancellable: bool = True
    cancellation_token: Optional[str] = None

    def calculate_progress(self) -> float:
        """Calculate progress percentage based on processed items."""
        if self.total_items and self.total_items > 0:
            return min(100.0, (self.processed_items / self.total_items) * 100.0)
        return self.progress_percentage

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the operation."""
        self.warning_messages.append(warning)
        self.last_update = datetime.utcnow()

    def update_progress(
        self,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        current_step_number: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update operation progress."""
        if progress is not None:
            self.progress_percentage = min(100.0, max(0.0, progress))

        if current_step is not None:
            self.current_step = current_step

        if current_step_number is not None:
            self.current_step_number = current_step_number

        self.last_update = datetime.utcnow()

        # Update estimated completion if we have progress
        if self.progress_percentage > 0 and self.status == ProgressStatus.RUNNING:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
            if elapsed > 0:
                total_estimated = elapsed / (self.progress_percentage / 100.0)
                remaining = total_estimated - elapsed
                if remaining > 0:
                    self.estimated_completion = datetime.utcnow() + timedelta(
                        seconds=remaining
                    )

    def mark_completed(self, message: Optional[str] = None) -> None:
        """Mark operation as completed."""
        self.status = ProgressStatus.COMPLETED
        self.progress_percentage = 100.0
        self.completed_at = datetime.utcnow()
        self.last_update = datetime.utcnow()
        if message:
            self.current_step = message

    def mark_failed(self, error_message: str) -> None:
        """Mark operation as failed."""
        self.status = ProgressStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.last_update = datetime.utcnow()

    def mark_cancelled(self) -> None:
        """Mark operation as cancelled."""
        self.status = ProgressStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.last_update = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if operation is currently active."""
        return self.status in [
            ProgressStatus.PENDING,
            ProgressStatus.RUNNING,
            ProgressStatus.PAUSED,
        ]

    def is_finished(self) -> bool:
        """Check if operation is finished (completed, failed, or cancelled)."""
        return self.status in [
            ProgressStatus.COMPLETED,
            ProgressStatus.FAILED,
            ProgressStatus.CANCELLED,
        ]

    def get_duration(self) -> Optional[float]:
        """Get operation duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.status == ProgressStatus.RUNNING:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary for serialization."""
        return {
            "id": self.id,
            "operation_type": self.operation_type.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "progress_percentage": self.calculate_progress(),
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "last_update": self.last_update.isoformat(),
            "error_message": self.error_message,
            "warning_messages": self.warning_messages,
            "metadata": self.metadata,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "parent_operation_id": self.parent_operation_id,
            "child_operations": self.child_operations,
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "is_cancellable": self.is_cancellable,
            "duration": self.get_duration(),
        }
