"""
Job models for the queue system.

This module defines the core job classes for different types of operations
including downloads, health checks, and organization tasks.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .events import JobPriority, JobStatus, JobType, get_job_timeout


@dataclass
class BaseJob:
    """
    Base class for all jobs in the queue system.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType = JobType.DOWNLOAD_CHAPTER
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL

    # Job metadata
    title: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Progress tracking
    progress_percentage: float = 0.0
    current_step: str = ""
    items_processed: int = 0
    items_total: Optional[int] = None

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # User and session context
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Job configuration
    timeout_seconds: int = field(default=1800)  # 30 minutes default
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Dependencies and relationships
    parent_job_id: Optional[str] = None
    child_job_ids: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize job after creation."""
        if self.timeout_seconds == 1800:  # If using default
            self.timeout_seconds = get_job_timeout(self.job_type)

    def update_progress(
        self,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        items_processed: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update job progress."""
        if progress is not None:
            self.progress_percentage = min(100.0, max(0.0, progress))

        if current_step is not None:
            self.current_step = current_step

        if items_processed is not None:
            self.items_processed = items_processed

        self.updated_at = datetime.utcnow()

        # Calculate progress from items if available
        if self.items_total and self.items_total > 0:
            calculated_progress = (self.items_processed / self.items_total) * 100.0
            self.progress_percentage = min(100.0, calculated_progress)

    def mark_started(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_completed(self, message: Optional[str] = None) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.progress_percentage = 100.0
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if message:
            self.current_step = message

    def mark_failed(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_paused(self) -> None:
        """Mark job as paused."""
        self.status = JobStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def mark_resumed(self) -> None:
        """Mark job as resumed."""
        self.status = JobStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def increment_retry(self) -> bool:
        """
        Increment retry count and check if more retries are allowed.

        Returns:
            True if more retries are allowed
        """
        self.retry_count += 1
        if self.retry_count <= self.max_retries:
            self.status = JobStatus.RETRYING
            self.updated_at = datetime.utcnow()
            return True
        else:
            self.mark_failed(f"Max retries ({self.max_retries}) exceeded")
            return False

    def is_active(self) -> bool:
        """Check if job is currently active."""
        return self.status in [
            JobStatus.PENDING,
            JobStatus.PROCESSING,
            JobStatus.RETRYING,
        ]

    def is_finished(self) -> bool:
        """Check if job is finished."""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    def is_timed_out(self) -> bool:
        """Check if job has timed out."""
        if not self.started_at:
            return False

        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return elapsed > self.timeout_seconds

    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at and self.status == JobStatus.PROCESSING:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None

    def get_estimated_completion(self) -> Optional[datetime]:
        """Get estimated completion time based on progress."""
        if not self.started_at or self.progress_percentage <= 0:
            return None

        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        total_estimated = elapsed / (self.progress_percentage / 100.0)
        remaining = total_estimated - elapsed

        if remaining > 0:
            return datetime.utcnow() + timedelta(seconds=remaining)

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            "id": self.id,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "updated_at": self.updated_at.isoformat(),
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
            "parent_job_id": self.parent_job_id,
            "child_job_ids": self.child_job_ids,
            "depends_on": self.depends_on,
            "duration": self.get_duration(),
            "estimated_completion": (
                self.get_estimated_completion().isoformat()
                if self.get_estimated_completion()
                else None
            ),
        }


@dataclass
class DownloadJob(BaseJob):
    """
    Job for downloading manga content.
    """

    job_type: JobType = JobType.DOWNLOAD_CHAPTER

    # Download-specific fields
    provider_name: str = ""
    manga_id: Optional[str] = None
    chapter_id: Optional[str] = None
    external_manga_id: str = ""
    external_chapter_id: str = ""
    download_path: str = ""

    # Download configuration
    quality: str = "high"  # high, medium, low
    format: str = "cbz"  # cbz, pdf, images
    overwrite_existing: bool = False

    def __post_init__(self):
        super().__post_init__()
        if not self.title:
            if self.job_type == JobType.DOWNLOAD_CHAPTER:
                self.title = f"Download Chapter from {self.provider_name}"
            elif self.job_type == JobType.DOWNLOAD_MANGA:
                self.title = f"Download Manga from {self.provider_name}"
            elif self.job_type == JobType.DOWNLOAD_COVER:
                self.title = f"Download Cover from {self.provider_name}"


@dataclass
class HealthCheckJob(BaseJob):
    """
    Job for provider health monitoring.
    """

    job_type: JobType = JobType.HEALTH_CHECK
    priority: JobPriority = JobPriority.CRITICAL

    # Health check specific fields
    provider_name: str = ""
    check_type: str = "basic"  # basic, comprehensive, performance
    timeout_override: Optional[int] = None

    # Health check configuration
    test_search: bool = True
    test_download: bool = False
    test_metadata: bool = True
    performance_benchmark: bool = False

    def __post_init__(self):
        super().__post_init__()
        if not self.title:
            self.title = f"Health Check: {self.provider_name}"

        if self.timeout_override:
            self.timeout_seconds = self.timeout_override


@dataclass
class OrganizationJob(BaseJob):
    """
    Job for library organization tasks.
    """

    job_type: JobType = JobType.ORGANIZE_LIBRARY
    priority: JobPriority = JobPriority.LOW

    # Organization specific fields
    target_path: str = ""
    organization_type: str = "by_series"  # by_series, by_author, by_genre, custom

    # Organization configuration
    create_folders: bool = True
    move_files: bool = False  # False = copy, True = move
    update_metadata: bool = True
    cleanup_empty_folders: bool = True

    def __post_init__(self):
        super().__post_init__()
        if not self.title:
            self.title = f"Organize Library: {self.organization_type}"
