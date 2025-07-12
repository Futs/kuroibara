"""
Schemas for organization and metadata tracking.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import BaseSchema


# Naming format schemas
class NamingFormatValidation(BaseModel):
    """Schema for validating naming format templates."""

    template: str = Field(..., description="The naming format template to validate")


class NamingFormatValidationResponse(BaseModel):
    """Response schema for naming format validation."""

    is_valid: bool = Field(..., description="Whether the template is valid")
    error_message: Optional[str] = Field(None, description="Error message if invalid")
    sample_output: Optional[str] = Field(
        None, description="Sample output using test data"
    )


# Organization operation schemas
class OrganizeChapterRequest(BaseModel):
    """Request schema for organizing a single chapter."""

    chapter_id: UUID = Field(..., description="ID of the chapter to organize")
    preserve_original: Optional[bool] = Field(
        None, description="Override user setting for preserving original files"
    )
    custom_naming_format: Optional[str] = Field(
        None, description="Custom naming format for this operation"
    )


class OrganizeMangaRequest(BaseModel):
    """Request schema for organizing all chapters of a manga."""

    manga_id: UUID = Field(..., description="ID of the manga to organize")
    preserve_original: Optional[bool] = Field(
        None, description="Override user setting for preserving original files"
    )
    custom_naming_format: Optional[str] = Field(
        None, description="Custom naming format for this operation"
    )


class BatchOrganizeRequest(BaseModel):
    """Request schema for batch organization operations."""

    manga_ids: Optional[List[UUID]] = Field(
        None, description="List of manga IDs to organize"
    )
    chapter_ids: Optional[List[UUID]] = Field(
        None, description="List of chapter IDs to organize"
    )
    organize_all_library: bool = Field(
        False, description="Organize entire user library"
    )
    preserve_original: Optional[bool] = Field(
        None, description="Override user setting for preserving original files"
    )
    custom_naming_format: Optional[str] = Field(
        None, description="Custom naming format for this operation"
    )


class OrganizationResult(BaseModel):
    """Result of an organization operation."""

    success: bool = Field(..., description="Whether the operation was successful")
    organized_files: List[str] = Field(
        default_factory=list, description="List of organized file paths"
    )
    created_directories: List[str] = Field(
        default_factory=list, description="List of created directory paths"
    )
    errors: List[str] = Field(
        default_factory=list, description="List of errors encountered"
    )
    warnings: List[str] = Field(
        default_factory=list, description="List of warnings encountered"
    )


# Metadata schemas
class MangaMetadataBase(BaseModel):
    """Base manga metadata schema."""

    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = None
    custom_cover_url: Optional[str] = None
    custom_description: Optional[str] = None
    reading_status: str = "unread"
    custom_metadata: Optional[Dict] = None


class MangaMetadataCreate(MangaMetadataBase):
    """Schema for creating manga metadata."""

    manga_id: UUID


class MangaMetadataUpdate(BaseModel):
    """Schema for updating manga metadata."""

    display_name: Optional[str] = None
    custom_cover_url: Optional[str] = None
    custom_description: Optional[str] = None
    reading_status: Optional[str] = None
    custom_metadata: Optional[Dict] = None


class MangaMetadata(MangaMetadataBase, BaseSchema):
    """Schema for manga metadata responses."""

    manga_id: UUID
    user_id: UUID
    is_organized: bool
    organization_format: Optional[str]
    last_organized_at: Optional[datetime]
    last_read_at: Optional[datetime]


class ChapterMetadataBase(BaseModel):
    """Base chapter metadata schema."""

    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = None
    custom_cover_url: Optional[str] = None
    current_page: int = 1
    reading_progress: int = 0
    is_completed: bool = False
    custom_metadata: Optional[Dict] = None


class ChapterMetadataCreate(ChapterMetadataBase):
    """Schema for creating chapter metadata."""

    chapter_id: UUID


class ChapterMetadataUpdate(BaseModel):
    """Schema for updating chapter metadata."""

    display_name: Optional[str] = None
    custom_cover_url: Optional[str] = None
    current_page: Optional[int] = None
    reading_progress: Optional[int] = None
    is_completed: Optional[bool] = None
    custom_metadata: Optional[Dict] = None


class ChapterMetadata(ChapterMetadataBase, BaseSchema):
    """Schema for chapter metadata responses."""

    chapter_id: UUID
    user_id: UUID
    is_organized: bool
    organized_path: Optional[str]
    original_path: Optional[str]
    cbz_path: Optional[str]
    total_pages: Optional[int]
    last_read_at: Optional[datetime]


# Organization job schemas
class OrganizationJobBase(BaseModel):
    """Base organization job schema."""

    model_config = ConfigDict(from_attributes=True)

    job_type: str
    job_status: str = "pending"
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0


class OrganizationJobCreate(OrganizationJobBase):
    """Schema for creating organization jobs."""

    job_config: Optional[Dict] = None
    naming_format_manga: Optional[str] = None
    naming_format_chapter: Optional[str] = None


class OrganizationJob(OrganizationJobBase, BaseSchema):
    """Schema for organization job responses."""

    user_id: UUID
    job_config: Optional[Dict]
    naming_format_manga: Optional[str]
    naming_format_chapter: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    result_summary: Optional[Dict]
    error_log: Optional[Dict]

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100


# Organization history schemas
class OrganizationHistoryBase(BaseModel):
    """Base organization history schema."""

    model_config = ConfigDict(from_attributes=True)

    operation_type: str
    operation_status: str
    source_path: Optional[str]
    destination_path: Optional[str]
    backup_path: Optional[str]
    naming_format_used: Optional[str]
    files_processed: int = 0


class OrganizationHistory(OrganizationHistoryBase, BaseSchema):
    """Schema for organization history responses."""

    user_id: UUID
    manga_id: Optional[UUID]
    chapter_id: Optional[UUID]
    errors_encountered: Optional[List[str]]
    warnings_encountered: Optional[List[str]]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    operation_details: Optional[Dict]


# Settings update schemas
class NamingSettingsUpdate(BaseModel):
    """Schema for updating naming settings."""

    naming_format_manga: Optional[str] = None
    naming_format_chapter: Optional[str] = None
    auto_organize_imports: Optional[bool] = None
    create_cbz_files: Optional[bool] = None
    preserve_original_files: Optional[bool] = None


class NamingSettings(BaseModel):
    """Schema for naming settings responses."""

    model_config = ConfigDict(from_attributes=True)

    naming_format_manga: str
    naming_format_chapter: str
    auto_organize_imports: bool
    create_cbz_files: bool
    preserve_original_files: bool


# Storage recovery schemas
class RecoverableManga(BaseModel):
    """Schema for recoverable manga from storage."""

    storage_uuid: str = Field(..., description="Original storage UUID")
    extracted_title: str = Field(
        ..., description="Manga title extracted from folder structure"
    )
    chapter_count: int = Field(..., description="Number of chapters found")
    volume_count: int = Field(..., description="Number of volumes found")
    storage_size: int = Field(..., description="Total storage size in bytes")
    has_volume_structure: bool = Field(
        ..., description="Whether manga has volume-based organization"
    )
    organized_path: str = Field(..., description="Path to organized files")
    volumes: Dict = Field(..., description="Volume and chapter information")
    metadata: Optional[Dict] = Field(
        None, description="Extracted metadata from CBZ files"
    )


class RecoverMangaRequest(BaseModel):
    """Request schema for recovering manga from storage."""

    storage_uuid: str = Field(..., description="Storage UUID to recover")
    manga_title: str = Field(..., description="Title for the recovered manga")
    custom_metadata: Optional[Dict] = Field(
        None, description="Custom metadata to apply"
    )


class RecoverMangaResponse(BaseModel):
    """Response schema for manga recovery."""

    success: bool = Field(..., description="Whether recovery was successful")
    manga_id: Optional[UUID] = Field(None, description="ID of recovered manga")
    message: str = Field(..., description="Recovery result message")
    chapters_recovered: int = Field(0, description="Number of chapters recovered")
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )


class BatchRecoveryRequest(BaseModel):
    """Request schema for batch manga recovery."""

    recovery_items: List[RecoverMangaRequest] = Field(
        ..., description="List of manga to recover"
    )
    skip_errors: bool = Field(
        True, description="Whether to continue on individual errors"
    )


class BatchRecoveryResponse(BaseModel):
    """Response schema for batch recovery."""

    total_requested: int = Field(..., description="Total manga requested for recovery")
    successful_recoveries: int = Field(
        ..., description="Number of successful recoveries"
    )
    failed_recoveries: int = Field(..., description="Number of failed recoveries")
    recovered_manga: List[RecoverMangaResponse] = Field(
        ..., description="Details of recovered manga"
    )
    errors: List[str] = Field(default_factory=list, description="Overall errors")
