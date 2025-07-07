from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema


class UserProviderPreferenceBase(BaseModel):
    """Base user provider preference schema."""

    model_config = ConfigDict(from_attributes=True)

    provider_id: str
    is_favorite: bool = False
    priority_order: Optional[int] = None
    is_enabled: bool = True


class UserProviderPreferenceCreate(UserProviderPreferenceBase):
    """User provider preference creation schema."""

    pass


class UserProviderPreferenceUpdate(BaseModel):
    """User provider preference update schema."""

    is_favorite: Optional[bool] = None
    priority_order: Optional[int] = None
    is_enabled: Optional[bool] = None


class UserProviderPreference(UserProviderPreferenceBase, BaseSchema):
    """User provider preference schema for responses."""

    user_id: UUID


class UserProviderPreferenceBulkUpdate(BaseModel):
    """Schema for bulk updating user provider preferences."""

    preferences: List[UserProviderPreferenceBase] = Field(
        ..., description="List of provider preferences to update"
    )


class ProviderWithPreference(BaseModel):
    """Enhanced provider info with user preference data."""

    model_config = ConfigDict(from_attributes=True)

    # Provider info
    id: str
    name: str
    url: str
    supports_nsfw: bool
    status: str = "unknown"
    is_enabled: bool = True
    last_check: Optional[str] = None
    response_time: Optional[int] = None
    uptime_percentage: int = 100
    consecutive_failures: int = 0
    is_healthy: bool = True

    # User preference data
    is_favorite: bool = False
    priority_order: Optional[int] = None
    user_enabled: bool = True


class UserProviderPreferencesResponse(BaseModel):
    """Response schema for user provider preferences."""

    providers: List[ProviderWithPreference]
    total_providers: int
    favorite_count: int
