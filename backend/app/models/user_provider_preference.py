from sqlalchemy import Boolean, Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class UserProviderPreference(BaseModel):
    """User provider preference model - stores user's provider favorites and preferences."""

    __tablename__ = "user_provider_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(String(100), nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    priority_order = Column(Integer, nullable=True)  # 1 = highest priority, null = no specific order
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="provider_preferences")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'provider_id', name='uq_user_provider'),
    )

    def __repr__(self):
        return f"<UserProviderPreference(user_id={self.user_id}, provider_id={self.provider_id}, is_favorite={self.is_favorite})>"
