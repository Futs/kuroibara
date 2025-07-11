"""
File organization service for manga and chapter management.

This module handles the physical organization of manga files according to user-defined
naming conventions and folder structures.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.services.naming import naming_engine
from app.core.utils import create_cbz_from_directory, get_manga_storage_path
from app.models.manga import Chapter, Manga
from app.models.user import User

logger = logging.getLogger(__name__)


class OrganizationResult:
    """Result of an organization operation."""

    def __init__(self):
        self.success = True
        self.organized_files: List[str] = []
        self.created_directories: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, error: str):
        """Add an error to the result."""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str):
        """Add a warning to the result."""
        self.warnings.append(warning)

    def add_organized_file(self, file_path: str):
        """Add an organized file to the result."""
        self.organized_files.append(file_path)

    def add_created_directory(self, dir_path: str):
        """Add a created directory to the result."""
        self.created_directories.append(dir_path)


class MangaOrganizer:
    """
    Service for organizing manga files according to naming conventions.
    """

    def __init__(self):
        """Initialize the manga organizer."""
        self.naming_engine = naming_engine

    def get_organized_base_path(self, manga_id: UUID) -> str:
        """
        Get the base path for organized manga files.

        Args:
            manga_id: The manga UUID

        Returns:
            Base path for organized files
        """
        manga_storage = get_manga_storage_path(manga_id)
        return os.path.join(manga_storage, "organized")

    def get_raw_base_path(self, manga_id: UUID) -> str:
        """
        Get the base path for raw (original) manga files.

        Args:
            manga_id: The manga UUID

        Returns:
            Base path for raw files
        """
        manga_storage = get_manga_storage_path(manga_id)
        return os.path.join(manga_storage, "raw")

    def ensure_directory_exists(self, directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            True if directory exists or was created successfully
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {e}")
            return False

    def safe_move_file(self, source: str, destination: str) -> bool:
        """
        Safely move a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if move was successful
        """
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if not self.ensure_directory_exists(dest_dir):
                return False

            # If destination exists, create a unique name
            if os.path.exists(destination):
                base, ext = os.path.splitext(destination)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                destination = f"{base}_{counter}{ext}"

            shutil.move(source, destination)
            logger.info(f"Moved file from {source} to {destination}")
            return True

        except Exception as e:
            logger.error(f"Failed to move file from {source} to {destination}: {e}")
            return False

    def safe_copy_file(self, source: str, destination: str) -> bool:
        """
        Safely copy a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            True if copy was successful
        """
        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if not self.ensure_directory_exists(dest_dir):
                return False

            # If destination exists, create a unique name
            if os.path.exists(destination):
                base, ext = os.path.splitext(destination)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                destination = f"{base}_{counter}{ext}"

            shutil.copy2(source, destination)
            logger.info(f"Copied file from {source} to {destination}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy file from {source} to {destination}: {e}")
            return False

    async def organize_chapter(
        self,
        manga: Manga,
        chapter: Chapter,
        user: User,
        preserve_original: Optional[bool] = None,
    ) -> OrganizationResult:
        """
        Organize a single chapter according to user's naming preferences.

        Args:
            manga: The manga object
            chapter: The chapter object
            user: The user object with naming preferences
            preserve_original: Whether to preserve original files (overrides user setting)

        Returns:
            OrganizationResult with operation details
        """
        result = OrganizationResult()

        try:
            # Determine if we should preserve original files
            should_preserve = (
                preserve_original
                if preserve_original is not None
                else user.preserve_original_files
            )

            # Get current chapter file path
            if not chapter.file_path or not os.path.exists(chapter.file_path):
                result.add_error(f"Chapter file not found: {chapter.file_path}")
                return result

            # Generate organized path using user's naming format
            organized_base = self.get_organized_base_path(manga.id)
            relative_path = self.naming_engine.generate_manga_path(
                manga, chapter, user.naming_format_manga
            )
            organized_dir = os.path.join(organized_base, relative_path)

            # Generate chapter filename
            chapter_filename = self.naming_engine.generate_chapter_filename(
                manga, chapter, user.naming_format_chapter, include_extension=True
            )
            organized_file_path = os.path.join(organized_dir, chapter_filename)

            # Ensure organized directory exists
            if not self.ensure_directory_exists(organized_dir):
                result.add_error(
                    f"Failed to create organized directory: {organized_dir}"
                )
                return result

            result.add_created_directory(organized_dir)

            # Handle file organization based on user preferences
            if user.create_cbz_files:
                # Create CBZ file in organized location
                if os.path.isdir(chapter.file_path):
                    # Source is a directory, create CBZ from it
                    create_cbz_from_directory(chapter.file_path, organized_file_path)
                    result.add_organized_file(organized_file_path)

                    # Handle original directory
                    if not should_preserve:
                        try:
                            shutil.rmtree(chapter.file_path)
                            logger.info(
                                f"Removed original directory: {chapter.file_path}"
                            )
                        except Exception as e:
                            result.add_warning(
                                f"Failed to remove original directory: {e}"
                            )
                    else:
                        # Move to raw storage
                        raw_base = self.get_raw_base_path(manga.id)
                        raw_path = os.path.join(
                            raw_base, os.path.basename(chapter.file_path)
                        )
                        if self.safe_move_file(chapter.file_path, raw_path):
                            result.add_organized_file(raw_path)

                elif chapter.file_path.lower().endswith(
                    (".cbz", ".cbr", ".zip", ".rar", ".7z")
                ):
                    # Source is already an archive
                    if should_preserve:
                        # Copy to organized location
                        if self.safe_copy_file(chapter.file_path, organized_file_path):
                            result.add_organized_file(organized_file_path)
                    else:
                        # Move to organized location
                        if self.safe_move_file(chapter.file_path, organized_file_path):
                            result.add_organized_file(organized_file_path)

                else:
                    result.add_error(f"Unsupported file type: {chapter.file_path}")
                    return result

            else:
                # User doesn't want CBZ files, organize as-is
                if should_preserve:
                    if self.safe_copy_file(chapter.file_path, organized_file_path):
                        result.add_organized_file(organized_file_path)
                else:
                    if self.safe_move_file(chapter.file_path, organized_file_path):
                        result.add_organized_file(organized_file_path)

            # Update chapter file path in database
            chapter.file_path = organized_file_path

            logger.info(
                f"Successfully organized chapter {chapter.number} for manga {manga.title}"
            )

        except Exception as e:
            result.add_error(f"Unexpected error organizing chapter: {str(e)}")
            logger.error(f"Error organizing chapter {chapter.id}: {e}")

        return result


# Global instance
manga_organizer = MangaOrganizer()
