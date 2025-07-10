"""
Batch organization service for handling multiple manga/chapters.

This module provides functionality to organize multiple manga and chapters
in batch operations with progress tracking and error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.cbz_converter import cbz_converter
from app.core.services.organizer import manga_organizer
from app.db.session import AsyncSessionLocal
from app.models.manga import Chapter, Manga
from app.models.organization import OrganizationHistory, OrganizationJob
from app.models.user import User

logger = logging.getLogger(__name__)


class BatchOrganizer:
    """
    Service for batch organization operations with progress tracking.
    """
    
    def __init__(self):
        """Initialize the batch organizer."""
        self.organizer = manga_organizer
        self.cbz_converter = cbz_converter
    
    async def create_organization_job(
        self,
        user_id: UUID,
        job_type: str,
        total_items: int,
        job_config: Dict,
        db: AsyncSession
    ) -> OrganizationJob:
        """
        Create a new organization job.
        
        Args:
            user_id: User ID
            job_type: Type of job (organize_manga, organize_library, etc.)
            total_items: Total number of items to process
            job_config: Job configuration
            db: Database session
            
        Returns:
            Created organization job
        """
        job = OrganizationJob(
            user_id=user_id,
            job_type=job_type,
            job_status="pending",
            total_items=total_items,
            job_config=job_config,
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return job
    
    async def update_job_progress(
        self,
        job_id: UUID,
        processed_items: int,
        successful_items: int,
        failed_items: int,
        status: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> None:
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            processed_items: Number of processed items
            successful_items: Number of successful items
            failed_items: Number of failed items
            status: New job status (optional)
            db: Database session (optional, will create new if not provided)
        """
        if db is None:
            async with AsyncSessionLocal() as db:
                await self._update_job_progress_internal(
                    job_id, processed_items, successful_items, failed_items, status, db
                )
        else:
            await self._update_job_progress_internal(
                job_id, processed_items, successful_items, failed_items, status, db
            )
    
    async def _update_job_progress_internal(
        self,
        job_id: UUID,
        processed_items: int,
        successful_items: int,
        failed_items: int,
        status: Optional[str],
        db: AsyncSession
    ) -> None:
        """Internal method to update job progress."""
        update_data = {
            "processed_items": processed_items,
            "successful_items": successful_items,
            "failed_items": failed_items,
        }
        
        if status:
            update_data["job_status"] = status
            if status == "running" and not await self._job_has_started(job_id, db):
                update_data["started_at"] = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                update_data["completed_at"] = datetime.utcnow()
        
        await db.execute(
            update(OrganizationJob)
            .where(OrganizationJob.id == job_id)
            .values(**update_data)
        )
        await db.commit()
    
    async def _job_has_started(self, job_id: UUID, db: AsyncSession) -> bool:
        """Check if job has already started."""
        result = await db.execute(
            select(OrganizationJob.started_at).where(OrganizationJob.id == job_id)
        )
        started_at = result.scalar_one_or_none()
        return started_at is not None
    
    async def organize_manga_batch(
        self,
        manga_ids: List[UUID],
        user: User,
        job_id: UUID,
        preserve_original: Optional[bool] = None,
        custom_naming_format: Optional[str] = None
    ) -> Dict:
        """
        Organize multiple manga in batch.
        
        Args:
            manga_ids: List of manga IDs to organize
            user: User object
            job_id: Organization job ID
            preserve_original: Whether to preserve original files
            custom_naming_format: Custom naming format
            
        Returns:
            Summary of batch operation
        """
        async with AsyncSessionLocal() as db:
            try:
                await self.update_job_progress(job_id, 0, 0, 0, "running", db)
                
                total_chapters = 0
                processed_chapters = 0
                successful_chapters = 0
                failed_chapters = 0
                errors = []
                
                # Count total chapters first
                for manga_id in manga_ids:
                    result = await db.execute(
                        select(Chapter).where(Chapter.manga_id == manga_id)
                    )
                    chapters = result.scalars().all()
                    total_chapters += len(chapters)
                
                # Update job with actual total
                await db.execute(
                    update(OrganizationJob)
                    .where(OrganizationJob.id == job_id)
                    .values(total_items=total_chapters)
                )
                await db.commit()
                
                # Process each manga
                for manga_id in manga_ids:
                    try:
                        manga = await db.get(Manga, manga_id)
                        if not manga:
                            errors.append(f"Manga {manga_id} not found")
                            continue
                        
                        # Get chapters for this manga
                        result = await db.execute(
                            select(Chapter).where(Chapter.manga_id == manga_id)
                        )
                        chapters = result.scalars().all()
                        
                        # Organize each chapter
                        for chapter in chapters:
                            try:
                                result = await self.organizer.organize_chapter(
                                    manga=manga,
                                    chapter=chapter,
                                    user=user,
                                    preserve_original=preserve_original
                                )
                                
                                if result.success:
                                    successful_chapters += 1
                                    
                                    # Create history entry
                                    history = OrganizationHistory(
                                        user_id=user.id,
                                        manga_id=manga.id,
                                        chapter_id=chapter.id,
                                        operation_type="organize_chapter",
                                        operation_status="success",
                                        source_path=chapter.file_path,
                                        destination_path=result.organized_files[0] if result.organized_files else None,
                                        naming_format_used=custom_naming_format or user.naming_format_manga,
                                        files_processed=len(result.organized_files),
                                        operation_details={"job_id": str(job_id)},
                                        started_at=datetime.utcnow(),
                                        completed_at=datetime.utcnow(),
                                    )
                                    db.add(history)
                                else:
                                    failed_chapters += 1
                                    errors.extend(result.errors)
                                    
                                    # Create failed history entry
                                    history = OrganizationHistory(
                                        user_id=user.id,
                                        manga_id=manga.id,
                                        chapter_id=chapter.id,
                                        operation_type="organize_chapter",
                                        operation_status="failed",
                                        source_path=chapter.file_path,
                                        naming_format_used=custom_naming_format or user.naming_format_manga,
                                        files_processed=0,
                                        errors_encountered=result.errors,
                                        warnings_encountered=result.warnings,
                                        operation_details={"job_id": str(job_id)},
                                        started_at=datetime.utcnow(),
                                        completed_at=datetime.utcnow(),
                                    )
                                    db.add(history)
                                
                                processed_chapters += 1
                                
                                # Update progress every 10 chapters or at the end
                                if processed_chapters % 10 == 0 or processed_chapters == total_chapters:
                                    await self.update_job_progress(
                                        job_id, processed_chapters, successful_chapters, failed_chapters, db=db
                                    )
                                
                            except Exception as e:
                                failed_chapters += 1
                                processed_chapters += 1
                                error_msg = f"Error organizing chapter {chapter.id}: {str(e)}"
                                errors.append(error_msg)
                                logger.error(error_msg)
                        
                        await db.commit()
                        
                    except Exception as e:
                        error_msg = f"Error processing manga {manga_id}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                
                # Final job update
                final_status = "completed" if failed_chapters == 0 else "partial"
                await self.update_job_progress(
                    job_id, processed_chapters, successful_chapters, failed_chapters, final_status, db
                )
                
                # Update job with summary
                summary = {
                    "total_chapters": total_chapters,
                    "successful_chapters": successful_chapters,
                    "failed_chapters": failed_chapters,
                    "errors": errors[:50],  # Limit errors to prevent huge payloads
                }
                
                await db.execute(
                    update(OrganizationJob)
                    .where(OrganizationJob.id == job_id)
                    .values(
                        result_summary=summary,
                        error_log={"errors": errors} if errors else None
                    )
                )
                await db.commit()
                
                return summary
                
            except Exception as e:
                logger.error(f"Batch organization job {job_id} failed: {e}")
                await self.update_job_progress(job_id, 0, 0, 0, "failed", db)
                raise
    
    async def organize_user_library(
        self,
        user: User,
        job_id: UUID,
        preserve_original: Optional[bool] = None,
        custom_naming_format: Optional[str] = None
    ) -> Dict:
        """
        Organize entire user library.
        
        Args:
            user: User object
            job_id: Organization job ID
            preserve_original: Whether to preserve original files
            custom_naming_format: Custom naming format
            
        Returns:
            Summary of batch operation
        """
        async with AsyncSessionLocal() as db:
            # Get all manga for user (through library)
            from app.models.library import MangaUserLibrary
            
            result = await db.execute(
                select(MangaUserLibrary.manga_id)
                .where(MangaUserLibrary.user_id == user.id)
            )
            manga_ids = [row[0] for row in result.fetchall()]
            
            return await self.organize_manga_batch(
                manga_ids, user, job_id, preserve_original, custom_naming_format
            )


# Global instance
batch_organizer = BatchOrganizer()
