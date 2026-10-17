"""Reading state, activity and chapter cache for extension-source series.

The library is global (series.in_library). Everything the user does is per user: reading_state, reading_events,
user_day_activity. Chapters are shared per series. See docs/TODO_TACHIYOMI_EXTENSIONS.md (storage decision).
"""
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.db.session import Base


class SeriesChapter(BaseModel):
    """A chapter of a series, cached from the source. Reading state refers to this row, not to the source URL."""

    __tablename__ = "series_chapters"

    series_id = Column(UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    name = Column(Text, nullable=False, default="")
    chapter_number = Column(Float, nullable=True)
    date_upload = Column(BigInteger, nullable=True)  # epoch milliseconds, as the source reports it
    scanlator = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("series_id", "url", name="uq_series_chapter_url"),)


class ReadingState(Base):
    """What one user did with one chapter. One row per (user, chapter), updated in place."""

    __tablename__ = "reading_state"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("series_chapters.id", ondelete="CASCADE"), primary_key=True)
    series_id = Column(UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True)
    read = Column(Boolean, nullable=False, default=False)
    bookmark = Column(Boolean, nullable=False, default=False)
    last_page = Column(Integer, nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    chapter = relationship("SeriesChapter")


class ReadingEvent(Base):
    """Append-only log of read and unread changes. Source of truth for activity; the rollup is derived from it."""

    __tablename__ = "reading_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    series_id = Column(UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("series_chapters.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(10), nullable=False)  # "read" | "unread"
    at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    local_day = Column(Date, nullable=False)  # calendar day in the user's zone at the time of the event


class UserDayActivity(Base):
    """Net chapters read per user per local day (the user's zone when the event was written). Rollup of reading_events."""

    __tablename__ = "user_day_activity"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    day = Column(Date, primary_key=True)
    chapters_read = Column(Integer, nullable=False, default=0)
