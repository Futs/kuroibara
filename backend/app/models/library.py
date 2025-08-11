from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel

# Association table for manga user library and categories
manga_user_library_category = Table(
    "manga_user_library_category",
    Base.metadata,
    Column(
        "manga_user_library_id",
        UUID(as_uuid=True),
        ForeignKey("manga_user_library.id"),
        primary_key=True,
    ),
    Column(
        "category_id", UUID(as_uuid=True), ForeignKey("category.id"), primary_key=True
    ),
)


# Association table for reading lists and manga
reading_list_manga = Table(
    "reading_list_manga",
    Base.metadata,
    Column(
        "reading_list_id",
        UUID(as_uuid=True),
        ForeignKey("reading_list.id"),
        primary_key=True,
    ),
    Column("manga_id", UUID(as_uuid=True), ForeignKey("manga.id"), primary_key=True),
)


class MangaUserLibrary(BaseModel):
    """Manga user library model - represents a manga in a user's library."""

    __tablename__ = "manga_user_library"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False)

    # User-specific metadata
    custom_title = Column(String(255), nullable=True)
    custom_cover = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False, nullable=False)
    rating = Column(Float, nullable=True)

    # Download status
    is_downloaded = Column(Boolean, default=False, nullable=False)
    download_path = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="manga_items")
    manga = relationship("Manga", back_populates="user_libraries")
    categories = relationship(
        "LibraryCategory",
        secondary=manga_user_library_category,
        back_populates="manga_items",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "user_id", "manga_id", name="uq_manga_user_library_user_manga"
        ),
    )


class LibraryCategory(BaseModel):
    """Category model."""

    __tablename__ = "category"
    __table_args__ = {"extend_existing": True}

    name = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # Null for system categories

    # Relationships
    user = relationship("User", back_populates="categories")
    manga_items = relationship(
        "MangaUserLibrary",
        secondary=manga_user_library_category,
        back_populates="categories",
    )


class ReadingList(BaseModel):
    """Reading list model."""

    __tablename__ = "reading_list"

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reading_lists")
    manga = relationship("Manga", secondary=reading_list_manga)


class ReadingProgress(BaseModel):
    """Reading progress model."""

    __tablename__ = "reading_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id"), nullable=False)
    page = Column(Integer, nullable=False, default=1)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reading_progress")
    chapter = relationship("Chapter", back_populates="reading_progress")


class Bookmark(BaseModel):
    """Bookmark model."""

    __tablename__ = "bookmark"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id"), nullable=False)
    page = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    chapter = relationship("Chapter", back_populates="bookmarks")
