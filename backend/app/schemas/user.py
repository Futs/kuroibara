from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.base import BaseSchema


# Shared properties
class UserBase(BaseModel):
    """Base user schema."""

    model_config = ConfigDict(from_attributes=True)

    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    avatar: Optional[str] = None
    bio: Optional[str] = None
    two_fa_enabled: bool = False
    anilist_username: Optional[str] = None
    myanimelist_username: Optional[str] = None
    theme: str = "light"
    nsfw_blur: bool = True
    download_quality: str = "high"
    download_path: str = "/app/storage"
    naming_format_manga: str = (
        "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
    )
    naming_format_chapter: str = "{Chapter Number} - {Chapter Name}"
    auto_organize_imports: bool = True
    create_cbz_files: bool = True
    preserve_original_files: bool = False
    chapter_auto_refresh_interval: int = 300
    chapter_check_on_tab_focus: bool = True
    chapter_show_update_notifications: bool = True
    chapter_enable_manual_refresh: bool = True
    storage_type: str = "local"
    max_upload_size: str = "100MB"


# Properties to receive via API on creation
class UserCreate(BaseModel):
    """User creation schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


# Properties to receive via API on update
class UserUpdate(BaseModel):
    """User update schema."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    current_password: str = Field(
        ..., description="Current password required for verification"
    )
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    anilist_username: Optional[str] = None
    myanimelist_username: Optional[str] = None
    theme: Optional[str] = None
    nsfw_blur: Optional[bool] = None
    download_quality: Optional[str] = None
    download_path: Optional[str] = None
    naming_format_manga: Optional[str] = None
    naming_format_chapter: Optional[str] = None
    auto_organize_imports: Optional[bool] = None
    create_cbz_files: Optional[bool] = None
    preserve_original_files: Optional[bool] = None
    chapter_auto_refresh_interval: Optional[int] = None
    chapter_check_on_tab_focus: Optional[bool] = None
    chapter_show_update_notifications: Optional[bool] = None
    chapter_enable_manual_refresh: Optional[bool] = None
    storage_type: Optional[str] = None
    max_upload_size: Optional[str] = None


# Properties to return via API
class User(UserBase, BaseSchema):
    """User schema for responses."""


# Properties for user in DB
class UserInDB(User):
    """User schema with hashed password."""

    hashed_password: str
    two_fa_secret: Optional[str] = None


# User settings schemas
class UserSettings(BaseModel):
    """User settings schema for responses."""

    model_config = ConfigDict(from_attributes=True)

    theme: str = "light"
    nsfw_blur: bool = True
    download_quality: str = "high"
    download_path: str = "/app/storage"
    naming_format_manga: str = (
        "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
    )
    naming_format_chapter: str = "{Chapter Number} - {Chapter Name}"
    auto_organize_imports: bool = True
    create_cbz_files: bool = True
    preserve_original_files: bool = False
    chapter_auto_refresh_interval: int = 300
    chapter_check_on_tab_focus: bool = True
    chapter_show_update_notifications: bool = True
    chapter_enable_manual_refresh: bool = True
    storage_type: str = "local"
    max_upload_size: str = "100MB"


class UserSettingsUpdate(BaseModel):
    """User settings update schema."""

    theme: Optional[str] = None
    nsfw_blur: Optional[bool] = None
    download_quality: Optional[str] = None
    download_path: Optional[str] = None
    naming_format_manga: Optional[str] = None
    naming_format_chapter: Optional[str] = None
    auto_organize_imports: Optional[bool] = None
    create_cbz_files: Optional[bool] = None
    preserve_original_files: Optional[bool] = None
    chapter_auto_refresh_interval: Optional[int] = None
    chapter_check_on_tab_focus: Optional[bool] = None
    chapter_show_update_notifications: Optional[bool] = None
    chapter_enable_manual_refresh: Optional[bool] = None
    storage_type: Optional[str] = None
    max_upload_size: Optional[str] = None
