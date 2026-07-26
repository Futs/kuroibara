"""
Database models for download tasks.

This module defines the DownloadTask model for managing the persistent download queue,
tracking progress, retries, and metadata for manga and chapter downloads.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.db.session import Base


class DownloadTask(Base):
    """Database model for download tasks."""

    __tablename__ = "download_tasks"

    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Task identification
    manga_id = Column(PostgresUUID(as_uuid=True), index=True)
    chapter_id = Column(PostgresUUID(as_uuid=True), index=True)
    provider_name = Column(String(100), index=True)
    external_manga_id = Column(String(255))
    external_chapter_id = Column(String(255))

    # Status and progress
    status = Column(String(20), nullable=False, default="queued", index=True)
    priority = Column(
        Integer, nullable=False, default=3, index=True
    )  # 1: High, 2: Medium, 3: Low
    progress_percentage = Column(Float, default=0.0)
    downloaded_pages = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    downloaded_bytes = Column(Integer, default=0)
    total_bytes = Column(Integer, default=0)

    # Timing and persistence
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    started_at = Column(DateTime(timezone=True), index=True)
    completed_at = Column(DateTime(timezone=True), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)

    # Storage info
    download_path = Column(Text)

    # Metadata
    metadata = Column(Text)  # JSON string or similar for extra info

    # Indexes
    __table_args__ = (
        Index("idx_download_tasks_status", "status"),
        Index("idx_download_tasks_manga", "manga_id"),
        Index("idx_download_tasks_priority", "priority"),
        Index("idx_download_tasks_created_at", "created_at"),
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "manga_id": str(self.manga_id) if self.manga_id else None,
            "chapter_id": str(self.chapter_id) if self.chapter_id else None,
            "provider_name": self.provider_name,
            "status": self.status,
            "priority": self.priority,
            "progress_percentage": self.progress_percentage,
            "downloaded_pages": self.downloaded_pages,
            "total_pages": self.total_pages,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "download_path": self.download_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
