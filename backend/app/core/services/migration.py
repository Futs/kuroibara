"""
Migration and validation tools for manga organization.

This module provides tools to migrate existing manga to the new organization
structure and validate file integrity. Enhanced with smart pattern detection
and structure migration capabilities.
"""

import hashlib
import logging
import os
import shutil
from datetime import datetime
from typing import Callable, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.naming import naming_engine
from app.core.utils import get_manga_storage_path, is_image_file
from app.models.manga import Chapter, Manga
from app.models.organization import MangaMetadata
from app.models.user import User

logger = logging.getLogger(__name__)


class MigrationPlan:
    """Represents a migration plan for reorganizing manga files."""

    def __init__(self):
        self.manga_id: Optional[UUID] = None
        self.manga_title: str = ""
        self.source_pattern: str = ""
        self.target_pattern: str = ""
        self.operations: List[Dict] = []
        self.estimated_size: int = 0
        self.estimated_time: int = 0  # seconds
        self.risks: List[str] = []
        self.warnings: List[str] = []
        self.can_rollback: bool = True
        self.backup_required: bool = True

    def add_operation(
        self,
        operation_type: str,
        source: str,
        target: str,
        chapter_id: UUID,
        file_size: int = 0,
    ):
        """Add a file operation to the migration plan."""
        self.operations.append(
            {
                "type": operation_type,  # "move", "copy", "create_dir"
                "source": source,
                "target": target,
                "chapter_id": str(chapter_id),
                "file_size": file_size,
                "status": "pending",
            }
        )
        self.estimated_size += file_size

    def get_summary(self) -> Dict:
        """Get a summary of the migration plan."""
        return {
            "manga_title": self.manga_title,
            "source_pattern": self.source_pattern,
            "target_pattern": self.target_pattern,
            "total_operations": len(self.operations),
            "estimated_size_mb": round(self.estimated_size / (1024 * 1024), 2),
            "estimated_time_minutes": round(self.estimated_time / 60, 1),
            "risks": self.risks,
            "warnings": self.warnings,
            "can_rollback": self.can_rollback,
            "backup_required": self.backup_required,
        }


class MigrationTool:
    """
    Enhanced tool for migrating existing manga to new organization structure.

    Provides functionality to migrate existing manga to new organization
    structures, validate file integrity, and handle structure changes safely.
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

    async def create_structure_migration_plan(
        self,
        manga: Manga,
        user: User,
        new_template: str,
        db: AsyncSession,
        preserve_original: bool = True,
    ) -> MigrationPlan:
        """
        Create a migration plan for changing folder structure.

        Args:
            manga: Manga to migrate
            user: User requesting migration
            new_template: New naming template to use
            db: Database session
            preserve_original: Whether to preserve original files

        Returns:
            MigrationPlan with detailed operations
        """
        plan = MigrationPlan()
        plan.manga_id = manga.id
        plan.manga_title = getattr(manga, "title", "Unknown")
        plan.source_pattern = user.naming_format_manga
        plan.target_pattern = new_template
        plan.backup_required = not preserve_original

        # Get all chapters for this manga
        chapters_query = select(Chapter).where(Chapter.manga_id == manga.id)
        chapters_result = await db.execute(chapters_query)
        chapters = chapters_result.scalars().all()

        if not chapters:
            plan.warnings.append("No chapters found for this manga")
            return plan

        # Analyze current volume usage
        volume_analysis = await self.naming_engine.analyze_manga_volume_usage(manga, db)

        # Check if new template is appropriate
        recommended_template = self.naming_engine.get_recommended_template(
            volume_analysis
        )
        if new_template != recommended_template:
            confidence = volume_analysis.confidence_score
            if confidence > 0.7:
                plan.warnings.append(
                    f"Template '{new_template}' may not be optimal for this manga. "
                    f"Recommended: '{recommended_template}' (confidence: {confidence:.1%})"
                )

        # Plan operations for each chapter
        manga_storage_base = get_manga_storage_path(manga.id)
        organized_base = os.path.join(manga_storage_base, "organized")

        for chapter in chapters:
            # Current path
            current_relative = self.naming_engine.generate_manga_path(
                manga, chapter, user.naming_format_manga
            )
            current_filename = self.naming_engine.generate_chapter_filename(
                manga, chapter, user.naming_format_chapter, include_extension=True
            )
            current_path = os.path.join(
                organized_base, current_relative, current_filename
            )

            # New path
            new_relative = self.naming_engine.generate_manga_path(
                manga, chapter, new_template
            )
            new_filename = self.naming_engine.generate_chapter_filename(
                manga, chapter, user.naming_format_chapter, include_extension=True
            )
            new_path = os.path.join(organized_base, new_relative, new_filename)

            # Skip if paths are the same
            if current_path == new_path:
                continue

            # Check if source file exists
            if not os.path.exists(current_path):
                plan.warnings.append(f"Source file not found: {current_path}")
                continue

            # Get file size
            try:
                file_size = os.path.getsize(current_path)
            except OSError:
                file_size = 0
                plan.warnings.append(f"Could not get size for: {current_path}")

            # Add directory creation operation if needed
            new_dir = os.path.dirname(new_path)
            if not any(
                op["target"] == new_dir and op["type"] == "create_dir"
                for op in plan.operations
            ):
                plan.add_operation("create_dir", "", new_dir, chapter.id, 0)

            # Add file operation
            operation_type = "copy" if preserve_original else "move"
            plan.add_operation(
                operation_type, current_path, new_path, chapter.id, file_size
            )

        # Calculate estimated time (rough estimate: 1MB per second)
        plan.estimated_time = max(30, plan.estimated_size // (1024 * 1024))

        # Add risks and warnings
        if not preserve_original:
            plan.risks.append("Original files will be moved (not copied)")
            plan.can_rollback = False

        if plan.estimated_size > 10 * 1024 * 1024 * 1024:  # 10GB
            plan.warnings.append(
                "Large migration (>10GB) - consider running during off-peak hours"
            )

        return plan

    async def execute_migration_plan(
        self,
        plan: MigrationPlan,
        db: AsyncSession,
        progress_callback: Optional[Callable] = None,
    ) -> Dict:
        """
        Execute a migration plan.

        Args:
            plan: MigrationPlan to execute
            db: Database session
            progress_callback: Optional callback for progress updates

        Returns:
            Execution result dictionary
        """
        result = {
            "success": True,
            "completed_operations": 0,
            "failed_operations": 0,
            "errors": [],
            "warnings": [],
            "rollback_info": [],
        }

        if not plan.operations:
            result["warnings"].append("No operations to execute")
            return result

        total_operations = len(plan.operations)

        try:
            # Create backup info for rollback
            if plan.backup_required and plan.manga_id:
                backup_dir = os.path.join(
                    get_manga_storage_path(plan.manga_id),
                    f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )
                os.makedirs(backup_dir, exist_ok=True)
                result["rollback_info"].append(f"Backup directory: {backup_dir}")

            for i, operation in enumerate(plan.operations):
                try:
                    if operation["type"] == "create_dir":
                        os.makedirs(operation["target"], exist_ok=True)
                        operation["status"] = "completed"

                    elif operation["type"] == "copy":
                        # Ensure target directory exists
                        os.makedirs(os.path.dirname(operation["target"]), exist_ok=True)
                        shutil.copy2(operation["source"], operation["target"])
                        operation["status"] = "completed"

                    elif operation["type"] == "move":
                        # Create backup if needed
                        if plan.backup_required:
                            backup_path = os.path.join(
                                backup_dir, os.path.basename(operation["source"])
                            )
                            shutil.copy2(operation["source"], backup_path)
                            result["rollback_info"].append(f"Backed up: {backup_path}")

                        # Ensure target directory exists
                        os.makedirs(os.path.dirname(operation["target"]), exist_ok=True)
                        shutil.move(operation["source"], operation["target"])
                        operation["status"] = "completed"

                        # Update database with new path
                        chapter_id = UUID(operation["chapter_id"])
                        chapter_query = select(Chapter).where(Chapter.id == chapter_id)
                        chapter_result = await db.execute(chapter_query)
                        chapter = chapter_result.scalar_one_or_none()

                        if chapter:
                            chapter.file_path = operation["target"]
                            await db.commit()

                    result["completed_operations"] += 1

                    # Progress callback
                    if progress_callback:
                        progress = (i + 1) / total_operations
                        progress_callback(
                            progress, f"Completed operation {i + 1}/{total_operations}"
                        )

                except Exception as e:
                    operation["status"] = "failed"
                    operation["error"] = str(e)
                    result["failed_operations"] += 1
                    result["errors"].append(f"Operation {i + 1} failed: {str(e)}")
                    logger.error(f"Migration operation failed: {e}")

                    # Decide whether to continue or abort
                    if (
                        result["failed_operations"] > total_operations * 0.1
                    ):  # More than 10% failed
                        result["success"] = False
                        result["errors"].append(
                            "Too many operations failed, aborting migration"
                        )
                        break

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Migration execution failed: {str(e)}")
            logger.error(f"Migration execution failed: {e}")

        return result

    async def rollback_migration(
        self, plan: MigrationPlan, rollback_info: List[str], db: AsyncSession
    ) -> Dict:
        """
        Rollback a migration using backup information.

        Args:
            plan: Original migration plan
            rollback_info: Rollback information from execution
            db: Database session

        Returns:
            Rollback result dictionary
        """
        result = {"success": True, "restored_files": 0, "errors": []}

        if not plan.can_rollback:
            result["success"] = False
            result["errors"].append("Migration cannot be rolled back")
            return result

        try:
            # Find backup directory from rollback info
            backup_dir = None
            for info in rollback_info:
                if info.startswith("Backup directory:"):
                    backup_dir = info.split(": ", 1)[1]
                    break

            if not backup_dir or not os.path.exists(backup_dir):
                result["success"] = False
                result["errors"].append("Backup directory not found")
                return result

            # Restore files from backup
            for operation in plan.operations:
                if operation["status"] == "completed" and operation["type"] in [
                    "move",
                    "copy",
                ]:
                    try:
                        backup_file = os.path.join(
                            backup_dir, os.path.basename(operation["source"])
                        )
                        if os.path.exists(backup_file):
                            # Restore original file
                            os.makedirs(
                                os.path.dirname(operation["source"]), exist_ok=True
                            )
                            shutil.copy2(backup_file, operation["source"])

                            # Remove new file if it exists
                            if os.path.exists(operation["target"]):
                                os.remove(operation["target"])

                            # Update database
                            chapter_id = UUID(operation["chapter_id"])
                            chapter_query = select(Chapter).where(
                                Chapter.id == chapter_id
                            )
                            chapter_result = await db.execute(chapter_query)
                            chapter = chapter_result.scalar_one_or_none()

                            if chapter:
                                chapter.file_path = operation["source"]

                            result["restored_files"] += 1

                    except Exception as e:
                        result["errors"].append(
                            f"Failed to restore {operation['source']}: {str(e)}"
                        )

            await db.commit()

            # Clean up backup directory
            try:
                shutil.rmtree(backup_dir)
            except Exception as e:
                result["errors"].append(
                    f"Failed to clean up backup directory: {str(e)}"
                )

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Rollback failed: {str(e)}")
            logger.error(f"Migration rollback failed: {e}")

        return result


# Global instance
migration_tool = MigrationTool()
