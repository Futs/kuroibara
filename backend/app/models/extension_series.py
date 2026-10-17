"""Series and their extension sources (Tachiyomi/Keiyoushi extensions).

Separate from the legacy `manga` tables so existing providers keep working (strangler pattern, D4).
Metadata lives in `series_metadata`: `base` is the provider snapshot taken when the title was added
and never edited; `current` is what the library shows, with an origin per field. See Phase 2b.
"""
from sqlalchemy import (
    DateTime,
    func,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import BaseModel


class Series(BaseModel):
    """One library entry: a title as it exists on one source (Mihon's manga row).

    Migrating to another source creates a second entry; the first stays in the database with in_library=False.
    The shown title and cover are copies of series_metadata.current, kept here for listing and sorting.
    """

    __tablename__ = "series"

    module = Column(String(120), nullable=False)  # host install key, e.g. en/mangakatana
    package = Column(String(255), nullable=False)  # eu.kanade.tachiyomi.extension.en.mangakatana
    source_name = Column(String(255), nullable=False)
    source_lang = Column(String(20), nullable=False)
    source_id = Column(String(40), nullable=True)  # Keiyoushi source id, as text (a 64-bit number)
    series_url = Column(Text, nullable=False)  # the extension's URL for this title

    title = Column(String(500), nullable=False, index=True)
    cover_url = Column(Text, nullable=True)
    is_nsfw = Column(Boolean, nullable=False, default=False)
    content_warning = Column(String(40), nullable=True)
    in_library = Column(Boolean, nullable=False, default=True, index=True)

    metadata_record = relationship(
        "SeriesMetadata", back_populates="series", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("module", "series_url", name="uq_series_source_url"),
    )


class SeriesMetadata(Base):
    """One row per series, keyed by series_id. Not a BaseModel: it has no separate id column (migration 018)."""

    __tablename__ = "series_metadata"

    series_id = Column(
        UUID(as_uuid=True),
        ForeignKey("series.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Provider snapshot: {"title": "...", "authors": [...], ...}. Written once when the title is added.
    base = Column(JSONB, nullable=False)
    # Shown in the library: {"title": {"value": ..., "origin": "provider|mangaupdates|edited"}, ...}
    current = Column(JSONB, nullable=False)
    # Cached MangaUpdates entry for comparison (Phase 2b). Null until the user asks.
    mangaupdates = Column(JSONB, nullable=True)
    schema_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    series = relationship("Series", back_populates="metadata_record")


class SourceDownload(BaseModel):
    """One chapter queued for download from an extension source. Persisted, so a restart keeps the queue (Mihon's DownloadStore)."""

    __tablename__ = "source_downloads"

    series_id = Column(
        UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module = Column(String(120), nullable=False)
    chapter_url = Column(Text, nullable=False)
    chapter_name = Column(String(500), nullable=False)
    chapter_number = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="queued", index=True)  # queued|downloading|downloaded|error
    # Page list is fetched once and kept, so a retry does not refetch it: [{"index", "url", "image_url"}]
    pages = Column(JSONB, nullable=True)
    page_count = Column(Integer, nullable=True)
    path = Column(Text, nullable=True)  # the committed .cbz or chapter folder
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    claimed_by = Column(String(120), nullable=True)  # worker id that is downloading this row
    claimed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("series_id", "module", "chapter_url", name="uq_source_download_chapter"),
    )
