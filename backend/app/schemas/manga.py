from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.models.manga import MangaType, MangaStatus
from app.schemas.base import BaseSchema


# Genre schemas
class GenreBase(BaseModel):
    """Base genre schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    description: Optional[str] = None


class GenreCreate(GenreBase):
    """Genre creation schema."""
    pass


class GenreUpdate(GenreBase):
    """Genre update schema."""
    
    name: Optional[str] = None


class Genre(GenreBase, BaseSchema):
    """Genre schema for responses."""
    pass


# Author schemas
class AuthorBase(BaseModel):
    """Base author schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    alternative_names: Optional[Dict[str, str]] = None
    biography: Optional[str] = None


class AuthorCreate(AuthorBase):
    """Author creation schema."""
    pass


class AuthorUpdate(AuthorBase):
    """Author update schema."""
    
    name: Optional[str] = None


class Author(AuthorBase, BaseSchema):
    """Author schema for responses."""
    pass


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
    pass


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
    external_ids: Optional[Dict[str, str]] = None
    genres: Optional[List[str]] = None
    authors: Optional[List[str]] = None


class Manga(MangaBase, BaseSchema):
    """Manga schema for responses."""
    
    genres: List[Genre] = []
    authors: List[Author] = []
    chapters: Optional[List[Chapter]] = None
