from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.manga import MangaStatus, MangaType
from app.schemas.base import BaseSchema


# Genre schemas
class GenreBase(BaseModel):
    """Base genre schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None


class GenreCreate(GenreBase):
    """Genre creation schema."""


class GenreUpdate(GenreBase):
    """Genre update schema."""

    name: Optional[str] = None


class Genre(GenreBase, BaseSchema):
    """Genre schema for responses."""


# Author schemas
class AuthorBase(BaseModel):
    """Base author schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    alternative_names: Optional[Dict[str, str]] = None
    biography: Optional[str] = None


class AuthorCreate(AuthorBase):
    """Author creation schema."""


class AuthorUpdate(AuthorBase):
    """Author update schema."""

    name: Optional[str] = None


class Author(AuthorBase, BaseSchema):
    """Author schema for responses."""


# Chapter schemas
class PageBase(BaseModel):
    """Base page schema."""

    model_config = ConfigDict(from_attributes=True)

    number: int
    file_path: str
    width: Optional[int] = None
    height: Optional[int] = None


class PageCreate(PageBase):
    """Page creation schema."""


class Page(PageBase, BaseSchema):
    """Page schema for responses."""

    chapter_id: UUID


class ChapterBase(BaseModel):
    """Base chapter schema."""

    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    number: str
    volume: Optional[str] = None
    language: str = "en"
    pages_count: Optional[int] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    source: Optional[str] = None
    publish_at: Optional[datetime] = None
    readable_at: Optional[datetime] = None
    download_status: str = "not_downloaded"
    download_error: Optional[str] = None
    external_id: Optional[str] = None


class ChapterCreate(ChapterBase):
    """Chapter creation schema."""

    manga_id: UUID


class ChapterUpdate(ChapterBase):
    """Chapter update schema."""

    title: Optional[str] = None
    number: Optional[str] = None
    volume: Optional[str] = None
    language: Optional[str] = None
    pages_count: Optional[int] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    source: Optional[str] = None
    download_status: Optional[str] = None
    download_error: Optional[str] = None
    external_id: Optional[str] = None


class ChapterSummary(ChapterBase, BaseSchema):
    """Chapter schema for responses without pages (for library listings)."""

    manga_id: UUID


class Chapter(ChapterBase, BaseSchema):
    """Chapter schema for responses."""

    manga_id: UUID
    pages: Optional[List[Page]] = None


# Manga schemas
class MangaBase(BaseModel):
    """Base manga schema."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    alternative_titles: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    type: MangaType = MangaType.UNKNOWN
    status: MangaStatus = MangaStatus.UNKNOWN
    year: Optional[int] = None
    is_nsfw: bool = False
    provider: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    external_ids: Optional[Dict[str, str]] = None


class MangaCreate(MangaBase):
    """Manga creation schema."""

    genres: Optional[List[str]] = None
    authors: Optional[List[str]] = None


class MangaUpdate(MangaBase):
    """Manga update schema."""

    title: Optional[str] = None
    alternative_titles: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    type: Optional[MangaType] = None
    status: Optional[MangaStatus] = None
    year: Optional[int] = None
    is_nsfw: Optional[bool] = None
    provider: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    external_ids: Optional[Dict[str, str]] = None
    genres: Optional[List[str]] = None
    authors: Optional[List[str]] = None


class MangaSummary(MangaBase, BaseSchema):
    """Manga schema for responses without chapter pages (for library listings)."""

    genres: List[Genre] = []
    authors: List[Author] = []
    chapters: Optional[List[ChapterSummary]] = None


class Manga(MangaBase, BaseSchema):
    """Manga schema for responses."""

    genres: List[Genre] = []
    authors: List[Author] = []
    chapters: Optional[List[Chapter]] = None
