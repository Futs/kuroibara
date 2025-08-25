"""MangaUpdates integration models."""

import enum
from datetime import datetime
from typing import Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class MangaUpdatesStatus(enum.Enum):
    """MangaUpdates series status."""
    
    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class UniversalMangaEntry(BaseModel):
    """Universal manga entry supporting multiple indexers."""

    __tablename__ = "universal_manga_entries"

    # Source information
    source_indexer = Column(String(50), nullable=False, index=True)  # mangaupdates, madaradx, mangadx
    source_id = Column(String(100), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)

    # Unique constraint on source + id combination
    __table_args__ = (
        sa.UniqueConstraint('source_indexer', 'source_id', name='uq_source_indexer_id'),
    )
    
    # Core metadata
    title = Column(String(500), nullable=False, index=True)
    alternative_titles = Column(JSONB, nullable=True)  # {"english": "...", "japanese": "...", etc}
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)

    # Series information
    type = Column(String(50), nullable=True)  # manga, manhwa, manhua, novel
    status = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    completed_year = Column(Integer, nullable=True)

    # Content ratings
    is_nsfw = Column(Boolean, default=False, nullable=False)
    content_rating = Column(String(20), nullable=True)  # safe, suggestive, erotica, pornographic
    demographic = Column(String(20), nullable=True)  # shounen, seinen, shoujo, josei

    # Enhanced metadata for tiered system
    genres = Column(JSONB, nullable=True)  # List of genre strings
    tags = Column(JSONB, nullable=True)  # More specific than genres
    themes = Column(JSONB, nullable=True)  # Thematic elements
    categories = Column(JSONB, nullable=True)  # Additional categorization

    # People
    authors = Column(JSONB, nullable=True)  # List of author objects with roles
    artists = Column(JSONB, nullable=True)  # List of artist objects with roles
    publishers = Column(JSONB, nullable=True)  # List of publisher objects

    # Statistics (can come from any indexer)
    rating = Column(Float, nullable=True)  # Average rating
    rating_count = Column(Integer, nullable=True)  # Number of ratings
    popularity_rank = Column(Integer, nullable=True)
    follows = Column(Integer, nullable=True)  # Follower count (MangaDex)
    
    # Chapter information
    latest_chapter = Column(String(20), nullable=True)
    total_chapters = Column(Integer, nullable=True)

    # Quality and confidence scoring
    confidence_score = Column(Float, default=1.0, nullable=False)  # How confident we are in this data
    data_completeness = Column(Float, default=0.0, nullable=False)  # Percentage of fields populated

    # Refresh tracking
    last_refreshed = Column(DateTime(timezone=True), nullable=True)
    refresh_interval_hours = Column(Integer, default=24, nullable=False)  # Auto-refresh interval
    auto_refresh_enabled = Column(Boolean, default=True, nullable=False)

    # Raw data for debugging/future use
    raw_data = Column(JSONB, nullable=True)

    # Relationships
    manga_mappings = relationship("UniversalMangaMapping", back_populates="universal_entry", cascade="all, delete-orphan")
    cross_references = relationship("CrossIndexerReference", back_populates="universal_entry", cascade="all, delete-orphan")
    
    def needs_refresh(self) -> bool:
        """Check if entry needs refreshing."""
        if not self.auto_refresh_enabled or not self.last_refreshed:
            return True
        
        hours_since_refresh = (datetime.utcnow() - self.last_refreshed).total_seconds() / 3600
        return hours_since_refresh >= self.refresh_interval_hours


class UniversalMangaMapping(BaseModel):
    """Maps local manga entries to universal manga entries."""

    __tablename__ = "universal_manga_mappings"

    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False)
    universal_entry_id = Column(UUID(as_uuid=True), ForeignKey("universal_manga_entries.id"), nullable=False)
    
    # Mapping confidence and source
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0
    mapping_source = Column(String(50), nullable=False)  # "manual", "auto_title", "auto_fuzzy", etc.
    verified_by_user = Column(Boolean, default=False, nullable=False)

    # Override settings
    use_universal_metadata = Column(Boolean, default=True, nullable=False)
    use_universal_cover = Column(Boolean, default=True, nullable=False)

    # Preferred indexer for this mapping
    preferred_indexer = Column(String(50), nullable=True)  # Which indexer to prioritize

    # Relationships
    manga = relationship("Manga", back_populates="universal_mapping")
    universal_entry = relationship("UniversalMangaEntry", back_populates="manga_mappings")


class CrossIndexerReference(BaseModel):
    """Cross-references between the same manga across different indexers."""

    __tablename__ = "cross_indexer_references"

    # Primary universal entry (usually from highest tier indexer)
    universal_entry_id = Column(UUID(as_uuid=True), ForeignKey("universal_manga_entries.id"), nullable=False)

    # Reference to another indexer's entry for the same manga
    reference_indexer = Column(String(50), nullable=False)  # madaradx, mangadx, etc.
    reference_id = Column(String(100), nullable=False)
    reference_url = Column(String(500), nullable=True)

    # Confidence in this cross-reference
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0.0 - 1.0
    match_method = Column(String(50), nullable=False)  # "title_exact", "title_fuzzy", "manual", etc.

    # Verification status
    verified_by_user = Column(Boolean, default=False, nullable=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)

    # Additional metadata from this reference
    additional_metadata = Column(JSONB, nullable=True)  # Extra data not in main entry

    # Relationships
    universal_entry = relationship("UniversalMangaEntry", back_populates="cross_references")

    # Unique constraint to prevent duplicate references
    __table_args__ = (
        sa.UniqueConstraint('universal_entry_id', 'reference_indexer', 'reference_id',
                          name='uq_cross_reference'),
    )


class DownloadClient(BaseModel):
    """Download client configuration (torrent/NZB clients)."""
    
    __tablename__ = "download_clients"
    
    name = Column(String(100), nullable=False)
    client_type = Column(String(20), nullable=False)  # "torrent", "nzb"
    implementation = Column(String(50), nullable=False)  # "qbittorrent", "deluge", "sabnzb", etc.
    
    # Connection settings
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    use_ssl = Column(Boolean, default=False, nullable=False)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)  # Encrypted
    api_key = Column(String(255), nullable=True)  # For clients that use API keys
    
    # Client-specific settings
    settings = Column(JSONB, nullable=True)  # Client-specific configuration
    
    # Status and priority
    is_enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # Lower = higher priority
    
    # Categories and paths
    default_category = Column(String(100), nullable=True)
    download_path = Column(String(500), nullable=True)
    
    # Health tracking
    last_test = Column(DateTime(timezone=True), nullable=True)
    is_healthy = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    downloads = relationship("Download", back_populates="client")


class Indexer(BaseModel):
    """NZB/Torrent indexer configuration."""
    
    __tablename__ = "indexers"
    
    name = Column(String(100), nullable=False)
    indexer_type = Column(String(20), nullable=False)  # "torrent", "nzb"
    implementation = Column(String(50), nullable=False)  # "nyaa", "1337x", "nzbgeek", etc.
    
    # Connection settings
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(255), nullable=True)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)  # Encrypted
    
    # Indexer capabilities
    supports_search = Column(Boolean, default=True, nullable=False)
    supports_rss = Column(Boolean, default=False, nullable=False)
    
    # Settings
    settings = Column(JSONB, nullable=True)  # Indexer-specific configuration
    
    # Status and priority
    is_enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    
    # Health tracking
    last_test = Column(DateTime(timezone=True), nullable=True)
    is_healthy = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Rate limiting
    requests_per_day = Column(Integer, nullable=True)
    requests_today = Column(Integer, default=0, nullable=False)
    last_request_reset = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MangaUpdatesEntry(BaseModel):
    """MangaUpdates specific entry model."""

    __tablename__ = "mangaupdates_entries"

    # MangaUpdates specific fields
    mu_series_id = Column(String(100), nullable=False, unique=True, index=True)
    mu_url = Column(String(500), nullable=True)

    # Core metadata
    title = Column(String(500), nullable=False, index=True)
    alternative_titles = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)

    # Series information
    type = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    completed_year = Column(Integer, nullable=True)

    # Content ratings
    is_nsfw = Column(Boolean, default=False, nullable=False)
    content_rating = Column(String(20), nullable=True)

    # Enhanced metadata
    genres = Column(JSONB, nullable=True)
    authors = Column(JSONB, nullable=True)
    publishers = Column(JSONB, nullable=True)

    # Statistics
    rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=True)

    # Chapter information
    latest_chapter = Column(String(20), nullable=True)
    total_chapters = Column(Integer, nullable=True)

    # Refresh tracking
    last_refreshed = Column(DateTime(timezone=True), nullable=True)
    auto_refresh_enabled = Column(Boolean, default=True, nullable=False)

    # Raw data
    raw_data = Column(JSONB, nullable=True)

    # Relationships
    manga_mappings = relationship("MangaUpdatesMapping", back_populates="mu_entry", cascade="all, delete-orphan")


class MangaUpdatesMapping(BaseModel):
    """Maps local manga entries to MangaUpdates entries."""

    __tablename__ = "mangaupdates_mappings"

    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False)
    mu_entry_id = Column(UUID(as_uuid=True), ForeignKey("mangaupdates_entries.id"), nullable=False)

    # Mapping confidence and source
    confidence_score = Column(Float, nullable=True)
    mapping_source = Column(String(50), nullable=False)
    verified_by_user = Column(Boolean, default=False, nullable=False)

    # Relationships
    manga = relationship("Manga", back_populates="mangaupdates_mapping")
    mu_entry = relationship("MangaUpdatesEntry", back_populates="manga_mappings")


class Download(BaseModel):
    """Download tracking for all download types."""

    __tablename__ = "downloads"
    
    # What's being downloaded
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=True)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id"), nullable=True)
    
    # Download source and method
    download_type = Column(String(20), nullable=False)  # "provider", "torrent", "nzb"
    source_name = Column(String(100), nullable=True)  # Provider/indexer name
    
    # Download client (for torrent/NZB)
    client_id = Column(UUID(as_uuid=True), ForeignKey("download_clients.id"), nullable=True)
    external_download_id = Column(String(255), nullable=True)  # ID in download client
    
    # Download details
    title = Column(String(500), nullable=False)
    download_url = Column(String(1000), nullable=True)
    magnet_link = Column(Text, nullable=True)
    torrent_hash = Column(String(40), nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, default="queued")  # queued, downloading, completed, failed, cancelled
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 - 100.0
    
    # File information
    total_size = Column(Integer, nullable=True)  # Bytes
    downloaded_size = Column(Integer, default=0, nullable=False)  # Bytes
    download_speed = Column(Integer, nullable=True)  # Bytes per second
    eta = Column(Integer, nullable=True)  # Seconds
    
    # Paths
    download_path = Column(String(500), nullable=True)
    final_path = Column(String(500), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Relationships
    manga = relationship("Manga", back_populates="downloads")
    chapter = relationship("Chapter", back_populates="downloads")
    client = relationship("DownloadClient", back_populates="downloads")
