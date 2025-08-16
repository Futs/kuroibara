"""
Job queue events and status definitions.

This module defines the core data structures for job queue management
including job statuses, priorities, types, and events.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class JobStatus(Enum):
    """Status of a job in the queue."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(Enum):
    """Priority levels for jobs."""

    CRITICAL = 1  # System-critical jobs (health checks, backups)
    HIGH = 2  # User-requested immediate downloads
    NORMAL = 3  # Regular downloads
    LOW = 4  # Background organization, cleanup
    BULK = 5  # Bulk operations (lowest priority)


class JobType(Enum):
    """Types of jobs that can be queued."""

    # Download jobs
    DOWNLOAD_CHAPTER = "download_chapter"
    DOWNLOAD_MANGA = "download_manga"
    DOWNLOAD_COVER = "download_cover"
    DOWNLOAD_PAGE = "download_page"
    BULK_DOWNLOAD = "bulk_download"

    # Health monitoring jobs
    HEALTH_CHECK = "health_check"
    PROVIDER_TEST = "provider_test"
    PERFORMANCE_BENCHMARK = "performance_benchmark"

    # Organization jobs
    ORGANIZE_LIBRARY = "organize_library"
    ORGANIZE_MANGA = "organize_manga"
    CONVERT_FORMAT = "convert_format"
    CLEANUP_FILES = "cleanup_files"

    # System jobs
    BACKUP_DATABASE = "backup_database"
    MIGRATE_DATA = "migrate_data"
    UPDATE_METADATA = "update_metadata"


class JobEventType(Enum):
    """Types of job events."""

    CREATED = "created"
    QUEUED = "queued"
    STARTED = "started"
    PROGRESS = "progress"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    WARNING = "warning"


@dataclass
class JobEvent:
    """
    A single job event with detailed information.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    job_type: JobType = JobType.DOWNLOAD_CHAPTER
    event_type: JobEventType = JobEventType.PROGRESS

    # Event details
    message: str = ""
    error_message: Optional[str] = None
    warning_message: Optional[str] = None

    # Progress information
    progress_percentage: float = 0.0
    current_step: str = ""
    items_processed: int = 0
    items_total: Optional[int] = None

    # Metadata and context
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # User and session context
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "event_type": self.event_type.value,
            "message": self.message,
            "error_message": self.error_message,
            "warning_message": self.warning_message,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobEvent":
        """Create event from dictionary."""
        event = cls()
        event.id = data.get("id", str(uuid.uuid4()))
        event.job_id = data.get("job_id", "")
        event.job_type = JobType(data.get("job_type", "download_chapter"))
        event.event_type = JobEventType(data.get("event_type", "progress"))
        event.message = data.get("message", "")
        event.error_message = data.get("error_message")
        event.warning_message = data.get("warning_message")
        event.progress_percentage = data.get("progress_percentage", 0.0)
        event.current_step = data.get("current_step", "")
        event.items_processed = data.get("items_processed", 0)
        event.items_total = data.get("items_total")
        event.metadata = data.get("metadata", {})
        event.timestamp = datetime.fromisoformat(
            data.get("timestamp", datetime.utcnow().isoformat())
        )
        event.user_id = data.get("user_id")
        event.session_id = data.get("session_id")
        return event


# Job priority mappings for different scenarios
PRIORITY_MAPPINGS = {
    # User-initiated downloads get higher priority
    "user_download": JobPriority.HIGH,
    "user_bulk_download": JobPriority.NORMAL,
    # System operations
    "health_check": JobPriority.CRITICAL,
    "backup": JobPriority.CRITICAL,
    "migration": JobPriority.HIGH,
    # Background operations
    "organization": JobPriority.LOW,
    "cleanup": JobPriority.LOW,
    "metadata_update": JobPriority.LOW,
    # Bulk operations
    "bulk_organization": JobPriority.BULK,
    "bulk_conversion": JobPriority.BULK,
}


def get_job_priority(job_type: JobType, context: str = "default") -> JobPriority:
    """
    Get appropriate priority for a job based on type and context.

    Args:
        job_type: Type of job
        context: Context for priority determination

    Returns:
        Appropriate job priority
    """
    # Check context-specific mappings first
    if context in PRIORITY_MAPPINGS:
        return PRIORITY_MAPPINGS[context]

    # Default mappings based on job type
    if job_type in [JobType.HEALTH_CHECK, JobType.BACKUP_DATABASE]:
        return JobPriority.CRITICAL
    elif job_type in [JobType.DOWNLOAD_CHAPTER, JobType.DOWNLOAD_COVER]:
        return JobPriority.HIGH
    elif job_type in [JobType.DOWNLOAD_MANGA, JobType.BULK_DOWNLOAD]:
        return JobPriority.NORMAL
    elif job_type in [JobType.ORGANIZE_LIBRARY, JobType.CLEANUP_FILES]:
        return JobPriority.LOW
    else:
        return JobPriority.NORMAL


def is_download_job(job_type: JobType) -> bool:
    """Check if a job type is a download job."""
    return job_type in [
        JobType.DOWNLOAD_CHAPTER,
        JobType.DOWNLOAD_MANGA,
        JobType.DOWNLOAD_COVER,
        JobType.DOWNLOAD_PAGE,
        JobType.BULK_DOWNLOAD,
    ]


def is_health_job(job_type: JobType) -> bool:
    """Check if a job type is a health monitoring job."""
    return job_type in [
        JobType.HEALTH_CHECK,
        JobType.PROVIDER_TEST,
        JobType.PERFORMANCE_BENCHMARK,
    ]


def is_organization_job(job_type: JobType) -> bool:
    """Check if a job type is an organization job."""
    return job_type in [
        JobType.ORGANIZE_LIBRARY,
        JobType.ORGANIZE_MANGA,
        JobType.CONVERT_FORMAT,
        JobType.CLEANUP_FILES,
    ]


def is_system_job(job_type: JobType) -> bool:
    """Check if a job type is a system job."""
    return job_type in [
        JobType.BACKUP_DATABASE,
        JobType.MIGRATE_DATA,
        JobType.UPDATE_METADATA,
    ]


def can_job_be_paused(job_type: JobType) -> bool:
    """Check if a job type can be paused."""
    # Most jobs can be paused except critical system operations
    return job_type not in [
        JobType.HEALTH_CHECK,
        JobType.BACKUP_DATABASE,
        JobType.MIGRATE_DATA,
    ]


def can_job_be_cancelled(job_type: JobType) -> bool:
    """Check if a job type can be cancelled."""
    # Most jobs can be cancelled except critical system operations
    return job_type not in [JobType.BACKUP_DATABASE, JobType.MIGRATE_DATA]


def get_job_timeout(job_type: JobType) -> int:
    """
    Get appropriate timeout for a job type in seconds.

    Args:
        job_type: Type of job

    Returns:
        Timeout in seconds
    """
    timeouts = {
        JobType.DOWNLOAD_CHAPTER: 1800,  # 30 minutes
        JobType.DOWNLOAD_MANGA: 7200,  # 2 hours
        JobType.DOWNLOAD_COVER: 300,  # 5 minutes
        JobType.DOWNLOAD_PAGE: 120,  # 2 minutes
        JobType.BULK_DOWNLOAD: 14400,  # 4 hours
        JobType.HEALTH_CHECK: 60,  # 1 minute
        JobType.PROVIDER_TEST: 300,  # 5 minutes
        JobType.PERFORMANCE_BENCHMARK: 600,  # 10 minutes
        JobType.ORGANIZE_LIBRARY: 3600,  # 1 hour
        JobType.ORGANIZE_MANGA: 1800,  # 30 minutes
        JobType.CONVERT_FORMAT: 3600,  # 1 hour
        JobType.CLEANUP_FILES: 1800,  # 30 minutes
        JobType.BACKUP_DATABASE: 7200,  # 2 hours
        JobType.MIGRATE_DATA: 14400,  # 4 hours
        JobType.UPDATE_METADATA: 3600,  # 1 hour
    }

    return timeouts.get(job_type, 1800)  # Default 30 minutes
