"""
Database models for job queue system.

This module defines SQLAlchemy models for persisting job queue operations,
events, and health monitoring data.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class JobModel(Base):
    """Database model for jobs."""

    __tablename__ = "jobs"

    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Job identification
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    priority = Column(
        Integer, nullable=False, default=3, index=True
    )  # JobPriority enum value

    # Job metadata
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Timing information
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, index=True)
    completed_at = Column(DateTime, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(255))
    items_processed = Column(Integer, default=0)
    items_total = Column(Integer)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # User and session context
    user_id = Column(PostgresUUID(as_uuid=True), index=True)
    session_id = Column(String(255), index=True)

    # Job configuration
    timeout_seconds = Column(Integer, default=1800)
    job_metadata = Column(JSON)  # Job-specific metadata

    # Dependencies and relationships
    parent_job_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("jobs.id"), index=True
    )

    # Job-specific fields (for different job types)
    provider_name = Column(String(100), index=True)  # For download/health jobs
    manga_id = Column(PostgresUUID(as_uuid=True), index=True)
    chapter_id = Column(PostgresUUID(as_uuid=True), index=True)
    external_manga_id = Column(String(255))
    external_chapter_id = Column(String(255))
    download_path = Column(Text)
    quality = Column(String(20))
    format = Column(String(20))

    # Health check specific
    check_type = Column(String(50))
    test_search = Column(Boolean, default=True)
    test_metadata = Column(Boolean, default=True)
    test_download = Column(Boolean, default=False)
    performance_benchmark = Column(Boolean, default=False)

    # Organization specific
    target_path = Column(Text)
    organization_type = Column(String(50))
    create_folders = Column(Boolean, default=True)
    move_files = Column(Boolean, default=False)

    # Relationships
    parent_job = relationship("JobModel", remote_side=[id], backref="child_jobs")
    events = relationship(
        "JobEventModel", back_populates="job", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_jobs_user_status", "user_id", "status"),
        Index("idx_jobs_session_status", "session_id", "status"),
        Index("idx_jobs_type_status", "job_type", "status"),
        Index("idx_jobs_provider_status", "provider_name", "status"),
        Index("idx_jobs_created_at", "created_at"),
        Index("idx_jobs_priority_created", "priority", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "job_type": self.job_type,
            "status": self.status,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.job_metadata or {},
            "parent_job_id": str(self.parent_job_id) if self.parent_job_id else None,
            "provider_name": self.provider_name,
            "manga_id": str(self.manga_id) if self.manga_id else None,
            "chapter_id": str(self.chapter_id) if self.chapter_id else None,
            "external_manga_id": self.external_manga_id,
            "external_chapter_id": self.external_chapter_id,
            "download_path": self.download_path,
            "quality": self.quality,
            "format": self.format,
            "check_type": self.check_type,
            "test_search": self.test_search,
            "test_metadata": self.test_metadata,
            "test_download": self.test_download,
            "performance_benchmark": self.performance_benchmark,
            "target_path": self.target_path,
            "organization_type": self.organization_type,
            "create_folders": self.create_folders,
            "move_files": self.move_files,
            "duration": self.get_duration(),
        }

    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.status == "processing" and self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None


class JobEventModel(Base):
    """Database model for job events."""

    __tablename__ = "job_events"

    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event identification
    job_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    event_type = Column(String(20), nullable=False, index=True)

    # Event details
    message = Column(Text)
    error_message = Column(Text)
    warning_message = Column(Text)

    # Progress information
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(255))
    items_processed = Column(Integer, default=0)
    items_total = Column(Integer)

    # Metadata and context
    event_metadata = Column(JSON)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # User and session context
    user_id = Column(PostgresUUID(as_uuid=True), index=True)
    session_id = Column(String(255), index=True)

    # Relationships
    job = relationship("JobModel", back_populates="events")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_job_events_job_timestamp", "job_id", "timestamp"),
        Index("idx_job_events_user_timestamp", "user_id", "timestamp"),
        Index("idx_job_events_session_timestamp", "session_id", "timestamp"),
        Index("idx_job_events_type_timestamp", "event_type", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "job_id": str(self.job_id),
            "event_type": self.event_type,
            "message": self.message,
            "error_message": self.error_message,
            "warning_message": self.warning_message,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "metadata": self.event_metadata or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
        }


class ProviderHealthModel(Base):
    """Database model for provider health metrics."""

    __tablename__ = "provider_health"

    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Provider identification
    provider_name = Column(String(100), nullable=False, unique=True, index=True)

    # Health status
    status = Column(String(20), nullable=False, default="unknown", index=True)
    last_check = Column(DateTime, index=True)
    last_success = Column(DateTime, index=True)
    last_failure = Column(DateTime, index=True)

    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    requests_per_minute = Column(Float, default=0.0)

    # Error tracking
    consecutive_failures = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    total_successes = Column(Integer, default=0)

    # Status tracking
    status_changed_at = Column(DateTime, index=True)
    auto_disabled = Column(Boolean, default=False)
    manual_override = Column(Boolean, default=False)

    # Health check history (JSON array of recent checks)
    recent_checks = Column(JSON)

    # Metadata
    health_metadata = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Indexes
    __table_args__ = (
        Index("idx_provider_health_status", "status"),
        Index("idx_provider_health_last_check", "last_check"),
        Index("idx_provider_health_updated", "updated_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "provider_name": self.provider_name,
            "status": self.status,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_success": (
                self.last_success.isoformat() if self.last_success else None
            ),
            "last_failure": (
                self.last_failure.isoformat() if self.last_failure else None
            ),
            "average_response_time": self.average_response_time,
            "success_rate": self.success_rate,
            "requests_per_minute": self.requests_per_minute,
            "consecutive_failures": self.consecutive_failures,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "status_changed_at": (
                self.status_changed_at.isoformat() if self.status_changed_at else None
            ),
            "auto_disabled": self.auto_disabled,
            "manual_override": self.manual_override,
            "recent_checks": self.recent_checks or [],
            "metadata": self.health_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
