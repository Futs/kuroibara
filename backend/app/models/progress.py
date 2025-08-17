"""
Database models for progress tracking.

This module defines SQLAlchemy models for persisting progress operations
and events to the database.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

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


class ProgressOperationModel(Base):
    """Database model for progress operations."""

    __tablename__ = "progress_operations"

    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Operation identification
    operation_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Status and progress
    status = Column(String(20), nullable=False, default="pending", index=True)
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(255))
    total_steps = Column(Integer)
    current_step_number = Column(Integer)

    # Timing information
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, index=True)
    estimated_completion = Column(DateTime)
    last_update = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Error and warning information
    error_message = Column(Text)
    warning_messages = Column(JSON)  # List of warning messages

    # Metadata and context
    operation_metadata = Column(JSON)  # Additional operation metadata
    user_id = Column(PostgresUUID(as_uuid=True), index=True)
    session_id = Column(String(255), index=True)

    # Hierarchical operations
    parent_operation_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("progress_operations.id"), index=True
    )

    # Performance metrics
    total_items = Column(Integer)
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Cancellation support
    is_cancellable = Column(Boolean, default=True)
    cancellation_token = Column(String(255))

    # Relationships
    parent_operation = relationship(
        "ProgressOperationModel", remote_side=[id], backref="child_operations"
    )
    events = relationship(
        "ProgressEventModel", back_populates="operation", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_progress_operations_user_status", "user_id", "status"),
        Index("idx_progress_operations_session_status", "session_id", "status"),
        Index("idx_progress_operations_type_status", "operation_type", "status"),
        Index("idx_progress_operations_started_at", "started_at"),
        Index("idx_progress_operations_last_update", "last_update"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "operation_type": self.operation_type,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "error_message": self.error_message,
            "warning_messages": self.warning_messages or [],
            "metadata": self.operation_metadata or {},
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "parent_operation_id": (
                str(self.parent_operation_id) if self.parent_operation_id else None
            ),
            "total_items": self.total_items,
            "processed_items": self.processed_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "is_cancellable": self.is_cancellable,
            "cancellation_token": self.cancellation_token,
            "duration": self.get_duration(),
        }

    def get_duration(self) -> Optional[float]:
        """Get operation duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.status == "running" and self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None


class ProgressEventModel(Base):
    """Database model for progress events."""

    __tablename__ = "progress_events"

    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event identification
    operation_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("progress_operations.id"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(20), nullable=False, index=True)

    # Progress information
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(255))
    total_steps = Column(Integer)
    current_step_number = Column(Integer)

    # Messages and metadata
    message = Column(Text)
    error_message = Column(Text)
    warning_message = Column(Text)
    event_metadata = Column(JSON)

    # Timing information
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    estimated_completion = Column(DateTime)

    # Additional context
    user_id = Column(PostgresUUID(as_uuid=True), index=True)
    session_id = Column(String(255), index=True)

    # Relationships
    operation = relationship("ProgressOperationModel", back_populates="events")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_progress_events_operation_timestamp", "operation_id", "timestamp"),
        Index("idx_progress_events_user_timestamp", "user_id", "timestamp"),
        Index("idx_progress_events_session_timestamp", "session_id", "timestamp"),
        Index("idx_progress_events_type_timestamp", "event_type", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "operation_id": str(self.operation_id),
            "event_type": self.event_type,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_step_number": self.current_step_number,
            "message": self.message,
            "error_message": self.error_message,
            "warning_message": self.warning_message,
            "metadata": self.event_metadata or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
        }


class ProgressSessionModel(Base):
    """Database model for progress tracking sessions."""

    __tablename__ = "progress_sessions"

    # Primary key
    id = Column(String(255), primary_key=True)  # Session ID

    # Session information
    user_id = Column(PostgresUUID(as_uuid=True), index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_activity = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )
    is_active = Column(Boolean, default=True, index=True)

    # Session metadata
    client_info = Column(JSON)  # Browser, IP, etc.
    session_metadata = Column(JSON)

    # Indexes
    __table_args__ = (
        Index("idx_progress_sessions_user_active", "user_id", "is_active"),
        Index("idx_progress_sessions_last_activity", "last_activity"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "is_active": self.is_active,
            "client_info": self.client_info or {},
            "metadata": self.session_metadata or {},
        }
