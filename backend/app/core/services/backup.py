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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
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
        self.backup_path = getattr(settings, 'BACKUP_PATH', '/app/backups')
        self.storage_path = settings.STORAGE_PATH
        self.max_backups = getattr(settings, 'MAX_BACKUPS', 30)  # Keep 30 backups by default
        
        # Ensure backup directory exists
        os.makedirs(self.backup_path, exist_ok=True)
    
    def get_database_config(self) -> Dict[str, str]:
        """Extract database configuration from DATABASE_URL."""
        db_url = settings.DATABASE_URL
        
        # Parse postgresql://user:password@host:port/database
        if not db_url.startswith('postgresql://'):
            raise ValueError("Only PostgreSQL databases are supported for backup")
        
        # Remove protocol
        db_url = db_url.replace('postgresql://', '')
        
        # Split user:password@host:port/database
        if '@' in db_url:
            auth_part, host_part = db_url.split('@', 1)
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
            else:
                username, password = auth_part, ''
        else:
            username, password = '', ''
            host_part = db_url
        
        if '/' in host_part:
            host_port, database = host_part.split('/', 1)
        else:
            host_port, database = host_part, ''
        
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host, port = host_port, '5432'
        
        return {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'database': database
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
            
            # Prepare pg_dump command
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['username'],
                '-d', db_config['database'],
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                '--create',
                '-f', output_path
            ]
            
            # Set environment variables
            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']
            
            # Execute pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
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
                'psql',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['username'],
                '-d', 'postgres',  # Connect to postgres db first
                '--no-password',
                '-f', dump_path
            ]
            
            # Set environment variables
            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']
            
            # Execute psql
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
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
    
    def create_storage_archive(self, output_path: str, exclude_temp: bool = True) -> bool:
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
                    if '/temp/' in tarinfo.name or tarinfo.name.endswith('.tmp'):
                        return None
                    if '/.git/' in tarinfo.name or tarinfo.name.endswith('.log'):
                        return None
                return tarinfo
            
            with tarfile.open(output_path, 'w:gz') as tar:
                tar.add(
                    self.storage_path,
                    arcname='storage',
                    filter=filter_func
                )
            
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
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=extract_to)
            
            logger.info(f"Storage archive extracted successfully to: {extract_to}")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting storage archive: {e}")
            return False
    
    async def create_full_backup(
        self,
        backup_name: Optional[str] = None,
        include_storage: bool = True
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
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"kuroibara_backup_{timestamp}"
            
            # Create temporary directory for backup components
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create database dump
                db_dump_path = os.path.join(temp_dir, 'database.sql')
                db_success = await self.create_database_dump(db_dump_path)
                
                if not db_success:
                    return False, None
                
                # Create storage archive if requested
                storage_success = True
                if include_storage:
                    storage_archive_path = os.path.join(temp_dir, 'storage.tar.gz')
                    storage_success = self.create_storage_archive(storage_archive_path)
                
                if not storage_success:
                    return False, None
                
                # Create metadata file
                metadata = {
                    'backup_name': backup_name,
                    'created_at': datetime.now().isoformat(),
                    'kuroibara_version': getattr(settings, 'VERSION', 'unknown'),
                    'includes_storage': include_storage,
                    'database_size': os.path.getsize(db_dump_path),
                    'storage_size': os.path.getsize(storage_archive_path) if include_storage else 0
                }
                
                metadata_path = os.path.join(temp_dir, 'backup_metadata.json')
                import json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Create final backup archive
                backup_file_path = os.path.join(self.backup_path, f"{backup_name}.tar.gz")
                
                with tarfile.open(backup_file_path, 'w:gz') as tar:
                    tar.add(db_dump_path, arcname='database.sql')
                    tar.add(metadata_path, arcname='backup_metadata.json')
                    
                    if include_storage:
                        tar.add(storage_archive_path, arcname='storage.tar.gz')
                
                logger.info(f"Full backup created successfully: {backup_file_path}")
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
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(path=temp_dir)
                
                # Read metadata
                metadata_path = os.path.join(temp_dir, 'backup_metadata.json')
                if os.path.exists(metadata_path):
                    import json
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    logger.info(f"Restoring backup: {metadata.get('backup_name', 'unknown')}")
                
                # Restore database
                db_dump_path = os.path.join(temp_dir, 'database.sql')
                if os.path.exists(db_dump_path):
                    db_success = await self.restore_database_dump(db_dump_path)
                    if not db_success:
                        errors.append("Failed to restore database")
                else:
                    errors.append("Database dump not found in backup")
                
                # Restore storage if present
                storage_archive_path = os.path.join(temp_dir, 'storage.tar.gz')
                if os.path.exists(storage_archive_path):
                    # Backup current storage
                    if os.path.exists(self.storage_path):
                        backup_storage_path = f"{self.storage_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.move(self.storage_path, backup_storage_path)
                        logger.info(f"Current storage backed up to: {backup_storage_path}")
                    
                    # Extract new storage
                    extract_dir = os.path.dirname(self.storage_path)
                    storage_success = self.extract_storage_archive(storage_archive_path, extract_dir)
                    
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
            if not os.path.exists(self.backup_path):
                return backups
            
            for filename in os.listdir(self.backup_path):
                if filename.endswith('.tar.gz'):
                    file_path = os.path.join(self.backup_path, filename)
                    stat = os.stat(file_path)
                    
                    # Try to extract metadata
                    metadata = None
                    try:
                        with tarfile.open(file_path, 'r:gz') as tar:
                            if 'backup_metadata.json' in tar.getnames():
                                metadata_file = tar.extractfile('backup_metadata.json')
                                if metadata_file:
                                    import json
                                    metadata = json.load(metadata_file)
                    except Exception:
                        pass  # Ignore metadata extraction errors
                    
                    backup_info = {
                        'filename': filename,
                        'file_path': file_path,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'metadata': metadata
                    }
                    
                    backups.append(backup_info)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
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
            
            # Remove oldest backups
            backups_to_remove = backups[self.max_backups:]
            removed_count = 0
            
            for backup in backups_to_remove:
                try:
                    os.remove(backup['file_path'])
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
            daily_enabled = getattr(settings, 'BACKUP_DAILY_ENABLED', True)
            weekly_enabled = getattr(settings, 'BACKUP_WEEKLY_ENABLED', True)
            monthly_enabled = getattr(settings, 'BACKUP_MONTHLY_ENABLED', True)

            if daily_enabled:
                # Daily backup at 2 AM
                self.scheduler.add_job(
                    self._daily_backup,
                    CronTrigger(hour=2, minute=0),
                    id='daily_backup',
                    replace_existing=True
                )

            if weekly_enabled:
                # Weekly backup on Sunday at 3 AM
                self.scheduler.add_job(
                    self._weekly_backup,
                    CronTrigger(day_of_week=6, hour=3, minute=0),
                    id='weekly_backup',
                    replace_existing=True
                )

            if monthly_enabled:
                # Monthly backup on 1st day at 4 AM
                self.scheduler.add_job(
                    self._monthly_backup,
                    CronTrigger(day=1, hour=4, minute=0),
                    id='monthly_backup',
                    replace_existing=True
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
                include_storage=False  # Daily backups exclude storage for speed
            )

            if success:
                logger.info(f"Daily backup completed: {backup_path}")
                # Cleanup old daily backups (keep last 7)
                self._cleanup_backup_type('daily', keep=7)
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
                include_storage=True  # Weekly backups include storage
            )

            if success:
                logger.info(f"Weekly backup completed: {backup_path}")
                # Cleanup old weekly backups (keep last 4)
                self._cleanup_backup_type('weekly', keep=4)
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
                include_storage=True  # Monthly backups include storage
            )

            if success:
                logger.info(f"Monthly backup completed: {backup_path}")
                # Cleanup old monthly backups (keep last 12)
                self._cleanup_backup_type('monthly', keep=12)
            else:
                logger.error("Monthly backup failed")

        except Exception as e:
            logger.error(f"Error in monthly backup: {e}")

    def _cleanup_backup_type(self, backup_type: str, keep: int):
        """Clean up old backups of a specific type."""
        try:
            backups = self.backup_service.list_backups()
            type_backups = [b for b in backups if backup_type in b['filename']]

            if len(type_backups) > keep:
                to_remove = type_backups[keep:]
                for backup in to_remove:
                    try:
                        os.remove(backup['file_path'])
                        logger.info(f"Removed old {backup_type} backup: {backup['filename']}")
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


# Global instances
backup_service = BackupService()
scheduled_backup_service = ScheduledBackupService()
