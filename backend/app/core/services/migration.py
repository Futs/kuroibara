"""
Migration and validation tools for manga organization.

This module provides tools to migrate existing manga to the new organization
structure and validate file integrity.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.naming import naming_engine
from app.core.utils import get_manga_storage_path, is_image_file
from app.models.manga import Chapter, Manga
from app.models.organization import ChapterMetadata, MangaMetadata
from app.models.user import User

logger = logging.getLogger(__name__)


class MigrationTool:
    """
    Tool for migrating existing manga to new organization structure.
    """

    def __init__(self):
        """Initialize the migration tool."""
        self.naming_engine = naming_engine

    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash string or None if error
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    def validate_chapter_integrity(self, chapter: Chapter) -> Dict[str, any]:
        """
        Validate the integrity of a chapter's files.

        Args:
            chapter: Chapter object to validate

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_count": 0,
            "total_size": 0,
            "missing_files": [],
            "corrupted_files": [],
        }

        if not chapter.file_path:
            result["valid"] = False
            result["errors"].append("Chapter has no file path")
            return result

        if not os.path.exists(chapter.file_path):
            result["valid"] = False
            result["errors"].append(
                f"Chapter file/directory not found: {chapter.file_path}"
            )
            return result

        try:
            if os.path.isdir(chapter.file_path):
                # Validate directory of images
                image_files = []
                for root, _, files in os.walk(chapter.file_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if is_image_file(file_path):
                            image_files.append(file_path)
                            result["total_size"] += os.path.getsize(file_path)

                result["file_count"] = len(image_files)

                if result["file_count"] == 0:
                    result["valid"] = False
                    result["errors"].append("No image files found in chapter directory")

                # Check for common image file issues
                for img_file in image_files:
                    try:
                        # Try to get file size (basic corruption check)
                        size = os.path.getsize(img_file)
                        if size == 0:
                            result["corrupted_files"].append(img_file)
                            result["warnings"].append(
                                f"Zero-size image file: {img_file}"
                            )
                    except Exception as e:
                        result["corrupted_files"].append(img_file)
                        result["errors"].append(
                            f"Cannot access image file {img_file}: {e}"
                        )

            else:
                # Validate archive file
                result["file_count"] = 1
                result["total_size"] = os.path.getsize(chapter.file_path)

                # Basic archive validation
                file_ext = os.path.splitext(chapter.file_path)[1].lower()
                if file_ext not in [".cbz", ".cbr", ".zip", ".rar", ".7z"]:
                    result["warnings"].append(f"Unusual file extension: {file_ext}")

                if result["total_size"] == 0:
                    result["valid"] = False
                    result["errors"].append("Archive file is empty")

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error validating chapter: {str(e)}")

        return result

    async def scan_unorganized_manga(
        self, user: User, db: AsyncSession
    ) -> List[Dict[str, any]]:
        """
        Scan for manga that haven't been organized yet.

        Args:
            user: User object
            db: Database session

        Returns:
            List of unorganized manga with details
        """
        unorganized = []

        try:
            # Get all manga for user
            from app.models.library import MangaUserLibrary

            result = await db.execute(
                select(Manga)
                .join(MangaUserLibrary, Manga.id == MangaUserLibrary.manga_id)
                .where(MangaUserLibrary.user_id == user.id)
            )
            manga_list = result.scalars().all()

            for manga in manga_list:
                # Check if manga has metadata indicating organization
                metadata_result = await db.execute(
                    select(MangaMetadata).where(
                        (MangaMetadata.manga_id == manga.id)
                        & (MangaMetadata.user_id == user.id)
                    )
                )
                metadata = metadata_result.scalars().first()

                is_organized = metadata and metadata.is_organized

                if not is_organized:
                    # Get chapters for this manga
                    chapters_result = await db.execute(
                        select(Chapter).where(Chapter.manga_id == manga.id)
                    )
                    chapters = chapters_result.scalars().all()

                    # Check if any chapters exist in organized structure
                    organized_base = os.path.join(
                        get_manga_storage_path(manga.id), "organized"
                    )
                    has_organized_files = os.path.exists(organized_base) and os.listdir(
                        organized_base
                    )

                    manga_info = {
                        "manga_id": manga.id,
                        "title": manga.title,
                        "chapter_count": len(chapters),
                        "is_organized": is_organized,
                        "has_organized_files": has_organized_files,
                        "storage_path": get_manga_storage_path(manga.id),
                        "chapters": [],
                    }

                    # Validate each chapter
                    for chapter in chapters:
                        validation = self.validate_chapter_integrity(chapter)
                        chapter_info = {
                            "chapter_id": chapter.id,
                            "number": chapter.number,
                            "title": chapter.title,
                            "file_path": chapter.file_path,
                            "validation": validation,
                        }
                        manga_info["chapters"].append(chapter_info)

                    unorganized.append(manga_info)

        except Exception as e:
            logger.error(f"Error scanning unorganized manga: {e}")

        return unorganized

    async def create_migration_plan(
        self, manga_id: UUID, user: User, db: AsyncSession
    ) -> Dict[str, any]:
        """
        Create a migration plan for a specific manga.

        Args:
            manga_id: Manga ID to create plan for
            user: User object
            db: Database session

        Returns:
            Migration plan dictionary
        """
        plan = {
            "manga_id": manga_id,
            "valid": True,
            "errors": [],
            "warnings": [],
            "operations": [],
            "estimated_size": 0,
            "estimated_duration": 0,
        }

        try:
            manga = await db.get(Manga, manga_id)
            if not manga:
                plan["valid"] = False
                plan["errors"].append("Manga not found")
                return plan

            # Get chapters
            result = await db.execute(
                select(Chapter).where(Chapter.manga_id == manga_id)
            )
            chapters = result.scalars().all()

            if not chapters:
                plan["warnings"].append("No chapters found for manga")
                return plan

            # Plan operations for each chapter
            for chapter in chapters:
                validation = self.validate_chapter_integrity(chapter)

                if not validation["valid"]:
                    plan["errors"].extend(
                        [
                            f"Chapter {chapter.number}: {error}"
                            for error in validation["errors"]
                        ]
                    )
                    continue

                # Generate target paths
                organized_base = os.path.join(
                    get_manga_storage_path(manga.id), "organized"
                )
                relative_path = self.naming_engine.generate_manga_path(
                    manga, chapter, user.naming_format_manga
                )
                target_dir = os.path.join(organized_base, relative_path)

                chapter_filename = self.naming_engine.generate_chapter_filename(
                    manga, chapter, user.naming_format_chapter, include_extension=True
                )
                target_file = os.path.join(target_dir, chapter_filename)

                operation = {
                    "type": "organize_chapter",
                    "chapter_id": chapter.id,
                    "chapter_number": chapter.number,
                    "source_path": chapter.file_path,
                    "target_path": target_file,
                    "target_dir": target_dir,
                    "file_size": validation["total_size"],
                    "file_count": validation["file_count"],
                    "needs_cbz_conversion": user.create_cbz_files
                    and os.path.isdir(chapter.file_path),
                    "preserve_original": user.preserve_original_files,
                }

                plan["operations"].append(operation)
                plan["estimated_size"] += validation["total_size"]

                # Estimate duration (rough calculation)
                # ~1MB per second for file operations, +extra for CBZ conversion
                base_time = validation["total_size"] / (1024 * 1024)  # seconds
                if operation["needs_cbz_conversion"]:
                    base_time *= 2  # CBZ conversion takes extra time
                plan["estimated_duration"] += base_time

            if plan["errors"]:
                plan["valid"] = False

        except Exception as e:
            plan["valid"] = False
            plan["errors"].append(f"Error creating migration plan: {str(e)}")
            logger.error(f"Error creating migration plan for manga {manga_id}: {e}")

        return plan

    async def validate_organized_structure(
        self, manga_id: UUID, user: User, db: AsyncSession
    ) -> Dict[str, any]:
        """
        Validate that a manga's organized structure is correct.

        Args:
            manga_id: Manga ID to validate
            user: User object
            db: Database session

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "organized_chapters": 0,
            "missing_chapters": [],
            "extra_files": [],
        }

        try:
            manga = await db.get(Manga, manga_id)
            if not manga:
                result["valid"] = False
                result["errors"].append("Manga not found")
                return result

            # Get expected organized path
            organized_base = os.path.join(get_manga_storage_path(manga.id), "organized")

            if not os.path.exists(organized_base):
                result["valid"] = False
                result["errors"].append("Organized directory does not exist")
                return result

            # Get chapters from database
            chapters_result = await db.execute(
                select(Chapter).where(Chapter.manga_id == manga_id)
            )
            chapters = chapters_result.scalars().all()

            expected_files = set()

            # Check each chapter
            for chapter in chapters:
                relative_path = self.naming_engine.generate_manga_path(
                    manga, chapter, user.naming_format_manga
                )
                chapter_filename = self.naming_engine.generate_chapter_filename(
                    manga, chapter, user.naming_format_chapter, include_extension=True
                )
                expected_file = os.path.join(
                    organized_base, relative_path, chapter_filename
                )
                expected_files.add(expected_file)

                if os.path.exists(expected_file):
                    result["organized_chapters"] += 1
                else:
                    result["missing_chapters"].append(
                        {
                            "chapter_id": chapter.id,
                            "number": chapter.number,
                            "expected_path": expected_file,
                        }
                    )

            # Check for extra files
            for root, _, files in os.walk(organized_base):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path not in expected_files and not file.startswith("."):
                        result["extra_files"].append(file_path)

            if result["missing_chapters"]:
                result["valid"] = False
                result["errors"].append(
                    f"{len(result['missing_chapters'])} chapters missing from organized structure"
                )

            if result["extra_files"]:
                result["warnings"].append(
                    f"{len(result['extra_files'])} unexpected files found in organized structure"
                )

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error validating organized structure: {str(e)}")
            logger.error(
                f"Error validating organized structure for manga {manga_id}: {e}"
            )

        return result


# Global instance
migration_tool = MigrationTool()
