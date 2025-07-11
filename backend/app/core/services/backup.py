"""
Backup and restore service for Kuroibara.

This module provides comprehensive backup functionality including:
- Database dumps
- Storage file archiving
- Scheduled backups
- Restore operations
"""

import asyncio
import gzip
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class BackupService:
    """Service for creating and managing backups."""

    def __init__(self):
        """Initialize the backup service."""
        import tempfile

        # Use temp directory for testing environments where /app is not writable
        if getattr(settings, "APP_ENV", "") == "testing":
            self.backup_path = tempfile.mkdtemp(prefix="kuroibara_backup_test_")
            self.storage_path = tempfile.mkdtemp(prefix="kuroibara_storage_test_")
        else:
            self.backup_path = getattr(settings, "BACKUP_PATH", "/app/backups")
            self.storage_path = settings.STORAGE_PATH

        # Organized backup subdirectories
        self.backups_dir = os.path.join(self.backup_path, "archives")
        self.restore_temp_dir = os.path.join(self.backup_path, "restore_temp")
        self.logs_dir = os.path.join(self.backup_path, "logs")

        # Retention settings
        self.retention_enabled = getattr(settings, "BACKUP_RETENTION_ENABLED", True)
        self.retention_daily = getattr(settings, "BACKUP_RETENTION_DAILY", 7)
        self.retention_weekly = getattr(settings, "BACKUP_RETENTION_WEEKLY", 4)
        self.retention_monthly = getattr(settings, "BACKUP_RETENTION_MONTHLY", 12)
        self.retention_yearly = getattr(settings, "BACKUP_RETENTION_YEARLY", 5)
        self.retention_max_total = getattr(settings, "BACKUP_RETENTION_MAX_TOTAL", 50)
        self.max_backups = getattr(
            settings, "BACKUP_MAX_BACKUPS", 10
        )  # Default max backups

        # Ensure backup directories exist (with error handling for testing)
        try:
            os.makedirs(self.backups_dir, exist_ok=True)
            os.makedirs(self.restore_temp_dir, exist_ok=True)
            os.makedirs(self.logs_dir, exist_ok=True)
        except PermissionError as e:
            logger.warning(
                f"Could not create backup directories: {e}. Backup functionality may be limited."
            )
            # In testing environments, this is expected and not critical

    def get_database_config(self) -> Dict[str, str]:
        """Extract database configuration from settings."""
        # Validate that we're using PostgreSQL
        if hasattr(settings, "DATABASE_URL") and settings.DATABASE_URL:
            if not settings.DATABASE_URL.startswith("postgresql://"):
                raise ValueError(
                    "Only PostgreSQL databases are supported for backup operations"
                )

        # Use individual database settings instead of DATABASE_URL
        return {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "username": settings.DB_USERNAME,
            "password": settings.DB_PASSWORD,
            "database": settings.DB_DATABASE,
        }

    async def create_database_dump(self, output_path: str) -> bool:
        """
        Create a PostgreSQL database dump.

        Args:
            output_path: Path where the dump file should be saved

        Returns:
            True if dump was successful
        """
        try:
            db_config = self.get_database_config()

            # Use pg_dump with --no-sync to allow version mismatches
            cmd = [
                "pg_dump",
                "-h",
                db_config["host"],
                "-p",
                db_config["port"],
                "-U",
                db_config["username"],
                "-d",
                db_config["database"],
                "--no-password",
                "--no-sync",  # Allow version mismatches
                "--clean",
                "--if-exists",
                "--create",
                "-f",
                output_path,
            ]

            # Set environment variables
            env = os.environ.copy()
            if db_config["password"]:
                env["PGPASSWORD"] = db_config["password"]

            # Execute pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Database dump created successfully: {output_path}")
                return True
            else:
                logger.error(f"Database dump failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error creating database dump: {e}")
            return False

    async def restore_database_dump(self, dump_path: str) -> bool:
        """
        Restore a PostgreSQL database from dump.

        Args:
            dump_path: Path to the dump file

        Returns:
            True if restore was successful
        """
        try:
            db_config = self.get_database_config()

            # Prepare psql command
            cmd = [
                "psql",
                "-h",
                db_config["host"],
                "-p",
                db_config["port"],
                "-U",
                db_config["username"],
                "-d",
                "postgres",  # Connect to postgres db first
                "--no-password",
                "-f",
                dump_path,
            ]

            # Set environment variables
            env = os.environ.copy()
            if db_config["password"]:
                env["PGPASSWORD"] = db_config["password"]

            # Execute psql
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Database restored successfully from: {dump_path}")
                return True
            else:
                logger.error(f"Database restore failed: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False

    def create_storage_archive(
        self, output_path: str, exclude_temp: bool = True
    ) -> bool:
        """
        Create a compressed archive of the storage directory.

        Args:
            output_path: Path where the archive should be saved
            exclude_temp: Whether to exclude temporary files

        Returns:
            True if archive was successful
        """
        try:

            def filter_func(tarinfo):
                # Exclude temporary files and directories
                if exclude_temp:
                    if "/temp/" in tarinfo.name or tarinfo.name.endswith(".tmp"):
                        return None
                    if "/.git/" in tarinfo.name or tarinfo.name.endswith(".log"):
                        return None
                return tarinfo

            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(self.storage_path, arcname="storage", filter=filter_func)

            logger.info(f"Storage archive created successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating storage archive: {e}")
            return False

    def extract_storage_archive(self, archive_path: str, extract_to: str) -> bool:
        """
        Extract a storage archive.

        Args:
            archive_path: Path to the archive file
            extract_to: Directory to extract to

        Returns:
            True if extraction was successful
        """
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=extract_to)

            logger.info(f"Storage archive extracted successfully to: {extract_to}")
            return True

        except Exception as e:
            logger.error(f"Error extracting storage archive: {e}")
            return False

    async def create_full_backup(
        self, backup_name: Optional[str] = None, include_storage: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Create a full backup including database and storage.

        Args:
            backup_name: Custom name for the backup
            include_storage: Whether to include storage files

        Returns:
            Tuple of (success, backup_file_path)
        """
        try:
            # Generate backup name
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"kuroibara_backup_{timestamp}"

            # Create temporary directory for backup components
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create database dump
                db_dump_path = os.path.join(temp_dir, "database.sql")
                db_success = await self.create_database_dump(db_dump_path)

                if not db_success:
                    return False, None

                # Create storage archive if requested
                storage_success = True
                if include_storage:
                    storage_archive_path = os.path.join(temp_dir, "storage.tar.gz")
                    storage_success = self.create_storage_archive(storage_archive_path)

                if not storage_success:
                    return False, None

                # Create metadata file
                metadata = {
                    "backup_name": backup_name,
                    "created_at": datetime.now().isoformat(),
                    "kuroibara_version": getattr(settings, "VERSION", "unknown"),
                    "includes_storage": include_storage,
                    "database_size": os.path.getsize(db_dump_path),
                    "storage_size": (
                        os.path.getsize(storage_archive_path) if include_storage else 0
                    ),
                }

                metadata_path = os.path.join(temp_dir, "backup_metadata.json")
                import json

                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)

                # Create final backup archive in organized structure
                backup_file_path = os.path.join(
                    self.backups_dir, f"{backup_name}.tar.gz"
                )

                with tarfile.open(backup_file_path, "w:gz") as tar:
                    tar.add(db_dump_path, arcname="database.sql")
                    tar.add(metadata_path, arcname="backup_metadata.json")

                    if include_storage:
                        tar.add(storage_archive_path, arcname="storage.tar.gz")

                logger.info(f"Full backup created successfully: {backup_file_path}")

                # Apply retention policy after successful backup creation
                if self.retention_enabled:
                    try:
                        retention_result = await self.apply_retention_policy()
                        if retention_result.get("deleted_count", 0) > 0:
                            logger.info(
                                f"Retention policy applied: deleted {retention_result['deleted_count']} old backups"
                            )
                    except Exception as e:
                        logger.error(f"Failed to apply retention policy: {e}")

                return True, backup_file_path

        except Exception as e:
            logger.error(f"Error creating full backup: {e}")
            return False, None

    async def restore_full_backup(self, backup_path: str) -> Tuple[bool, List[str]]:
        """
        Restore from a full backup file.

        Args:
            backup_path: Path to the backup file

        Returns:
            Tuple of (success, list_of_errors)
        """
        errors = []

        try:
            # Extract backup to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup archive
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(path=temp_dir)

                # Read metadata
                metadata_path = os.path.join(temp_dir, "backup_metadata.json")
                if os.path.exists(metadata_path):
                    import json

                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    logger.info(
                        f"Restoring backup: {metadata.get('backup_name', 'unknown')}"
                    )

                # Restore database
                db_dump_path = os.path.join(temp_dir, "database.sql")
                if os.path.exists(db_dump_path):
                    db_success = await self.restore_database_dump(db_dump_path)
                    if not db_success:
                        errors.append("Failed to restore database")
                else:
                    errors.append("Database dump not found in backup")

                # Restore storage if present
                storage_archive_path = os.path.join(temp_dir, "storage.tar.gz")
                if os.path.exists(storage_archive_path):
                    # Backup current storage to organized location
                    if os.path.exists(self.storage_path):
                        backup_storage_name = (
                            f"storage_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        )
                        backup_storage_path = os.path.join(
                            self.restore_temp_dir, backup_storage_name
                        )
                        shutil.move(self.storage_path, backup_storage_path)
                        logger.info(
                            f"Current storage backed up to: {backup_storage_path}"
                        )

                    # Extract new storage
                    extract_dir = os.path.dirname(self.storage_path)
                    storage_success = self.extract_storage_archive(
                        storage_archive_path, extract_dir
                    )

                    if not storage_success:
                        errors.append("Failed to restore storage")

                if not errors:
                    logger.info("Full backup restored successfully")
                    return True, []
                else:
                    logger.error(f"Backup restore completed with errors: {errors}")
                    return False, errors

        except Exception as e:
            error_msg = f"Error restoring backup: {e}"
            logger.error(error_msg)
            return False, [error_msg]

    def list_backups(self) -> List[Dict]:
        """
        List all available backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []

        try:
            if not os.path.exists(self.backups_dir):
                return backups

            for filename in os.listdir(self.backups_dir):
                if filename.endswith(".tar.gz"):
                    file_path = os.path.join(self.backups_dir, filename)
                    stat = os.stat(file_path)

                    # Try to extract metadata
                    metadata = None
                    try:
                        with tarfile.open(file_path, "r:gz") as tar:
                            if "backup_metadata.json" in tar.getnames():
                                metadata_file = tar.extractfile("backup_metadata.json")
                                if metadata_file:
                                    import json

                                    metadata = json.load(metadata_file)
                    except Exception:
                        pass  # Ignore metadata extraction errors

                    backup_info = {
                        "filename": filename,
                        "file_path": file_path,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "metadata": metadata,
                    }

                    backups.append(backup_info)

            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            logger.error(f"Error listing backups: {e}")

        return backups

    def cleanup_old_backups(self) -> int:
        """
        Remove old backups beyond the retention limit.

        Returns:
            Number of backups removed
        """
        try:
            backups = self.list_backups()

            if len(backups) <= self.max_backups:
                return 0

            # Sort backups by creation time (oldest first)
            backups.sort(key=lambda x: x["created_at"])

            # Remove oldest backups
            backups_to_remove = backups[: -self.max_backups]
            removed_count = 0

            for backup in backups_to_remove:
                try:
                    os.remove(backup["file_path"])
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup['filename']}")
                except Exception as e:
                    logger.error(f"Error removing backup {backup['filename']}: {e}")

            return removed_count

        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0


class ScheduledBackupService:
    """Service for managing scheduled backups."""

    def __init__(self):
        """Initialize the scheduled backup service."""
        self.backup_service = BackupService()
        self.scheduler = None
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Set up the APScheduler for backup jobs."""
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger

            self.scheduler = AsyncIOScheduler()

            # Add default backup schedules based on settings
            daily_enabled = getattr(settings, "BACKUP_DAILY_ENABLED", True)
            weekly_enabled = getattr(settings, "BACKUP_WEEKLY_ENABLED", True)
            monthly_enabled = getattr(settings, "BACKUP_MONTHLY_ENABLED", True)

            if daily_enabled:
                # Daily backup at 2 AM
                self.scheduler.add_job(
                    self._daily_backup,
                    CronTrigger(hour=2, minute=0),
                    id="daily_backup",
                    replace_existing=True,
                )

            if weekly_enabled:
                # Weekly backup on Sunday at 3 AM
                self.scheduler.add_job(
                    self._weekly_backup,
                    CronTrigger(day_of_week=6, hour=3, minute=0),
                    id="weekly_backup",
                    replace_existing=True,
                )

            if monthly_enabled:
                # Monthly backup on 1st day at 4 AM
                self.scheduler.add_job(
                    self._monthly_backup,
                    CronTrigger(day=1, hour=4, minute=0),
                    id="monthly_backup",
                    replace_existing=True,
                )

            # Add daily provider health check at 1 AM (before daily backup)
            provider_health_enabled = getattr(
                settings, "PROVIDER_HEALTH_CHECK_ENABLED", True
            )
            if provider_health_enabled:
                self.scheduler.add_job(
                    self._daily_provider_health_check,
                    CronTrigger(hour=1, minute=0),
                    id="daily_provider_health_check",
                    replace_existing=True,
                )

            logger.info("Backup scheduler initialized")

        except ImportError:
            logger.warning("APScheduler not available, scheduled backups disabled")
            self.scheduler = None

    async def _daily_backup(self):
        """Perform daily backup."""
        try:
            logger.info("Starting daily backup")
            success, backup_path = await self.backup_service.create_full_backup(
                backup_name=f"daily_{datetime.now().strftime('%Y%m%d')}",
                include_storage=False,  # Daily backups exclude storage for speed
            )

            if success:
                logger.info(f"Daily backup completed: {backup_path}")
                # Apply retention policy after backup
                try:
                    retention_result = (
                        await self.backup_service.apply_retention_policy()
                    )
                    if retention_result.get("deleted_count", 0) > 0:
                        logger.info(
                            f"Retention policy applied: deleted {retention_result['deleted_count']} old backups"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to apply retention policy after daily backup: {e}"
                    )
            else:
                logger.error("Daily backup failed")

        except Exception as e:
            logger.error(f"Error in daily backup: {e}")

    async def _weekly_backup(self):
        """Perform weekly backup."""
        try:
            logger.info("Starting weekly backup")
            success, backup_path = await self.backup_service.create_full_backup(
                backup_name=f"weekly_{datetime.now().strftime('%Y%m%d')}",
                include_storage=True,  # Weekly backups include storage
            )

            if success:
                logger.info(f"Weekly backup completed: {backup_path}")
                # Apply retention policy after backup
                try:
                    retention_result = (
                        await self.backup_service.apply_retention_policy()
                    )
                    if retention_result.get("deleted_count", 0) > 0:
                        logger.info(
                            f"Retention policy applied: deleted {retention_result['deleted_count']} old backups"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to apply retention policy after weekly backup: {e}"
                    )
            else:
                logger.error("Weekly backup failed")

        except Exception as e:
            logger.error(f"Error in weekly backup: {e}")

    async def _monthly_backup(self):
        """Perform monthly backup."""
        try:
            logger.info("Starting monthly backup")
            success, backup_path = await self.backup_service.create_full_backup(
                backup_name=f"monthly_{datetime.now().strftime('%Y%m')}",
                include_storage=True,  # Monthly backups include storage
            )

            if success:
                logger.info(f"Monthly backup completed: {backup_path}")
                # Apply retention policy after backup
                try:
                    retention_result = (
                        await self.backup_service.apply_retention_policy()
                    )
                    if retention_result.get("deleted_count", 0) > 0:
                        logger.info(
                            f"Retention policy applied: deleted {retention_result['deleted_count']} old backups"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to apply retention policy after monthly backup: {e}"
                    )
            else:
                logger.error("Monthly backup failed")

        except Exception as e:
            logger.error(f"Error in monthly backup: {e}")

    async def _daily_provider_health_check(self):
        """Perform daily provider health check."""
        try:
            logger.info("Starting daily provider health check")

            # Import here to avoid circular imports
            from app.core.services.provider_monitor import provider_monitor

            # Perform the health check
            results = await provider_monitor.daily_health_check()

            # Log summary
            logger.info(
                f"Provider health check completed: "
                f"{results.get('healthy_providers', 0)}/{results.get('total_providers', 0)} healthy, "
                f"{results.get('enabled_providers', 0)} enabled, "
                f"{len(results.get('actions_taken', []))} actions taken"
            )

            # Log any actions taken
            for action in results.get("actions_taken", []):
                logger.info(
                    f"Provider {action['provider']} {action['action']}: {action['reason']}"
                )

        except Exception as e:
            logger.error(f"Error in daily provider health check: {e}")

    def _cleanup_backup_type(self, backup_type: str, keep: int):
        """Clean up old backups of a specific type."""
        try:
            backups = self.backup_service.list_backups()
            type_backups = [b for b in backups if backup_type in b["filename"]]

            if len(type_backups) > keep:
                to_remove = type_backups[keep:]
                for backup in to_remove:
                    try:
                        os.remove(backup["file_path"])
                        logger.info(
                            f"Removed old {backup_type} backup: {backup['filename']}"
                        )
                    except Exception as e:
                        logger.error(f"Error removing {backup_type} backup: {e}")

        except Exception as e:
            logger.error(f"Error cleaning up {backup_type} backups: {e}")

    def start(self):
        """Start the backup scheduler."""
        if self.scheduler:
            self.scheduler.start()
            logger.info("Backup scheduler started")

    def stop(self):
        """Stop the backup scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Backup scheduler stopped")

    def get_next_backup_times(self) -> Dict[str, Optional[str]]:
        """Get the next scheduled backup times."""
        if not self.scheduler:
            return {}

        next_times = {}

        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            next_times[job.id] = next_run.isoformat() if next_run else None

        return next_times

    async def apply_retention_policy(self) -> Dict[str, Any]:
        """Apply backup retention policy to clean up old backups."""
        if not self.retention_enabled:
            return {
                "retention_enabled": False,
                "message": "Retention policy is disabled",
            }

        try:
            backups = await self.list_backups()
            if not backups:
                return {"deleted_count": 0, "message": "No backups to clean up"}

            # Sort backups by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

            # Apply retention rules
            to_delete = self._determine_backups_to_delete(backups)

            deleted_count = 0
            deleted_files = []

            for backup in to_delete:
                try:
                    backup_path = os.path.join(self.backups_dir, backup["filename"])
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        deleted_count += 1
                        deleted_files.append(backup["filename"])
                        logger.info(f"Deleted old backup: {backup['filename']}")
                except Exception as e:
                    logger.error(f"Failed to delete backup {backup['filename']}: {e}")

            return {
                "deleted_count": deleted_count,
                "deleted_files": deleted_files,
                "total_backups_before": len(backups),
                "total_backups_after": len(backups) - deleted_count,
                "retention_policy": {
                    "daily": self.retention_daily,
                    "weekly": self.retention_weekly,
                    "monthly": self.retention_monthly,
                    "yearly": self.retention_yearly,
                    "max_total": self.retention_max_total,
                },
            }

        except Exception as e:
            logger.error(f"Error applying retention policy: {e}")
            return {"error": str(e)}

    def _determine_backups_to_delete(self, backups: List[Dict]) -> List[Dict]:
        """Determine which backups should be deleted based on retention policy."""
        if not backups:
            return []

        # Convert creation times to datetime objects
        for backup in backups:
            backup["created_datetime"] = datetime.fromisoformat(
                backup["created_at"].replace("Z", "+00:00")
            )

        now = datetime.now(timezone.utc)
        to_keep = set()

        # Group backups by time periods
        daily_backups = []
        weekly_backups = []
        monthly_backups = []
        yearly_backups = []

        for backup in backups:
            age_days = (now - backup["created_datetime"]).days

            if age_days <= 1:  # Last 24 hours - keep all
                to_keep.add(backup["filename"])
            elif age_days <= 7:  # Last week - daily retention
                daily_backups.append(backup)
            elif age_days <= 30:  # Last month - weekly retention
                weekly_backups.append(backup)
            elif age_days <= 365:  # Last year - monthly retention
                monthly_backups.append(backup)
            else:  # Older than a year - yearly retention
                yearly_backups.append(backup)

        # Apply retention policies for each period
        to_keep.update(
            self._select_backups_for_period(
                daily_backups, self.retention_daily, "daily"
            )
        )
        to_keep.update(
            self._select_backups_for_period(
                weekly_backups, self.retention_weekly, "weekly"
            )
        )
        to_keep.update(
            self._select_backups_for_period(
                monthly_backups, self.retention_monthly, "monthly"
            )
        )
        to_keep.update(
            self._select_backups_for_period(
                yearly_backups, self.retention_yearly, "yearly"
            )
        )

        # If we still have too many backups, remove the oldest ones
        if len(to_keep) > self.retention_max_total:
            backups_to_keep = [b for b in backups if b["filename"] in to_keep]
            backups_to_keep.sort(key=lambda x: x["created_datetime"], reverse=True)
            to_keep = {
                b["filename"] for b in backups_to_keep[: self.retention_max_total]
            }

        # Return backups that should be deleted
        return [backup for backup in backups if backup["filename"] not in to_keep]

    def _select_backups_for_period(
        self, backups: List[Dict], retention_count: int, period: str
    ) -> Set[str]:
        """Select backups to keep for a specific time period."""
        if not backups or retention_count <= 0:
            return set()

        # Group backups by the appropriate time unit
        if period == "daily":
            # Keep one backup per day
            grouped = {}
            for backup in backups:
                day_key = backup["created_datetime"].date()
                if (
                    day_key not in grouped
                    or backup["created_datetime"] > grouped[day_key]["created_datetime"]
                ):
                    grouped[day_key] = backup
            candidates = list(grouped.values())
        elif period == "weekly":
            # Keep one backup per week (Monday as start of week)
            grouped = {}
            for backup in backups:
                week_key = backup["created_datetime"].isocalendar()[:2]  # (year, week)
                if (
                    week_key not in grouped
                    or backup["created_datetime"]
                    > grouped[week_key]["created_datetime"]
                ):
                    grouped[week_key] = backup
            candidates = list(grouped.values())
        elif period == "monthly":
            # Keep one backup per month
            grouped = {}
            for backup in backups:
                month_key = (
                    backup["created_datetime"].year,
                    backup["created_datetime"].month,
                )
                if (
                    month_key not in grouped
                    or backup["created_datetime"]
                    > grouped[month_key]["created_datetime"]
                ):
                    grouped[month_key] = backup
            candidates = list(grouped.values())
        elif period == "yearly":
            # Keep one backup per year
            grouped = {}
            for backup in backups:
                year_key = backup["created_datetime"].year
                if (
                    year_key not in grouped
                    or backup["created_datetime"]
                    > grouped[year_key]["created_datetime"]
                ):
                    grouped[year_key] = backup
            candidates = list(grouped.values())
        else:
            candidates = backups

        # Sort by creation time (newest first) and take the specified number
        candidates.sort(key=lambda x: x["created_datetime"], reverse=True)
        return {backup["filename"] for backup in candidates[:retention_count]}


# Global instances
backup_service = BackupService()
scheduled_backup_service = ScheduledBackupService()
