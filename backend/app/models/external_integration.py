"""External integration models for Anilist, MyAnimeList, etc."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class IntegrationType(str, Enum):
    """Supported external integration types."""

    ANILIST = "anilist"
    MYANIMELIST = "myanimelist"
    KITSU = "kitsu"


class SyncStatus(str, Enum):
    """Sync status for external integrations."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    DISABLED = "disabled"


class ExternalIntegration(BaseModel):
    """External integration model for storing user's connected accounts."""

    __tablename__ = "external_integrations"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    integration_type = Column(SQLEnum(IntegrationType), nullable=False)

    # API credentials (stored encrypted)
    client_id = Column(Text, nullable=True)  # OAuth client ID
    client_secret = Column(Text, nullable=True)  # OAuth client secret (encrypted)

    # Authentication data
    access_token = Column(Text, nullable=True)  # Encrypted access token
    refresh_token = Column(Text, nullable=True)  # Encrypted refresh token
    token_expires_at = Column(DateTime, nullable=True)

    # External account info
    external_user_id = Column(String(100), nullable=True)
    external_username = Column(String(100), nullable=True)

    # Sync settings
    sync_enabled = Column(Boolean, default=True, nullable=False)
    sync_reading_progress = Column(Boolean, default=True, nullable=False)
    sync_ratings = Column(Boolean, default=True, nullable=False)
    sync_status = Column(
        Boolean, default=True, nullable=False
    )  # reading/completed/dropped status
    auto_sync = Column(Boolean, default=True, nullable=False)  # Auto sync on changes

    # Sync tracking
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(
        SQLEnum(SyncStatus), default=SyncStatus.PENDING, nullable=False
    )
    last_sync_error = Column(Text, nullable=True)
    sync_count = Column(Integer, default=0, nullable=False)

    # Additional settings stored as JSON
    settings = Column(JSONB, nullable=True)

    # Relationships
    user = relationship("User", back_populates="external_integrations")
    manga_mappings = relationship(
        "ExternalMangaMapping",
        back_populates="integration",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", "integration_type", name="uq_user_integration_type"
        ),
    )


class ExternalMangaMapping(BaseModel):
    """Mapping between local manga and external service manga IDs."""

    __tablename__ = "external_manga_mappings"

    integration_id = Column(
        UUID(as_uuid=True),
        ForeignKey("external_integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    manga_id = Column(
        UUID(as_uuid=True), ForeignKey("manga.id", ondelete="CASCADE"), nullable=False
    )

    # External manga identifiers
    external_manga_id = Column(String(100), nullable=False)
    external_title = Column(String(500), nullable=True)
    external_url = Column(String(500), nullable=True)

    # Sync data
    last_synced_at = Column(DateTime, nullable=True)
    sync_status = Column(
        SQLEnum(SyncStatus), default=SyncStatus.PENDING, nullable=False
    )
    sync_error = Column(Text, nullable=True)

    # External data cache (to avoid frequent API calls)
    external_data = Column(JSONB, nullable=True)

    # Relationships
    integration = relationship("ExternalIntegration", back_populates="manga_mappings")
    manga = relationship("Manga")

    # Constraints
    __table_args__ = (
        UniqueConstraint("integration_id", "manga_id", name="uq_integration_manga"),
        UniqueConstraint(
            "integration_id", "external_manga_id", name="uq_integration_external_manga"
        ),
    )
