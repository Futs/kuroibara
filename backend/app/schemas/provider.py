from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.provider import ProviderStatusEnum


class ProviderStatusBase(BaseModel):
    """Base provider status schema."""
    
    provider_id: str
    provider_name: str
    provider_url: str
    status: str
    is_enabled: bool = True
    check_interval: int = 60
    max_consecutive_failures: int = 3


class ProviderStatusCreate(ProviderStatusBase):
    """Provider status creation schema."""
    pass


class ProviderStatusUpdate(BaseModel):
    """Provider status update schema."""
    
    status: Optional[str] = None
    is_enabled: Optional[bool] = None
    check_interval: Optional[int] = None
    max_consecutive_failures: Optional[int] = None


class ProviderStatus(ProviderStatusBase):
    """Provider status schema."""
    
    id: str
    last_check: datetime
    response_time: Optional[int] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    successful_checks: int = 0
    uptime_percentage: int = 100
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProviderInfo(BaseModel):
    """Enhanced provider information schema with status."""
    
    id: str
    name: str
    url: str
    supports_nsfw: bool
    status: str = ProviderStatusEnum.UNKNOWN.value
    is_enabled: bool = True
    last_check: Optional[datetime] = None
    response_time: Optional[int] = None
    uptime_percentage: int = 100
    consecutive_failures: int = 0
    is_healthy: bool = True


class ProviderHealthCheck(BaseModel):
    """Provider health check result schema."""
    
    provider_id: str
    is_success: bool
    response_time: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime


class ProviderCheckIntervalUpdate(BaseModel):
    """Schema for updating user's provider check interval preference."""
    
    interval: int = Field(..., description="Check interval in minutes (30, 60, 120, 1440, 10080, 43200)")
    
    class Config:
        schema_extra = {
            "example": {
                "interval": 60
            }
        }


class ProviderMonitoringSettings(BaseModel):
    """Provider monitoring settings schema."""
    
    enabled: bool = True
    global_check_interval: int = 60
    max_concurrent_checks: int = 10
    timeout_seconds: int = 30
    retry_attempts: int = 3
