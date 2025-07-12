"""
API endpoints for backup and restore operations.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.services.backup import backup_service, scheduled_backup_service
from app.core.services.storage_recovery import storage_recovery_service
from app.models.user import User
from app.schemas.backup import (
    BackupCreateRequest,
    BackupInfo,
    BackupListResponse,
    BackupRestoreResponse,
    BackupScheduleInfo,
    CreateBackupResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/list", response_model=BackupListResponse)
async def list_backups(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List all available backups.
    """
    try:
        backups = backup_service.list_backups()

        backup_infos = []
        for backup in backups:
            backup_info = BackupInfo(
                filename=backup["filename"],
                size=backup["size"],
                created_at=backup["created_at"],
                metadata=backup.get("metadata"),
                download_url=f"/api/v1/backup/download/{backup['filename']}",
            )
            backup_infos.append(backup_info)

        return BackupListResponse(
            backups=backup_infos,
            total_count=len(backup_infos),
            total_size=sum(b.size for b in backup_infos),
        )

    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}",
        )


@router.post("/create", response_model=CreateBackupResponse)
async def create_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new backup.
    """
    try:
        # Start backup in background
        background_tasks.add_task(
            create_backup_background,
            backup_name=request.backup_name,
            include_storage=request.include_storage,
            user_id=current_user.id,
        )

        return CreateBackupResponse(
            message="Backup creation started",
            backup_name=request.backup_name
            or f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            estimated_duration="5-30 minutes depending on storage size",
        )

    except Exception as e:
        logger.error(f"Error starting backup creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start backup creation: {str(e)}",
        )


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Download a backup file.
    """
    try:
        # Validate filename (security check)
        if not filename.endswith(".tar.gz") or "/" in filename or ".." in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
            )

        backup_path = os.path.join(backup_service.backups_dir, filename)

        if not os.path.exists(backup_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
            )

        return FileResponse(
            path=backup_path, filename=filename, media_type="application/gzip"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download backup: {str(e)}",
        )


@router.post("/upload-restore", response_model=BackupRestoreResponse)
async def upload_and_restore_backup(
    background_tasks: BackgroundTasks,
    backup_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Upload and restore from a backup file.
    """
    try:
        # Validate file
        if not backup_file.filename or not backup_file.filename.endswith(".tar.gz"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid backup file. Must be a .tar.gz file",
            )

        # Save uploaded file temporarily
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as temp_file:
            content = await backup_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Start restore in background
        background_tasks.add_task(
            restore_backup_background,
            backup_path=temp_file_path,
            user_id=current_user.id,
        )

        return BackupRestoreResponse(
            message="Backup restore started",
            filename=backup_file.filename,
            status="processing",
            warnings=[
                "This will overwrite the current database and storage",
                "All current data will be lost",
                "The application may be unavailable during restore",
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading backup for restore: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload backup: {str(e)}",
        )


@router.delete("/delete/{filename}")
async def delete_backup(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a backup file.
    """
    try:
        # Validate filename (security check)
        if not filename.endswith(".tar.gz") or "/" in filename or ".." in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
            )

        backup_path = os.path.join(backup_service.backups_dir, filename)

        if not os.path.exists(backup_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
            )

        os.remove(backup_path)
        logger.info(f"Backup deleted: {filename}")

        return {"message": f"Backup {filename} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}",
        )


@router.get("/schedule", response_model=BackupScheduleInfo)
async def get_backup_schedule(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get backup schedule information.
    """
    try:
        next_times = scheduled_backup_service.get_next_backup_times()

        return BackupScheduleInfo(
            daily_enabled=True,
            weekly_enabled=True,
            monthly_enabled=True,
            next_daily_backup=next_times.get("daily_backup"),
            next_weekly_backup=next_times.get("weekly_backup"),
            next_monthly_backup=next_times.get("monthly_backup"),
        )

    except Exception as e:
        logger.error(f"Error getting backup schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup schedule: {str(e)}",
        )


@router.post("/cleanup")
async def cleanup_old_backups(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Clean up old backups beyond retention limit.
    """
    try:
        removed_count = backup_service.cleanup_old_backups()

        return {"message": "Cleanup completed", "removed_backups": removed_count}

    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup backups: {str(e)}",
        )


@router.get("/check-orphaned")
async def check_for_orphaned_storage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Check if there are orphaned files in storage (useful after restore).
    """
    try:
        orphaned_manga = await storage_recovery_service.scan_storage_for_manga(
            current_user.id, db
        )

        return {
            "has_orphaned_files": len(orphaned_manga) > 0,
            "orphaned_count": len(orphaned_manga),
            "message": (
                f"Found {len(orphaned_manga)} manga in storage that are not in the database"
                if orphaned_manga
                else "No orphaned files found"
            ),
            "recovery_url": "/settings?tab=backup" if orphaned_manga else None,
        }

    except Exception as e:
        logger.error(f"Error checking for orphaned storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check for orphaned storage: {str(e)}",
        )


# Background task functions
async def create_backup_background(
    backup_name: str, include_storage: bool, user_id: str
):
    """Background task for creating backups."""
    try:
        logger.info(f"Starting background backup creation: {backup_name}")
        success, backup_path = await backup_service.create_full_backup(
            backup_name=backup_name, include_storage=include_storage
        )

        if success:
            logger.info(f"Background backup completed: {backup_path}")
        else:
            logger.error(f"Background backup failed: {backup_name}")

    except Exception as e:
        logger.error(f"Error in background backup creation: {e}")


async def restore_backup_background(backup_path: str, user_id: str):
    """Background task for restoring backups."""
    try:
        logger.info(f"Starting background backup restore: {backup_path}")
        success, errors = await backup_service.restore_full_backup(backup_path)

        if success:
            logger.info("Background backup restore completed successfully")
        else:
            logger.error(f"Background backup restore failed: {errors}")

        # Clean up temporary file
        if os.path.exists(backup_path):
            os.remove(backup_path)

    except Exception as e:
        logger.error(f"Error in background backup restore: {e}")
        # Clean up temporary file on error
        if os.path.exists(backup_path):
            os.remove(backup_path)


@router.post("/apply-retention")
async def apply_retention_policy(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Manually apply backup retention policy to clean up old backups.
    """
    try:
        result = await backup_service.apply_retention_policy()
        return result
    except Exception as e:
        logger.error(f"Error applying retention policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply retention policy: {str(e)}",
        )


@router.get("/retention-settings")
async def get_retention_settings(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current backup retention settings.
    """
    try:
        return {
            "retention_enabled": backup_service.retention_enabled,
            "retention_daily": backup_service.retention_daily,
            "retention_weekly": backup_service.retention_weekly,
            "retention_monthly": backup_service.retention_monthly,
            "retention_yearly": backup_service.retention_yearly,
            "retention_max_total": backup_service.retention_max_total,
            "description": {
                "daily": f"Keep {backup_service.retention_daily} daily backups (last 7 days)",
                "weekly": f"Keep {backup_service.retention_weekly} weekly backups (last month)",
                "monthly": f"Keep {backup_service.retention_monthly} monthly backups (last year)",
                "yearly": f"Keep {backup_service.retention_yearly} yearly backups (older than 1 year)",
                "max_total": f"Maximum {backup_service.retention_max_total} total backups regardless of age",
            },
        }
    except Exception as e:
        logger.error(f"Error getting retention settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retention settings: {str(e)}",
        )
