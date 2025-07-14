from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseSchema
from app.schemas.manga import Manga


# Category schemas
class CategoryBase(BaseModel):
    """Base category schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: bool = False


class CategoryCreate(CategoryBase):
    """Category creation schema."""


class CategoryUpdate(CategoryBase):
    """Category update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: Optional[bool] = None


class Category(CategoryBase, BaseSchema):
    """Category schema for responses."""

    user_id: Optional[UUID] = None


# MangaUserLibrary schemas
class MangaUserLibraryBase(BaseModel):
    """Base manga user library schema."""

    model_config = ConfigDict(from_attributes=True)

    custom_title: Optional[str] = None
    custom_cover: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: bool = False
    rating: Optional[float] = None
    is_downloaded: bool = False
    download_path: Optional[str] = None


class MangaUserLibraryCreate(MangaUserLibraryBase):
    """Manga user library creation schema."""

    manga_id: UUID
    category_ids: Optional[List[UUID]] = None


class MangaUserLibraryUpdate(MangaUserLibraryBase):
    """Manga user library update schema."""

    custom_title: Optional[str] = None
    custom_cover: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    rating: Optional[float] = None
    is_downloaded: Optional[bool] = None
    download_path: Optional[str] = None
    category_ids: Optional[List[UUID]] = None


class MangaUserLibrary(MangaUserLibraryBase, BaseSchema):
    """Manga user library schema for responses."""

    user_id: UUID
    manga_id: UUID
    manga: Optional[Manga] = None
    categories: List[Category] = []


# ReadingList schemas
class ReadingListBase(BaseModel):
    """Base reading list schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: Optional[str] = None
    is_public: bool = False


class ReadingListCreate(ReadingListBase):
    """Reading list creation schema."""

    manga_ids: Optional[List[UUID]] = None


class ReadingListUpdate(ReadingListBase):
    """Reading list update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    manga_ids: Optional[List[UUID]] = None


class ReadingList(ReadingListBase, BaseSchema):
    """Reading list schema for responses."""

    user_id: UUID
    manga: List[Manga] = []


# ReadingProgress schemas
class ReadingProgressBase(BaseModel):
    """Base reading progress schema."""

    model_config = ConfigDict(from_attributes=True)

    page: int = 1
    is_completed: bool = False


class ReadingProgressCreate(ReadingProgressBase):
    """Reading progress creation schema."""

    manga_id: UUID
    chapter_id: UUID


class ReadingProgressUpdate(ReadingProgressBase):
    """Reading progress update schema."""

    page: Optional[int] = None
    is_completed: Optional[bool] = None


class ReadingProgress(ReadingProgressBase, BaseSchema):
    """Reading progress schema for responses."""

    user_id: UUID
    manga_id: UUID
    chapter_id: UUID


# Bookmark schemas
class BookmarkBase(BaseModel):
    """Base bookmark schema."""

    model_config = ConfigDict(from_attributes=True)

    page: int
    name: Optional[str] = None
    notes: Optional[str] = None


class BookmarkCreate(BookmarkBase):
    """Bookmark creation schema."""

    manga_id: UUID
    chapter_id: UUID


class BookmarkUpdate(BookmarkBase):
    """Bookmark update schema."""

    page: Optional[int] = None
    name: Optional[str] = None
    notes: Optional[str] = None


class Bookmark(BookmarkBase, BaseSchema):
    """Bookmark schema for responses."""

    user_id: UUID
    manga_id: UUID
    chapter_id: UUID
