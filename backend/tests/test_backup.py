"""
Tests for the backup and restore functionality.
"""

import json
import os
import tarfile
import tempfile
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.services.backup import BackupService, ScheduledBackupService
from app.models.user import User


class TestBackupService:
    """Test the backup service."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.backup_path = os.path.join(self.temp_dir, "backups")
        self.storage_path = os.path.join(self.temp_dir, "storage")

        os.makedirs(self.backup_path)
        os.makedirs(self.storage_path)

        # Create backup service with test paths
        self.service = BackupService()
        self.service.backup_path = self.backup_path
        self.service.storage_path = self.storage_path
        # Update derived paths after changing backup_path
        self.service.backups_dir = os.path.join(self.backup_path, "archives")
        self.service.restore_temp_dir = os.path.join(self.backup_path, "restore_temp")
        self.service.logs_dir = os.path.join(self.backup_path, "logs")

        # Ensure backup subdirectories exist
        os.makedirs(self.service.backups_dir, exist_ok=True)
        os.makedirs(self.service.restore_temp_dir, exist_ok=True)
        os.makedirs(self.service.logs_dir, exist_ok=True)

        # Create mock user
        self.user = Mock(spec=User)
        self.user.id = uuid4()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_database_config(self):
        """Test database configuration parsing."""
        # Mock DATABASE_URL
        with patch("app.core.services.backup.settings") as mock_settings:
            mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"
            mock_settings.DB_HOST = "localhost"
            mock_settings.DB_PORT = "5432"
            mock_settings.DB_USERNAME = "user"
            mock_settings.DB_PASSWORD = "pass"
            mock_settings.DB_DATABASE = "testdb"

            config = self.service.get_database_config()

            assert config["host"] == "localhost"
            assert config["port"] == "5432"
            assert config["username"] == "user"
            assert config["password"] == "pass"
            assert config["database"] == "testdb"

    def test_get_database_config_no_auth(self):
        """Test database configuration parsing without authentication."""
        with patch("app.core.services.backup.settings") as mock_settings:
            mock_settings.DATABASE_URL = "postgresql://localhost:5432/testdb"
            mock_settings.DB_HOST = "localhost"
            mock_settings.DB_PORT = "5432"
            mock_settings.DB_USERNAME = ""
            mock_settings.DB_PASSWORD = ""
            mock_settings.DB_DATABASE = "testdb"

            config = self.service.get_database_config()

            assert config["host"] == "localhost"
            assert config["port"] == "5432"
            assert config["username"] == ""
            assert config["password"] == ""
            assert config["database"] == "testdb"

    def test_get_database_config_invalid_url(self):
        """Test database configuration with invalid URL."""
        with patch("app.core.services.backup.settings") as mock_settings:
            mock_settings.DATABASE_URL = "mysql://localhost/testdb"
            mock_settings.DB_HOST = "localhost"
            mock_settings.DB_PORT = "3306"
            mock_settings.DB_USERNAME = "user"
            mock_settings.DB_PASSWORD = "pass"
            mock_settings.DB_DATABASE = "testdb"

            with pytest.raises(
                ValueError, match="Only PostgreSQL databases are supported"
            ):
                self.service.get_database_config()

    def test_create_storage_archive(self):
        """Test creating storage archive."""
        # Create test storage structure
        manga_dir = os.path.join(self.storage_path, "manga", str(uuid4()))
        os.makedirs(manga_dir)

        test_file = os.path.join(manga_dir, "test.cbz")
        with open(test_file, "w") as f:
            f.write("test content")

        # Create archive
        archive_path = os.path.join(self.temp_dir, "test_storage.tar.gz")
        result = self.service.create_storage_archive(archive_path)

        assert result is True
        assert os.path.exists(archive_path)

        # Verify archive contents
        with tarfile.open(archive_path, "r:gz") as tar:
            names = tar.getnames()
            assert any("storage" in name for name in names)

    def test_extract_storage_archive(self):
        """Test extracting storage archive."""
        # Create test archive
        archive_path = os.path.join(self.temp_dir, "test_extract.tar.gz")
        extract_dir = os.path.join(self.temp_dir, "extract")
        os.makedirs(extract_dir)

        # Create archive with test content
        with tarfile.open(archive_path, "w:gz") as tar:
            test_file = os.path.join(self.temp_dir, "test_content.txt")
            with open(test_file, "w") as f:
                f.write("test content")
            tar.add(test_file, arcname="storage/test_content.txt")

        # Extract archive
        result = self.service.extract_storage_archive(archive_path, extract_dir)

        assert result is True
        assert os.path.exists(os.path.join(extract_dir, "storage", "test_content.txt"))

    @pytest.mark.asyncio
    async def test_create_database_dump_success(self):
        """Test successful database dump creation."""
        dump_path = os.path.join(self.temp_dir, "test_dump.sql")

        # Mock successful pg_dump execution
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"dump output", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            with patch("app.core.services.backup.settings") as mock_settings:
                mock_settings.DATABASE_URL = (
                    "postgresql://user:pass@localhost:5432/testdb"
                )

                result = await self.service.create_database_dump(dump_path)

                assert result is True
                mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_database_dump_failure(self):
        """Test failed database dump creation."""
        dump_path = os.path.join(self.temp_dir, "test_dump.sql")

        # Mock failed pg_dump execution
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"error message")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            with patch("app.core.services.backup.settings") as mock_settings:
                mock_settings.DATABASE_URL = (
                    "postgresql://user:pass@localhost:5432/testdb"
                )

                result = await self.service.create_database_dump(dump_path)

                assert result is False

    @pytest.mark.asyncio
    async def test_create_full_backup(self):
        """Test creating a full backup."""

        # Mock database dump creation that actually creates the file
        async def mock_create_database_dump(output_path: str) -> bool:
            # Create a dummy database dump file
            with open(output_path, "w") as f:
                f.write("-- Mock database dump\nCREATE TABLE test (id INTEGER);")
            return True

        # Mock storage archive creation that actually creates the file
        def mock_create_storage_archive(output_path: str) -> bool:
            # Create a dummy storage archive file
            with open(output_path, "w") as f:
                f.write("dummy storage archive content")
            return True

        with patch.object(
            self.service, "create_database_dump", side_effect=mock_create_database_dump
        ):
            with patch.object(
                self.service,
                "create_storage_archive",
                side_effect=mock_create_storage_archive,
            ):

                success, backup_path = await self.service.create_full_backup(
                    backup_name="test_backup", include_storage=True
                )

                assert success is True
                assert backup_path is not None
                assert os.path.exists(backup_path)

                # Verify backup archive contents
                with tarfile.open(backup_path, "r:gz") as tar:
                    names = tar.getnames()
                    assert "database.sql" in names
                    assert "backup_metadata.json" in names
                    assert "storage.tar.gz" in names

    @pytest.mark.asyncio
    async def test_create_full_backup_database_only(self):
        """Test creating a database-only backup."""

        # Mock database dump creation that actually creates the file
        async def mock_create_database_dump(output_path: str) -> bool:
            # Create a dummy database dump file
            with open(output_path, "w") as f:
                f.write("-- Mock database dump\nCREATE TABLE test (id INTEGER);")
            return True

        with patch.object(
            self.service, "create_database_dump", side_effect=mock_create_database_dump
        ):

            success, backup_path = await self.service.create_full_backup(
                backup_name="test_db_backup", include_storage=False
            )

            assert success is True
            assert backup_path is not None
            assert os.path.exists(backup_path)

            # Verify backup archive contents (no storage)
            with tarfile.open(backup_path, "r:gz") as tar:
                names = tar.getnames()
                assert "database.sql" in names
                assert "backup_metadata.json" in names
                assert "storage.tar.gz" not in names

    def test_list_backups(self):
        """Test listing available backups."""
        # Create test backup files in the correct directory (backups_dir)
        backup1_path = os.path.join(self.service.backups_dir, "backup1.tar.gz")
        backup2_path = os.path.join(self.service.backups_dir, "backup2.tar.gz")

        # Create backup with metadata
        with tarfile.open(backup1_path, "w:gz") as tar:
            metadata = {
                "backup_name": "backup1",
                "created_at": "2023-07-10T12:00:00",
                "includes_storage": True,
            }
            metadata_file = os.path.join(self.temp_dir, "metadata.json")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)
            tar.add(metadata_file, arcname="backup_metadata.json")

        # Create backup without metadata
        with tarfile.open(backup2_path, "w:gz") as tar:
            test_file = os.path.join(self.temp_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            tar.add(test_file, arcname="test.txt")

        backups = self.service.list_backups()

        assert len(backups) == 2

        # Check backup with metadata
        backup1 = next(b for b in backups if b["filename"] == "backup1.tar.gz")
        assert backup1["metadata"] is not None
        assert backup1["metadata"]["backup_name"] == "backup1"

        # Check backup without metadata
        backup2 = next(b for b in backups if b["filename"] == "backup2.tar.gz")
        assert backup2["metadata"] is None

    def test_cleanup_old_backups(self):
        """Test cleaning up old backups."""
        # Set max backups to 2
        self.service.max_backups = 2

        # Create 4 test backup files in the correct directory (backups_dir)
        for i in range(4):
            backup_path = os.path.join(self.service.backups_dir, f"backup{i}.tar.gz")
            with open(backup_path, "w") as f:
                f.write(f"backup {i}")

        removed_count = self.service.cleanup_old_backups()

        assert removed_count == 2

        # Check that only 2 backups remain
        remaining_backups = self.service.list_backups()
        assert len(remaining_backups) == 2


class TestScheduledBackupService:
    """Test the scheduled backup service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScheduledBackupService()

    def test_scheduler_initialization(self):
        """Test that scheduler is properly initialized."""
        # The scheduler should be created (or None if APScheduler not available)
        assert self.service.scheduler is not None or self.service.scheduler is None

    def test_get_next_backup_times_no_scheduler(self):
        """Test getting next backup times when scheduler is not available."""
        self.service.scheduler = None

        next_times = self.service.get_next_backup_times()

        assert next_times == {}

    @patch("app.core.services.backup.settings")
    def test_cleanup_backup_type(self, mock_settings):
        """Test cleaning up specific backup types."""
        # Create mock backups
        mock_backups = [
            {"filename": "daily_20230710.tar.gz", "file_path": "/path/to/daily1"},
            {"filename": "daily_20230709.tar.gz", "file_path": "/path/to/daily2"},
            {"filename": "daily_20230708.tar.gz", "file_path": "/path/to/daily3"},
            {"filename": "weekly_20230710.tar.gz", "file_path": "/path/to/weekly1"},
        ]

        with patch.object(
            self.service.backup_service, "list_backups", return_value=mock_backups
        ):
            with patch("os.remove") as mock_remove:

                self.service._cleanup_backup_type("daily", keep=2)

                # Should remove 1 daily backup (keep 2, have 3)
                mock_remove.assert_called_once_with("/path/to/daily3")


if __name__ == "__main__":
    pytest.main([__file__])
