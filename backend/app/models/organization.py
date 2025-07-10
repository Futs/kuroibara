"""
Organization and metadata tracking models.

These models provide enhanced metadata tracking for manga organization,
replacing JSON file-based tracking with database-backed solutions.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MangaMetadata(BaseModel):
    """
    Enhanced metadata for manga organization and display.
    
    This replaces JSON file-based metadata tracking with database storage.
    """
    
    __tablename__ = "manga_metadata"
    
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Display customization
    display_name = Column(String(255), nullable=True)  # Custom display name override
    custom_cover_url = Column(String(500), nullable=True)  # Custom cover image URL
    custom_description = Column(Text, nullable=True)  # Custom description override
    
    # Organization settings
    is_organized = Column(Boolean, default=False, nullable=False)  # Whether manga is organized
    organization_format = Column(String(500), nullable=True)  # Format used for organization
    last_organized_at = Column(DateTime, nullable=True)  # When last organized
    
    # Reading tracking
    last_read_at = Column(DateTime, nullable=True)  # When last read
    reading_status = Column(String(20), default="unread", nullable=False)  # unread, reading, completed, dropped
    
    # Custom metadata
    custom_metadata = Column(JSONB, nullable=True)  # Additional custom metadata
    
    # Relationships
    manga = relationship("Manga", back_populates="manga_metadata")
    user = relationship("User")


class ChapterMetadata(BaseModel):
    """
    Enhanced metadata for chapter organization and tracking.
    """
    
    __tablename__ = "chapter_metadata"
    
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Display customization
    display_name = Column(String(255), nullable=True)  # Custom chapter name override
    custom_cover_url = Column(String(500), nullable=True)  # Custom chapter cover
    
    # Organization tracking
    is_organized = Column(Boolean, default=False, nullable=False)  # Whether chapter is organized
    organized_path = Column(String(500), nullable=True)  # Path after organization
    original_path = Column(String(500), nullable=True)  # Original file path (if preserved)
    cbz_path = Column(String(500), nullable=True)  # Path to CBZ file
    
    # Reading progress
    current_page = Column(Integer, default=1, nullable=False)  # Current reading page
    total_pages = Column(Integer, nullable=True)  # Total pages in chapter
    reading_progress = Column(Integer, default=0, nullable=False)  # Progress percentage (0-100)
    last_read_at = Column(DateTime, nullable=True)  # When last read
    is_completed = Column(Boolean, default=False, nullable=False)  # Whether chapter is completed
    
    # Custom metadata
    custom_metadata = Column(JSONB, nullable=True)  # Additional custom metadata
    
    # Relationships
    chapter = relationship("Chapter", back_populates="chapter_metadata")
    user = relationship("User")


class OrganizationHistory(BaseModel):
    """
    Track organization operations for audit and rollback purposes.
    """
    
    __tablename__ = "organization_history"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    manga_id = Column(UUID(as_uuid=True), ForeignKey("manga.id"), nullable=True)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapter.id"), nullable=True)
    
    # Operation details
    operation_type = Column(String(50), nullable=False)  # organize, rename, convert_cbz, etc.
    operation_status = Column(String(20), nullable=False)  # success, failed, partial
    
    # File operations
    source_path = Column(String(500), nullable=True)  # Original file/directory path
    destination_path = Column(String(500), nullable=True)  # New file/directory path
    backup_path = Column(String(500), nullable=True)  # Backup location (if preserved)
    
    # Operation metadata
    naming_format_used = Column(String(500), nullable=True)  # Naming format used
    files_processed = Column(Integer, default=0, nullable=False)  # Number of files processed
    errors_encountered = Column(JSONB, nullable=True)  # List of errors during operation
    warnings_encountered = Column(JSONB, nullable=True)  # List of warnings during operation
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Operation duration
    
    # Additional details
    operation_details = Column(JSONB, nullable=True)  # Additional operation-specific data
    
    # Relationships
    user = relationship("User")
    manga = relationship("Manga")
    chapter = relationship("Chapter")


class OrganizationJob(BaseModel):
    """
    Track batch organization jobs for progress monitoring.
    """
    
    __tablename__ = "organization_jobs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # organize_manga, organize_library, convert_cbz, etc.
    job_status = Column(String(20), default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    
    # Progress tracking
    total_items = Column(Integer, default=0, nullable=False)  # Total items to process
    processed_items = Column(Integer, default=0, nullable=False)  # Items processed so far
    successful_items = Column(Integer, default=0, nullable=False)  # Successfully processed items
    failed_items = Column(Integer, default=0, nullable=False)  # Failed items
    
    # Job configuration
    job_config = Column(JSONB, nullable=True)  # Job-specific configuration
    naming_format_manga = Column(String(500), nullable=True)  # Manga naming format used
    naming_format_chapter = Column(String(500), nullable=True)  # Chapter naming format used
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_completion = Column(DateTime, nullable=True)  # Estimated completion time
    
    # Results
    result_summary = Column(JSONB, nullable=True)  # Summary of job results
    error_log = Column(JSONB, nullable=True)  # Detailed error log
    
    # Relationships
    user = relationship("User")
    history_entries = relationship("OrganizationHistory", 
                                 primaryjoin="OrganizationJob.id == foreign(OrganizationHistory.operation_details['job_id'].astext.cast(UUID))",
                                 viewonly=True)
