import enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import BaseModel


class ProviderStatusEnum(enum.Enum):
    """Provider status enumeration."""

    ACTIVE = "active"
    DOWN = "down"
    UNKNOWN = "unknown"
    TESTING = "testing"


class ProviderStatus(BaseModel):
    """Provider status model - tracks the health and availability of manga providers."""

    __tablename__ = "provider_status"

    provider_id = Column(String(100), unique=True, index=True, nullable=False)
    provider_name = Column(String(100), nullable=False)
    provider_url = Column(String(255), nullable=False)
    status = Column(
        String(20), default=ProviderStatusEnum.UNKNOWN.value, nullable=False
    )

    # Health check details
    last_check = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    response_time = Column(Integer, nullable=True)  # in milliseconds
    error_message = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0, nullable=False)

    # Statistics
    total_checks = Column(Integer, default=0, nullable=False)
    successful_checks = Column(Integer, default=0, nullable=False)
    uptime_percentage = Column(Integer, default=100, nullable=False)  # 0-100

    # Configuration
    is_enabled = Column(Boolean, default=True, nullable=False)
    check_interval = Column(Integer, default=60, nullable=False)  # minutes
    max_consecutive_failures = Column(Integer, default=3, nullable=False)

    @property
    def is_healthy(self) -> bool:
        """Check if the provider is considered healthy."""
        return (
            self.status == ProviderStatusEnum.ACTIVE.value
            and self.consecutive_failures < self.max_consecutive_failures
            and self.is_enabled
        )

    @property
    def should_be_grayed_out(self) -> bool:
        """Check if the provider should be grayed out in the UI."""
        return not self.is_healthy

    def update_status(
        self, is_success: bool, response_time: int = None, error_message: str = None
    ):
        """Update the provider status based on a health check result."""
        self.total_checks += 1
        self.last_check = func.now()

        if is_success:
            self.status = ProviderStatusEnum.ACTIVE.value
            self.consecutive_failures = 0
            self.successful_checks += 1
            self.response_time = response_time
            self.error_message = None
        else:
            self.consecutive_failures += 1
            self.error_message = error_message

            if self.consecutive_failures >= self.max_consecutive_failures:
                self.status = ProviderStatusEnum.DOWN.value

        # Update uptime percentage
        if self.total_checks > 0:
            self.uptime_percentage = int(
                (self.successful_checks / self.total_checks) * 100
            )
