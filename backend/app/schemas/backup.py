"""
Schemas for backup and restore operations.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BackupCreateRequest(BaseModel):
    """Request schema for creating a backup."""

    backup_name: Optional[str] = Field(None, description="Custom name for the backup")
    include_storage: bool = Field(
        True, description="Whether to include storage files in backup"
    )


class CreateBackupResponse(BaseModel):
    """Response schema for backup creation."""

    message: str = Field(..., description="Status message")
    backup_name: str = Field(..., description="Name of the backup being created")
    estimated_duration: str = Field(..., description="Estimated time for completion")


class BackupInfo(BaseModel):
    """Schema for backup file information."""

    filename: str = Field(..., description="Backup filename")
    size: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="Creation timestamp")
    metadata: Optional[Dict] = Field(None, description="Backup metadata")
    download_url: str = Field(..., description="URL to download the backup")

    @property
    def size_mb(self) -> float:
        """Get size in megabytes."""
        return round(self.size / (1024 * 1024), 2)

    @property
    def includes_storage(self) -> bool:
        """Check if backup includes storage files."""
        if self.metadata:
            return self.metadata.get("includes_storage", False)
        return "weekly" in self.filename or "monthly" in self.filename


class BackupListResponse(BaseModel):
    """Response schema for listing backups."""

    backups: List[BackupInfo] = Field(..., description="List of available backups")
    total_count: int = Field(..., description="Total number of backups")
    total_size: int = Field(..., description="Total size of all backups in bytes")

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return round(self.total_size / (1024 * 1024), 2)


class BackupRestoreResponse(BaseModel):
    """Response schema for backup restore operations."""

    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Name of the backup file being restored")
    status: str = Field(..., description="Restore status")
    warnings: List[str] = Field(
        default_factory=list, description="Important warnings about the restore"
    )


class BackupScheduleInfo(BaseModel):
    """Schema for backup schedule information."""

    daily_enabled: bool = Field(..., description="Whether daily backups are enabled")
    weekly_enabled: bool = Field(..., description="Whether weekly backups are enabled")
    monthly_enabled: bool = Field(
        ..., description="Whether monthly backups are enabled"
    )
    next_daily_backup: Optional[str] = Field(None, description="Next daily backup time")
    next_weekly_backup: Optional[str] = Field(
        None, description="Next weekly backup time"
    )
    next_monthly_backup: Optional[str] = Field(
        None, description="Next monthly backup time"
    )


class OrphanedStorageCheck(BaseModel):
    """Schema for orphaned storage check results."""

    has_orphaned_files: bool = Field(
        ..., description="Whether orphaned files were found"
    )
    orphaned_count: int = Field(..., description="Number of orphaned manga found")
    message: str = Field(..., description="Descriptive message")
    recovery_url: Optional[str] = Field(
        None, description="URL to recovery page if needed"
    )


class BackupMetadata(BaseModel):
    """Schema for backup metadata."""

    backup_name: str = Field(..., description="Name of the backup")
    created_at: str = Field(..., description="Creation timestamp")
    kuroibara_version: str = Field(
        ..., description="Version of Kuroibara that created the backup"
    )
    includes_storage: bool = Field(
        ..., description="Whether storage files are included"
    )
    database_size: int = Field(..., description="Size of database dump in bytes")
    storage_size: int = Field(..., description="Size of storage archive in bytes")


class BackupRestoreRequest(BaseModel):
    """Request schema for restoring from backup."""

    backup_filename: str = Field(..., description="Filename of backup to restore")
    confirm_overwrite: bool = Field(
        ..., description="Confirmation that user wants to overwrite current data"
    )


class BackupDeleteRequest(BaseModel):
    """Request schema for deleting a backup."""

    backup_filename: str = Field(..., description="Filename of backup to delete")
    confirm_delete: bool = Field(
        ..., description="Confirmation that user wants to delete the backup"
    )


class BackupValidationResult(BaseModel):
    """Schema for backup file validation results."""

    is_valid: bool = Field(..., description="Whether the backup file is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    metadata: Optional[BackupMetadata] = Field(
        None, description="Extracted backup metadata"
    )
    estimated_restore_time: Optional[str] = Field(
        None, description="Estimated time for restore"
    )


class BackupSettings(BaseModel):
    """Schema for backup configuration settings."""

    daily_enabled: bool = Field(True, description="Enable daily backups")
    weekly_enabled: bool = Field(True, description="Enable weekly backups")
    monthly_enabled: bool = Field(True, description="Enable monthly backups")
    max_backups: int = Field(30, description="Maximum number of backups to keep")
    backup_path: str = Field(
        "/app/backups", description="Path where backups are stored"
    )
    include_storage_daily: bool = Field(
        False, description="Include storage in daily backups"
    )
    include_storage_weekly: bool = Field(
        True, description="Include storage in weekly backups"
    )
    include_storage_monthly: bool = Field(
        True, description="Include storage in monthly backups"
    )


class BackupSettingsUpdate(BaseModel):
    """Schema for updating backup settings."""

    daily_enabled: Optional[bool] = None
    weekly_enabled: Optional[bool] = None
    monthly_enabled: Optional[bool] = None
    max_backups: Optional[int] = Field(None, ge=1, le=100)
    include_storage_daily: Optional[bool] = None
    include_storage_weekly: Optional[bool] = None
    include_storage_monthly: Optional[bool] = None


class BackupJobStatus(BaseModel):
    """Schema for backup job status."""

    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Type of backup job")
    status: str = Field(..., description="Current status")
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    started_at: Optional[str] = Field(None, description="Job start time")
    estimated_completion: Optional[str] = Field(
        None, description="Estimated completion time"
    )
    current_operation: Optional[str] = Field(
        None, description="Current operation being performed"
    )
    errors: List[str] = Field(
        default_factory=list, description="Any errors encountered"
    )


class BackupStatistics(BaseModel):
    """Schema for backup statistics."""

    total_backups: int = Field(..., description="Total number of backups")
    total_size: int = Field(..., description="Total size of all backups")
    oldest_backup: Optional[str] = Field(None, description="Date of oldest backup")
    newest_backup: Optional[str] = Field(None, description="Date of newest backup")
    daily_backups: int = Field(..., description="Number of daily backups")
    weekly_backups: int = Field(..., description="Number of weekly backups")
    monthly_backups: int = Field(..., description="Number of monthly backups")
    manual_backups: int = Field(..., description="Number of manual backups")
    average_backup_size: float = Field(..., description="Average backup size in bytes")

    @property
    def total_size_gb(self) -> float:
        """Get total size in gigabytes."""
        return round(self.total_size / (1024 * 1024 * 1024), 2)

    @property
    def average_backup_size_mb(self) -> float:
        """Get average backup size in megabytes."""
        return round(self.average_backup_size / (1024 * 1024), 2)
