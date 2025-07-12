"""External integration schemas for API requests and responses."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.external_integration import IntegrationType, SyncStatus
from app.schemas.base import BaseSchema


# Base schemas
class ExternalIntegrationBase(BaseModel):
    """Base external integration schema."""

    model_config = ConfigDict(from_attributes=True)

    integration_type: IntegrationType
    sync_enabled: bool = True
    sync_reading_progress: bool = True
    sync_ratings: bool = True
    sync_status: bool = True
    auto_sync: bool = True


class ExternalIntegrationCreate(ExternalIntegrationBase):
    """Schema for creating external integrations."""

    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    external_user_id: Optional[str] = None
    external_username: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ExternalIntegrationUpdate(BaseModel):
    """Schema for updating external integrations."""

    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    sync_enabled: Optional[bool] = None
    sync_reading_progress: Optional[bool] = None
    sync_ratings: Optional[bool] = None
    sync_status: Optional[bool] = None
    auto_sync: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class ExternalIntegration(ExternalIntegrationBase, BaseSchema):
    """Schema for external integration responses."""

    user_id: UUID
    client_id: Optional[str] = None  # Safe to expose client ID
    external_user_id: Optional[str] = None
    external_username: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: SyncStatus
    last_sync_error: Optional[str] = None
    sync_count: int = 0
    settings: Optional[Dict[str, Any]] = None

    # Don't expose sensitive tokens and secrets in responses
    model_config = ConfigDict(
        from_attributes=True, exclude={"access_token", "refresh_token", "client_secret"}
    )


# Manga mapping schemas
class ExternalMangaMappingBase(BaseModel):
    """Base external manga mapping schema."""

    model_config = ConfigDict(from_attributes=True)

    external_manga_id: str
    external_title: Optional[str] = None
    external_url: Optional[str] = None


class ExternalMangaMappingCreate(ExternalMangaMappingBase):
    """Schema for creating external manga mappings."""

    manga_id: UUID
    external_data: Optional[Dict[str, Any]] = None


class ExternalMangaMappingUpdate(BaseModel):
    """Schema for updating external manga mappings."""

    external_title: Optional[str] = None
    external_url: Optional[str] = None
    external_data: Optional[Dict[str, Any]] = None


class ExternalMangaMapping(ExternalMangaMappingBase, BaseSchema):
    """Schema for external manga mapping responses."""

    integration_id: UUID
    manga_id: UUID
    last_synced_at: Optional[datetime] = None
    sync_status: SyncStatus
    sync_error: Optional[str] = None
    external_data: Optional[Dict[str, Any]] = None


# API-specific schemas
class AnilistAuthRequest(BaseModel):
    """Schema for Anilist authentication request."""

    authorization_code: str
    redirect_uri: str
    client_id: Optional[str] = None  # Optional override
    client_secret: Optional[str] = None  # Optional override


class MyAnimeListAuthRequest(BaseModel):
    """Schema for MyAnimeList authentication request."""

    authorization_code: str
    code_verifier: str
    redirect_uri: str
    client_id: Optional[str] = None  # Optional override
    client_secret: Optional[str] = None  # Optional override


class KitsuAuthRequest(BaseModel):
    """Schema for Kitsu authentication request."""

    username: str
    password: str
    client_id: Optional[str] = None  # Optional override
    client_secret: Optional[str] = None  # Optional override


class IntegrationSetupRequest(BaseModel):
    """Schema for setting up integration with API credentials."""

    integration_type: IntegrationType
    client_id: str
    client_secret: str


class SyncRequest(BaseModel):
    """Schema for manual sync requests."""

    integration_type: IntegrationType
    force_full_sync: bool = False
    sync_direction: str = Field(
        default="bidirectional",
        description="Sync direction: 'to_external', 'from_external', or 'bidirectional'",
    )


class SyncResponse(BaseModel):
    """Schema for sync operation responses."""

    integration_type: IntegrationType
    status: SyncStatus
    message: str
    synced_manga_count: int = 0
    errors: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None


class IntegrationStatus(BaseModel):
    """Schema for integration status responses."""

    integration_type: IntegrationType
    is_connected: bool
    external_username: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: SyncStatus
    sync_enabled: bool
    auto_sync: bool
    manga_count: int = 0  # Number of mapped manga


class IntegrationSettings(BaseModel):
    """Schema for integration settings."""

    anilist: Optional[IntegrationStatus] = None
    myanimelist: Optional[IntegrationStatus] = None


# External service data schemas
class ExternalMangaData(BaseModel):
    """Schema for external manga data from APIs."""

    id: str
    title: str
    status: Optional[str] = None
    score: Optional[float] = None
    progress: Optional[int] = None  # Chapters read
    start_date: Optional[str] = None
    finish_date: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    cover_image: Optional[str] = None


class ExternalMangaList(BaseModel):
    """Schema for external manga list responses."""

    manga: List[ExternalMangaData]
    total_count: int
    has_next_page: bool = False
    cursor: Optional[str] = None  # For pagination


# Webhook schemas (for future use)
class WebhookEvent(BaseModel):
    """Schema for webhook events from external services."""

    integration_type: IntegrationType
    event_type: str
    manga_id: str
    data: Dict[str, Any]
    timestamp: datetime
