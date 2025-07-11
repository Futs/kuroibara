"""
Tests for the storage recovery functionality.
"""

import json
import os
import tempfile
import zipfile
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.services.storage_recovery import StorageRecoveryService
from app.models.manga import Manga, MangaStatus, MangaType
from app.models.user import User


class TestStorageRecoveryService:
    """Test the storage recovery service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = StorageRecoveryService()

        # Create mock user
        self.user = Mock(spec=User)
        self.user.id = uuid4()

        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Mock the storage path
        self.service.storage_path = self.temp_dir
        self.service.manga_storage_path = os.path.join(self.temp_dir, "manga")
        os.makedirs(self.service.manga_storage_path)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_valid_uuid_format(self):
        """Test UUID format validation."""
        valid_uuid = str(uuid4())
        invalid_uuid = "not-a-uuid"

        assert self.service._is_valid_uuid_format(valid_uuid) is True
        assert self.service._is_valid_uuid_format(invalid_uuid) is False

    def test_calculate_directory_size(self):
        """Test directory size calculation."""
        test_dir = os.path.join(self.temp_dir, "test_size")
        os.makedirs(test_dir)

        # Create test files
        file1 = os.path.join(test_dir, "file1.txt")
        file2 = os.path.join(test_dir, "file2.txt")

        with open(file1, "w") as f:
            f.write("hello")  # 5 bytes

        with open(file2, "w") as f:
            f.write("world!")  # 6 bytes

        size = self.service._calculate_directory_size(test_dir)
        assert size == 11  # 5 + 6 bytes

    def test_extract_chapter_info_from_filename(self):
        """Test chapter info extraction from filename."""
        # Test standard format
        result = self.service._extract_chapter_info_from_filename(
            "1 - Enter Sasuke!.cbz"
        )
        assert result["number"] == "1"
        assert result["title"] == "Enter Sasuke!"
        assert result["filename"] == "1 - Enter Sasuke!.cbz"

        # Test decimal chapter number
        result = self.service._extract_chapter_info_from_filename(
            "12.5 - Special Chapter.cbz"
        )
        assert result["number"] == "12.5"
        assert result["title"] == "Special Chapter"

        # Test fallback for non-standard format
        result = self.service._extract_chapter_info_from_filename("Chapter001.cbz")
        assert result["number"] == "001"
        assert result["title"] == "Chapter001"

    def test_natural_sort_key(self):
        """Test natural sorting of chapter numbers."""
        assert self.service._natural_sort_key("1") < self.service._natural_sort_key("2")
        assert self.service._natural_sort_key("1") < self.service._natural_sort_key(
            "10"
        )
        assert self.service._natural_sort_key("1.5") < self.service._natural_sort_key(
            "2"
        )
        assert self.service._natural_sort_key("invalid") == float("inf")

    def test_read_cbz_metadata(self):
        """Test reading metadata from CBZ files."""
        # Create a test CBZ file with metadata
        cbz_path = os.path.join(self.temp_dir, "test.cbz")

        metadata = {
            "manga": {
                "title": "Test Manga",
                "description": "Test description",
                "year": 2023,
            },
            "chapter": {"title": "Test Chapter", "number": "1"},
        }

        with zipfile.ZipFile(cbz_path, "w") as cbz:
            # Add a dummy image
            cbz.writestr("001.jpg", b"fake image data")
            # Add metadata
            cbz.writestr("metadata.json", json.dumps(metadata))

        result = self.service._read_cbz_metadata(cbz_path)
        assert result is not None
        assert result["manga"]["title"] == "Test Manga"
        assert result["chapter"]["number"] == "1"

    def test_count_pages_in_cbz(self):
        """Test counting pages in CBZ files."""
        cbz_path = os.path.join(self.temp_dir, "test.cbz")

        with zipfile.ZipFile(cbz_path, "w") as cbz:
            # Add image files
            cbz.writestr("001.jpg", b"fake image data")
            cbz.writestr("002.png", b"fake image data")
            cbz.writestr("003.gif", b"fake image data")
            # Add non-image file (should be ignored)
            cbz.writestr("metadata.json", b"metadata")

        count = self.service._count_pages_in_cbz(cbz_path)
        assert count == 3

    def create_test_organized_structure(self, manga_uuid: str, manga_title: str):
        """Helper to create test organized manga structure."""
        manga_dir = os.path.join(self.service.manga_storage_path, manga_uuid)
        organized_dir = os.path.join(manga_dir, "organized", manga_title)
        volume_dir = os.path.join(organized_dir, "Volume 1")

        os.makedirs(volume_dir)

        # Create test CBZ files
        chapters = [
            ("1 - Enter Sasuke!.cbz", "Enter Sasuke!"),
            ("2 - The Worst Client.cbz", "The Worst Client"),
        ]

        for filename, title in chapters:
            cbz_path = os.path.join(volume_dir, filename)

            metadata = {
                "manga": {
                    "title": manga_title,
                    "description": "Test manga description",
                    "year": 2023,
                    "status": "ongoing",
                    "type": "manga",
                },
                "chapter": {"title": title, "number": filename.split(" - ")[0]},
            }

            with zipfile.ZipFile(cbz_path, "w") as cbz:
                # Add dummy images
                for i in range(20):
                    cbz.writestr(f"{i+1:03d}.jpg", b"fake image data")
                # Add metadata
                cbz.writestr("metadata.json", json.dumps(metadata))

        return manga_dir

    @pytest.mark.asyncio
    async def test_scan_storage_for_manga(self):
        """Test scanning storage for recoverable manga."""
        # Create test organized structure
        manga_uuid = str(uuid4())
        manga_title = "Test Manga"
        self.create_test_organized_structure(manga_uuid, manga_title)

        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []  # No existing manga
        mock_db.execute.return_value = mock_result

        # Scan storage
        result = await self.service.scan_storage_for_manga(self.user.id, mock_db)

        assert len(result) == 1
        manga_info = result[0]
        assert manga_info["storage_uuid"] == manga_uuid
        assert manga_info["extracted_title"] == manga_title
        assert manga_info["chapter_count"] == 2
        assert manga_info["volume_count"] == 1
        assert manga_info["has_volume_structure"] is True

    @pytest.mark.asyncio
    async def test_recover_manga_to_database(self):
        """Test recovering manga to database."""
        # Create test organized structure
        manga_uuid = str(uuid4())
        manga_title = "Test Manga"
        self.create_test_organized_structure(manga_uuid, manga_title)

        # Mock database session
        mock_db = AsyncMock()
        mock_db.add = Mock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.rollback = AsyncMock()

        # Mock get_manga_storage_path
        new_uuid = uuid4()
        new_storage_path = os.path.join(self.temp_dir, "new_manga", str(new_uuid))

        with patch(
            "app.core.services.storage_recovery.get_manga_storage_path"
        ) as mock_get_path:
            mock_get_path.return_value = new_storage_path

            # Mock the manga creation
            mock_manga = Mock(spec=Manga)
            mock_manga.id = new_uuid
            mock_manga.title = manga_title

            with patch("app.core.services.storage_recovery.Manga") as mock_manga_class:
                mock_manga_class.return_value = mock_manga

                # Test recovery
                result = await self.service.recover_manga_to_database(
                    storage_uuid=manga_uuid,
                    manga_title=manga_title,
                    user_id=self.user.id,
                    db=mock_db,
                    metadata={"description": "Test description"},
                )

                # Verify manga was created
                assert mock_manga_class.called
                assert mock_db.add.called
                mock_db.commit.assert_awaited_once()

                # Verify file was moved (would need to check if new path exists)
                # This is mocked in the test, but in real usage the directory would be moved

    def test_scan_volume_for_chapters(self):
        """Test scanning a volume directory for chapters."""
        volume_dir = os.path.join(self.temp_dir, "Volume 1")
        os.makedirs(volume_dir)

        # Create test CBZ files
        chapters = [
            "1 - Chapter One.cbz",
            "2 - Chapter Two.cbz",
            "10 - Chapter Ten.cbz",
        ]
        for chapter in chapters:
            cbz_path = os.path.join(volume_dir, chapter)
            with zipfile.ZipFile(cbz_path, "w") as cbz:
                cbz.writestr("001.jpg", b"fake image data")

        result = self.service._scan_volume_for_chapters(volume_dir)

        assert len(result) == 3
        # Check natural sorting (1, 2, 10 not 1, 10, 2)
        assert result[0]["number"] == "1"
        assert result[1]["number"] == "2"
        assert result[2]["number"] == "10"

    @pytest.mark.asyncio
    async def test_extract_metadata_from_cbz_files(self):
        """Test extracting metadata from CBZ files."""
        # Create test CBZ with metadata
        cbz_path = os.path.join(self.temp_dir, "test.cbz")

        metadata = {
            "manga": {
                "description": "Test description",
                "year": 2023,
                "status": "ongoing",
                "type": "manga",
                "provider": "test_provider",
                "external_id": "test123",
            }
        }

        with zipfile.ZipFile(cbz_path, "w") as cbz:
            cbz.writestr("001.jpg", b"fake image data")
            cbz.writestr("metadata.json", json.dumps(metadata))

        volumes = {"Volume 1": [{"file_path": cbz_path}]}

        result = await self.service._extract_metadata_from_cbz_files(volumes)

        assert result["description"] == "Test description"
        assert result["year"] == 2023
        assert result["status"] == "ongoing"
        assert result["type"] == "manga"
        assert result["provider"] == "test_provider"
        assert result["external_id"] == "test123"


if __name__ == "__main__":
    pytest.main([__file__])
