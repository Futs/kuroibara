import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel


# Enum for manga types
class MangaType(str, enum.Enum):
    MANGA = "manga"
    MANHUA = "manhua"
    MANHWA = "manhwa"
    COMIC = "comic"
    UNKNOWN = "unknown"


# Enum for manga status
class MangaStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


# Association table for manga and genres
manga_genre = Table(
    "manga_genre",
    Base.metadata,
    Column("manga_id", UUID(as_uuid=True), ForeignKey("manga.id"), primary_key=True),
    Column("genre_id", UUID(as_uuid=True), ForeignKey("genre.id"), primary_key=True),
)


# Association table for manga and authors
manga_author = Table(
    "manga_author",
    Base.metadata,
    Column("manga_id", UUID(as_uuid=True), ForeignKey("manga.id"), primary_key=True),
    Column("author_id", UUID(as_uuid=True), ForeignKey("author.id"), primary_key=True),
)


class Manga(BaseModel):
    """Manga model."""

    __tablename__ = "manga"

    title = Column(String(255), nullable=False, index=True)
    alternative_titles = Column(
        JSONB, nullable=True
    )  # Store alternative titles in different languages
    description = Column(Text, nullable=True)
    cover_image = Column(String(255), nullable=True)
    type = Column(Enum(MangaType), default=MangaType.UNKNOWN, nullable=False)
    status = Column(Enum(MangaStatus), default=MangaStatus.UNKNOWN, nullable=False)
    year = Column(Integer, nullable=True)
    is_nsfw = Column(Boolean, default=False, nullable=False)

    # External provider information
    provider = Column(
        String(50), nullable=True, index=True
    )  # Provider name (e.g., 'mangadex', 'mangasee')
    external_id = Column(
        String(255), nullable=True, index=True
    )  # External ID on the provider
    external_url = Column(String(500), nullable=True)  # External URL

    # External IDs from different sources (for backward compatibility)
    external_ids = Column(JSONB, nullable=True)

    # Relationships
    genres = relationship("Genre", secondary=manga_genre, back_populates="manga")
    authors = relationship("Author", secondary=manga_author, back_populates="manga")
    chapters = relationship(
        "Chapter", back_populates="manga", cascade="all, delete-orphan"
    )
    universal_mapping = relationship("UniversalMangaMapping", back_populates="manga", uselist=False)
    mangaupdates_mapping = relationship("MangaUpdatesMapping", back_populates="manga", uselist=False)
    downloads = relationship("Download", back_populates="manga", cascade="all, delete-orphan")
    manga_metadata = relationship(
        "MangaMetadata",
        back_populates="manga",
        uselist=False,
        cascade="all, delete-orphan",
    )
    user_libraries = relationship(
        "MangaUserLibrary", back_populates="manga", cascade="all, delete-orphan"
    )


class Genre(BaseModel):
    """Genre model."""

    __tablename__ = "genre"

    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Relationships
    manga = relationship("Manga", secondary=manga_genre, back_populates="genres")


class Author(BaseModel):
    """Author model."""

    __tablename__ = "author"

    name = Column(String(100), nullable=False, index=True)
    alternative_names = Column(JSONB, nullable=True)
    biography = Column(Text, nullable=True)

    # Relationships
    manga = relationship("Manga", secondary=manga_author, back_populates="authors")


class Chapter(BaseModel):
    """Chapter model."""

    __tablename__ = "chapter"

    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False)
    title = Column(String(255), nullable=True)
    number = Column(
        String(20), nullable=False
    )  # String to support formats like "12.5", "Extra", etc.
    volume = Column(String(20), nullable=True)
    language = Column(String(10), nullable=False, default="en")
    pages_count = Column(Integer, nullable=True)
    file_path = Column(
        String(255), nullable=True
    )  # Path to the chapter file (CBZ, directory, etc.)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    source = Column(
        String(50), nullable=True
    )  # Source of the chapter (website, scanner, etc.)
    publish_at = Column(DateTime, nullable=True)  # When the chapter was published
    readable_at = Column(DateTime, nullable=True)  # When the chapter became readable

    # Download tracking fields
    download_status = Column(
        String(20), nullable=False, default="not_downloaded", index=True
    )  # Download status: not_downloaded, downloading, downloaded, error
    download_error = Column(Text, nullable=True)  # Error message if download failed
    external_id = Column(
        String(255), nullable=True, index=True
    )  # External ID from the provider
    provider_external_ids = Column(
        JSONB, nullable=True
    )  # External IDs from multiple providers {"mangadex": "abc123", "mangapill": "def456"}
    fallback_providers = Column(
        JSONB, nullable=True
    )  # List of fallback providers to try ["mangapill", "mangasee", "mangakakalot"]

    # Relationships
    manga = relationship("Manga", back_populates="chapters")
    pages = relationship("Page", back_populates="chapter", cascade="all, delete-orphan")
    downloads = relationship("Download", back_populates="chapter", cascade="all, delete-orphan")
    reading_progress = relationship(
        "ReadingProgress", back_populates="chapter", cascade="all, delete-orphan"
    )
    bookmarks = relationship(
        "Bookmark", back_populates="chapter", cascade="all, delete-orphan"
    )
    chapter_metadata = relationship(
        "ChapterMetadata",
        back_populates="chapter",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Page(BaseModel):
    """Page model."""

    __tablename__ = "page"

    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id"), nullable=False)
    number = Column(Integer, nullable=False)
    file_path = Column(String(255), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Relationships
    chapter = relationship("Chapter", back_populates="pages")
