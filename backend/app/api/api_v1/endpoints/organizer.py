"""
API endpoints for manga organization and naming management.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.services.batch_organizer import batch_organizer
from app.core.services.migration import migration_tool, MigrationPlan
from app.core.services.naming import naming_engine
from app.core.services.organizer import manga_organizer
from app.core.services.storage_recovery import storage_recovery_service
from app.db.session import AsyncSessionLocal
from app.models.manga import Chapter, Manga
from app.models.organization import (
    OrganizationJob,
)
from app.models.user import User
from app.schemas.organization import (
    BatchOrganizeRequest,
    BatchRecoveryRequest,
    BatchRecoveryResponse,
    NamingFormatValidation,
    NamingFormatValidationResponse,
    NamingSettings,
    NamingSettingsUpdate,
    OrganizationResult,
    OrganizeChapterRequest,
    OrganizeMangaRequest,
    RecoverableManga,
    RecoverMangaRequest,
    RecoverMangaResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/validate-naming-format", response_model=NamingFormatValidationResponse)
async def validate_naming_format(
    validation_request: NamingFormatValidation,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Validate a naming format template.
    """
    is_valid, error_message = naming_engine.validate_template(
        validation_request.template
    )

    sample_output = None
    if is_valid:
        # Generate sample output with test data
        sample_context = {
            "Manga Title": "Sample Manga",
            "Volume": "1",
            "Chapter Number": "1",
            "Chapter Name": "Sample Chapter",
            "Language": "en",
            "Year": "2023",
            "Source": "test",
        }
        sample_output = naming_engine.apply_template(
            validation_request.template, sample_context
        )

    return NamingFormatValidationResponse(
        is_valid=is_valid, error_message=error_message, sample_output=sample_output
    )


@router.get("/naming-settings", response_model=NamingSettings)
async def get_naming_settings(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's naming settings.
    """
    return NamingSettings(
        naming_format_manga=current_user.naming_format_manga,
        naming_format_chapter=current_user.naming_format_chapter,
        auto_organize_imports=current_user.auto_organize_imports,
        create_cbz_files=current_user.create_cbz_files,
        preserve_original_files=current_user.preserve_original_files,
    )


@router.put("/naming-settings", response_model=NamingSettings)
async def update_naming_settings(
    settings_update: NamingSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update user's naming settings.
    """
    # Validate naming formats if provided
    if settings_update.naming_format_manga:
        is_valid, error_message = naming_engine.validate_template(
            settings_update.naming_format_manga
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid manga naming format: {error_message}",
            )

    if settings_update.naming_format_chapter:
        is_valid, error_message = naming_engine.validate_template(
            settings_update.naming_format_chapter
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chapter naming format: {error_message}",
            )

    # Update user settings
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return NamingSettings(
        naming_format_manga=current_user.naming_format_manga,
        naming_format_chapter=current_user.naming_format_chapter,
        auto_organize_imports=current_user.auto_organize_imports,
        create_cbz_files=current_user.create_cbz_files,
        preserve_original_files=current_user.preserve_original_files,
    )


@router.post("/organize/chapter", response_model=OrganizationResult)
async def organize_chapter(
    request: OrganizeChapterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Organize a single chapter.
    """
    # Get chapter and manga
    chapter = await db.get(Chapter, request.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found"
        )

    manga = await db.get(Manga, chapter.manga_id)
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Manga not found"
        )

    # Perform organization
    try:
        result = await manga_organizer.organize_chapter(
            manga=manga,
            chapter=chapter,
            user=current_user,
            preserve_original=request.preserve_original,
        )

        # Update database if successful
        if result.success:
            await db.commit()

        return OrganizationResult(
            success=result.success,
            organized_files=result.organized_files,
            created_directories=result.created_directories,
            errors=result.errors,
            warnings=result.warnings,
        )

    except Exception as e:
        logger.error(f"Error organizing chapter {request.chapter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to organize chapter: {str(e)}",
        )


@router.post("/organize/manga", response_model=Dict[str, Any])
async def organize_manga(
    request: OrganizeMangaRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Organize all chapters of a manga (background task).
    """
    # Get manga
    manga = await db.get(Manga, request.manga_id)
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Manga not found"
        )

    # Get chapters
    result = await db.execute(
        select(Chapter).where(Chapter.manga_id == request.manga_id)
    )
    chapters = result.scalars().all()

    if not chapters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chapters found for this manga",
        )

    # Create organization job
    job = OrganizationJob(
        user_id=current_user.id,
        job_type="organize_manga",
        job_status="pending",
        total_items=len(chapters),
        job_config={
            "manga_id": str(request.manga_id),
            "preserve_original": request.preserve_original,
            "custom_naming_format": request.custom_naming_format,
        },
        naming_format_manga=request.custom_naming_format
        or current_user.naming_format_manga,
        naming_format_chapter=current_user.naming_format_chapter,
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Add background task
    background_tasks.add_task(
        organize_manga_background,
        job_id=job.id,
        manga_id=request.manga_id,
        preserve_original=request.preserve_original,
        custom_naming_format=request.custom_naming_format,
    )

    return {
        "message": "Organization job started",
        "job_id": job.id,
        "total_chapters": len(chapters),
    }


@router.post("/organize/batch", response_model=Dict[str, Any])
async def organize_batch(
    request: BatchOrganizeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Organize multiple manga/chapters in batch (background task).
    """
    total_items = 0
    job_config = {
        "preserve_original": request.preserve_original,
        "custom_naming_format": request.custom_naming_format,
    }

    if request.organize_all_library:
        # Count total chapters in user library
        from app.models.library import MangaUserLibrary

        result = await db.execute(
            select(Chapter.id)
            .join(Manga, Chapter.manga_id == Manga.id)
            .join(MangaUserLibrary, Manga.id == MangaUserLibrary.manga_id)
            .where(MangaUserLibrary.user_id == current_user.id)
        )
        total_items = len(result.fetchall())
        job_type = "organize_library"
        job_config["organize_all_library"] = True

    elif request.manga_ids:
        # Count chapters in specified manga
        result = await db.execute(
            select(Chapter.id).where(Chapter.manga_id.in_(request.manga_ids))
        )
        total_items = len(result.fetchall())
        job_type = "organize_manga_batch"
        job_config["manga_ids"] = [str(mid) for mid in request.manga_ids]

    elif request.chapter_ids:
        total_items = len(request.chapter_ids)
        job_type = "organize_chapters_batch"
        job_config["chapter_ids"] = [str(cid) for cid in request.chapter_ids]

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify manga_ids, chapter_ids, or organize_all_library",
        )

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No items found to organize"
        )

    # Create organization job
    job = await batch_organizer.create_organization_job(
        user_id=current_user.id,
        job_type=job_type,
        total_items=total_items,
        job_config=job_config,
        db=db,
    )

    # Add background task
    if request.organize_all_library:
        background_tasks.add_task(
            organize_library_background,
            user_id=current_user.id,
            job_id=job.id,
            preserve_original=request.preserve_original,
            custom_naming_format=request.custom_naming_format,
        )
    elif request.manga_ids:
        background_tasks.add_task(
            organize_manga_batch_background,
            manga_ids=request.manga_ids,
            user_id=current_user.id,
            job_id=job.id,
            preserve_original=request.preserve_original,
            custom_naming_format=request.custom_naming_format,
        )
    elif request.chapter_ids:
        background_tasks.add_task(
            organize_chapters_batch_background,
            chapter_ids=request.chapter_ids,
            user_id=current_user.id,
            job_id=job.id,
            preserve_original=request.preserve_original,
            custom_naming_format=request.custom_naming_format,
        )

    return {
        "message": "Batch organization job started",
        "job_id": job.id,
        "job_type": job_type,
        "total_items": total_items,
    }


async def organize_manga_background(
    job_id: UUID,
    manga_id: UUID,
    preserve_original: Optional[bool] = None,
    custom_naming_format: Optional[str] = None,
) -> None:
    """
    Background task for organizing manga chapters.
    """
    try:
        async with AsyncSessionLocal() as db:
            user = await db.execute(
                select(User).join(OrganizationJob).where(OrganizationJob.id == job_id)
            )
            user = user.scalars().first()

            if user:
                await batch_organizer.organize_manga_batch(
                    manga_ids=[manga_id],
                    user=user,
                    job_id=job_id,
                    preserve_original=preserve_original,
                    custom_naming_format=custom_naming_format,
                )
    except Exception as e:
        logger.error(f"Background organization job {job_id} failed: {e}")


async def organize_manga_batch_background(
    manga_ids: List[UUID],
    user_id: UUID,
    job_id: UUID,
    preserve_original: Optional[bool] = None,
    custom_naming_format: Optional[str] = None,
) -> None:
    """
    Background task for organizing multiple manga.
    """
    try:
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
            if user:
                await batch_organizer.organize_manga_batch(
                    manga_ids=manga_ids,
                    user=user,
                    job_id=job_id,
                    preserve_original=preserve_original,
                    custom_naming_format=custom_naming_format,
                )
    except Exception as e:
        logger.error(f"Background batch organization job {job_id} failed: {e}")


async def organize_library_background(
    user_id: UUID,
    job_id: UUID,
    preserve_original: Optional[bool] = None,
    custom_naming_format: Optional[str] = None,
) -> None:
    """
    Background task for organizing entire user library.
    """
    try:
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
            if user:
                await batch_organizer.organize_user_library(
                    user=user,
                    job_id=job_id,
                    preserve_original=preserve_original,
                    custom_naming_format=custom_naming_format,
                )
    except Exception as e:
        logger.error(f"Background library organization job {job_id} failed: {e}")


async def organize_chapters_batch_background(
    chapter_ids: List[UUID],
    user_id: UUID,
    job_id: UUID,
    preserve_original: Optional[bool] = None,
    custom_naming_format: Optional[str] = None,
) -> None:
    """
    Background task for organizing multiple chapters.
    """
    try:
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
            if not user:
                return

            await batch_organizer.update_job_progress(job_id, 0, 0, 0, "running")

            processed = 0
            successful = 0
            failed = 0

            for chapter_id in chapter_ids:
                try:
                    chapter = await db.get(Chapter, chapter_id)
                    if not chapter:
                        failed += 1
                        continue

                    manga = await db.get(Manga, chapter.manga_id)
                    if not manga:
                        failed += 1
                        continue

                    result = await manga_organizer.organize_chapter(
                        manga=manga,
                        chapter=chapter,
                        user=user,
                        preserve_original=preserve_original,
                    )

                    if result.success:
                        successful += 1
                    else:
                        failed += 1

                    processed += 1

                    # Update progress every 10 items
                    if processed % 10 == 0:
                        await batch_organizer.update_job_progress(
                            job_id, processed, successful, failed
                        )

                except Exception as e:
                    failed += 1
                    processed += 1
                    logger.error(f"Error organizing chapter {chapter_id}: {e}")

            # Final update
            final_status = "completed" if failed == 0 else "partial"
            await batch_organizer.update_job_progress(
                job_id, processed, successful, failed, final_status
            )

    except Exception as e:
        logger.error(f"Background chapters batch organization job {job_id} failed: {e}")


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_organization_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get user's organization jobs.
    """
    result = await db.execute(
        select(OrganizationJob)
        .where(OrganizationJob.user_id == current_user.id)
        .order_by(OrganizationJob.created_at.desc())
        .limit(50)
    )
    jobs = result.scalars().all()

    return [
        {
            "id": job.id,
            "job_type": job.job_type,
            "job_status": job.job_status,
            "progress_percentage": job.progress_percentage,
            "total_items": job.total_items,
            "processed_items": job.processed_items,
            "successful_items": job.successful_items,
            "failed_items": job.failed_items,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "estimated_completion": job.estimated_completion,
        }
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_organization_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get details of a specific organization job.
    """
    job = await db.get(OrganizationJob, job_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization job not found"
        )

    return {
        "id": job.id,
        "job_type": job.job_type,
        "job_status": job.job_status,
        "progress_percentage": job.progress_percentage,
        "total_items": job.total_items,
        "processed_items": job.processed_items,
        "successful_items": job.successful_items,
        "failed_items": job.failed_items,
        "job_config": job.job_config,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "estimated_completion": job.estimated_completion,
        "result_summary": job.result_summary,
        "error_log": job.error_log,
    }


@router.get("/migration/scan", response_model=List[Dict[str, Any]])
async def scan_unorganized_manga(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Scan for manga that haven't been organized yet.
    """
    try:
        unorganized = await migration_tool.scan_unorganized_manga(current_user, db)
        return unorganized
    except Exception as e:
        logger.error(f"Error scanning unorganized manga: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan unorganized manga: {str(e)}",
        )


@router.get("/migration/plan/{manga_id}", response_model=Dict[str, Any])
async def get_migration_plan(
    manga_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get migration plan for a specific manga.
    """
    try:
        plan = await migration_tool.create_migration_plan(manga_id, current_user, db)
        return plan
    except Exception as e:
        logger.error(f"Error creating migration plan for manga {manga_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create migration plan: {str(e)}",
        )


@router.get("/validation/{manga_id}", response_model=Dict[str, Any])
async def validate_manga_organization(
    manga_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Validate the organization structure of a manga.
    """
    try:
        validation = await migration_tool.validate_organized_structure(
            manga_id, current_user, db
        )
        return validation
    except Exception as e:
        logger.error(f"Error validating manga {manga_id} organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate manga organization: {str(e)}",
        )


@router.get("/recovery/scan-storage", response_model=List[RecoverableManga])
async def scan_storage_for_recovery(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Scan storage for manga that exist in files but not in database.
    """
    try:
        recoverable_manga = await storage_recovery_service.scan_storage_for_manga(
            current_user.id, db
        )

        # Convert to response format
        result = []
        for manga in recoverable_manga:
            result.append(
                RecoverableManga(
                    storage_uuid=manga["storage_uuid"],
                    extracted_title=manga["extracted_title"],
                    chapter_count=manga["chapter_count"],
                    volume_count=manga["volume_count"],
                    storage_size=manga["storage_size"],
                    has_volume_structure=manga["has_volume_structure"],
                    organized_path=manga["organized_path"],
                    volumes=manga["volumes"],
                    metadata=manga.get("metadata"),
                )
            )

        return result

    except Exception as e:
        logger.error(f"Error scanning storage for recovery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan storage for recovery: {str(e)}",
        )


@router.post("/recovery/recover-manga", response_model=RecoverMangaResponse)
async def recover_manga_from_storage(
    request: RecoverMangaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Recover specific manga from storage into database.
    """
    try:
        manga = await storage_recovery_service.recover_manga_to_database(
            storage_uuid=request.storage_uuid,
            manga_title=request.manga_title,
            user_id=current_user.id,
            db=db,
            metadata=request.custom_metadata,
        )

        # Count recovered chapters
        result = await db.execute(select(Chapter).where(Chapter.manga_id == manga.id))
        chapters = result.scalars().all()

        return RecoverMangaResponse(
            success=True,
            manga_id=manga.id,
            message=f"Successfully recovered manga '{manga.title}' with {len(chapters)} chapters",
            chapters_recovered=len(chapters),
            errors=[],
        )

    except Exception as e:
        logger.error(f"Error recovering manga {request.storage_uuid}: {e}")
        return RecoverMangaResponse(
            success=False,
            manga_id=None,
            message=f"Failed to recover manga: {str(e)}",
            chapters_recovered=0,
            errors=[str(e)],
        )


@router.post("/recovery/batch-recover", response_model=BatchRecoveryResponse)
async def batch_recover_manga_from_storage(
    request: BatchRecoveryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Recover multiple manga from storage in batch.
    """
    total_requested = len(request.recovery_items)
    successful_recoveries = 0
    failed_recoveries = 0
    recovered_manga = []
    overall_errors = []

    for recovery_item in request.recovery_items:
        try:
            manga = await storage_recovery_service.recover_manga_to_database(
                storage_uuid=recovery_item.storage_uuid,
                manga_title=recovery_item.manga_title,
                user_id=current_user.id,
                db=db,
                metadata=recovery_item.custom_metadata,
            )

            # Count recovered chapters
            result = await db.execute(
                select(Chapter).where(Chapter.manga_id == manga.id)
            )
            chapters = result.scalars().all()

            recovered_manga.append(
                RecoverMangaResponse(
                    success=True,
                    manga_id=manga.id,
                    message=f"Successfully recovered '{manga.title}' with {len(chapters)} chapters",
                    chapters_recovered=len(chapters),
                    errors=[],
                )
            )

            successful_recoveries += 1

        except Exception as e:
            error_msg = f"Failed to recover {recovery_item.manga_title}: {str(e)}"
            logger.error(error_msg)

            recovered_manga.append(
                RecoverMangaResponse(
                    success=False,
                    manga_id=None,
                    message=error_msg,
                    chapters_recovered=0,
                    errors=[str(e)],
                )
            )

            failed_recoveries += 1
            overall_errors.append(error_msg)

            # If skip_errors is False, stop on first error
            if not request.skip_errors:
                break

    return BatchRecoveryResponse(
        total_requested=total_requested,
        successful_recoveries=successful_recoveries,
        failed_recoveries=failed_recoveries,
        recovered_manga=recovered_manga,
        errors=overall_errors,
    )


# New migration endpoints for folder structure changes

@router.post("/migration/analyze-volume-usage/{manga_id}", response_model=Dict[str, Any])
async def analyze_manga_volume_usage(
    manga_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Analyze a manga's volume usage patterns to recommend folder structure.
    """
    try:
        # Get manga
        manga = await db.get(Manga, manga_id)
        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Manga not found"
            )

        # Analyze volume usage
        analysis = await naming_engine.analyze_manga_volume_usage(manga, db)

        # Get template recommendations
        recommended_template = naming_engine.get_recommended_template(analysis)
        template_presets = naming_engine.get_template_presets()

        return {
            "manga_id": manga_id,
            "manga_title": getattr(manga, 'title', 'Unknown'),
            "analysis": {
                "has_volumes": analysis.has_volumes,
                "volume_count": analysis.volume_count,
                "chapter_count": analysis.chapter_count,
                "chapters_with_volumes": analysis.chapters_with_volumes,
                "chapters_without_volumes": analysis.chapters_without_volumes,
                "confidence_score": analysis.confidence_score,
                "recommended_pattern": analysis.recommended_pattern,
                "unique_volumes": list(analysis.unique_volumes)
            },
            "recommended_template": recommended_template,
            "current_template": current_user.naming_format_manga,
            "available_templates": template_presets,
            "template_descriptions": {
                name: naming_engine.get_preset_description(name)
                for name in template_presets.keys()
            }
        }

    except Exception as e:
        logger.error(f"Error analyzing volume usage for manga {manga_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze volume usage: {str(e)}",
        )


@router.post("/migration/create-plan/{manga_id}", response_model=Dict[str, Any])
async def create_structure_migration_plan(
    manga_id: UUID,
    new_template: str,
    preserve_original: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a migration plan for changing a manga's folder structure.
    """
    try:
        # Get manga
        manga = await db.get(Manga, manga_id)
        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Manga not found"
            )

        # Validate template
        is_valid, error_msg = naming_engine.validate_template(new_template)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid template: {error_msg}"
            )

        # Create migration plan
        plan = await migration_tool.create_structure_migration_plan(
            manga=manga,
            user=current_user,
            new_template=new_template,
            db=db,
            preserve_original=preserve_original
        )

        return {
            "plan_id": str(plan.manga_id),  # Use manga_id as plan identifier
            "summary": plan.get_summary(),
            "operations": plan.operations,
            "preview": {
                "sample_operations": plan.operations[:5],  # Show first 5 operations
                "total_operations": len(plan.operations),
                "estimated_duration": f"{plan.estimated_time // 60} minutes",
                "space_required": f"{plan.estimated_size / (1024*1024):.1f} MB"
            }
        }

    except Exception as e:
        logger.error(f"Error creating migration plan for manga {manga_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create migration plan: {str(e)}",
        )


@router.post("/migration/execute/{manga_id}", response_model=Dict[str, Any])
async def execute_structure_migration(
    manga_id: UUID,
    new_template: str,
    preserve_original: bool = True,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Execute a folder structure migration for a manga.
    """
    try:
        # Get manga
        manga = await db.get(Manga, manga_id)
        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Manga not found"
            )

        # Validate template
        is_valid, error_msg = naming_engine.validate_template(new_template)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid template: {error_msg}"
            )

        # Create migration plan
        plan = await migration_tool.create_structure_migration_plan(
            manga=manga,
            user=current_user,
            new_template=new_template,
            db=db,
            preserve_original=preserve_original
        )

        if not plan.operations:
            return {
                "success": True,
                "message": "No migration needed - manga already uses the target structure",
                "operations_completed": 0,
                "operations_failed": 0
            }

        # Execute migration in background
        background_tasks.add_task(
            execute_migration_background,
            plan=plan,
            manga_id=manga_id,
            new_template=new_template,
            user_id=current_user.id
        )

        return {
            "success": True,
            "message": "Migration started in background",
            "manga_id": manga_id,
            "total_operations": len(plan.operations),
            "estimated_duration": f"{plan.estimated_time // 60} minutes",
            "preserve_original": preserve_original
        }

    except Exception as e:
        logger.error(f"Error executing migration for manga {manga_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute migration: {str(e)}",
        )


async def execute_migration_background(
    plan: MigrationPlan,
    manga_id: UUID,
    new_template: str,
    user_id: UUID
) -> None:
    """
    Background task for executing migration plan.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Execute the migration
            result = await migration_tool.execute_migration_plan(plan, db)

            # Update user's default template if migration was successful
            if result["success"] and result["failed_operations"] == 0:
                user = await db.get(User, user_id)
                if user:
                    user.naming_format_manga = new_template
                    await db.commit()

            logger.info(
                f"Migration completed for manga {manga_id}: "
                f"{result['completed_operations']} completed, "
                f"{result['failed_operations']} failed"
            )

    except Exception as e:
        logger.error(f"Background migration for manga {manga_id} failed: {e}")


@router.get("/templates", response_model=Dict[str, Any])
async def get_naming_templates(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get available naming templates and current user settings.
    """
    try:
        presets = naming_engine.get_template_presets()
        descriptions = {
            name: naming_engine.get_preset_description(name)
            for name in presets.keys()
        }

        return {
            "current_manga_template": current_user.naming_format_manga,
            "current_chapter_template": current_user.naming_format_chapter,
            "available_presets": presets,
            "preset_descriptions": descriptions,
            "template_variables": [
                "Manga Title", "Volume", "Chapter Number",
                "Chapter Name", "Language", "Year", "Source"
            ],
            "examples": {
                name: naming_engine.apply_template(template, {
                    "Manga Title": "Example Manga",
                    "Volume": "1",
                    "Chapter Number": "5",
                    "Chapter Name": "The Adventure Begins",
                    "Language": "en",
                    "Year": "2023",
                    "Source": "mangadex"
                })
                for name, template in presets.items()
            }
        }

    except Exception as e:
        logger.error(f"Error getting naming templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get naming templates: {str(e)}",
        )
