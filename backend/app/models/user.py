from typing import List, Optional
from sqlalchemy import Boolean, Column, String, Text, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # 2FA
    two_fa_secret = Column(String(32), nullable=True)
    two_fa_enabled = Column(Boolean, default=False, nullable=False)

    # Profile
    avatar = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)

    # External Account Links
    anilist_username = Column(String(100), nullable=True)
    myanimelist_username = Column(String(100), nullable=True)

    # Provider monitoring preferences
    provider_check_interval = Column(Integer, default=60, nullable=False)  # minutes: 30, 60, 120, 1440 (daily), 10080 (weekly), 43200 (monthly)

    # User settings
    theme = Column(String(20), default='light', nullable=False)  # light, dark, system
    nsfw_blur = Column(Boolean, default=True, nullable=False)
    download_quality = Column(String(20), default='high', nullable=False)  # low, medium, high
    download_path = Column(String(500), default='/app/storage', nullable=False)

    # Relationships
    manga_items = relationship("MangaUserLibrary", back_populates="user", cascade="all, delete-orphan")
    reading_lists = relationship("ReadingList", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("LibraryCategory", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="user", cascade="all, delete-orphan")
    provider_preferences = relationship("UserProviderPreference", back_populates="user", cascade="all, delete-orphan")
