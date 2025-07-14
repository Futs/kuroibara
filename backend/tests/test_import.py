import os
import tempfile
import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.import_file import (
    create_manga_from_import,
    import_archive,
    import_directory,
)
from app.models.manga import Manga, MangaStatus, MangaType


@pytest.mark.asyncio
@patch("app.core.services.import_file.get_image_dimensions")
@patch("app.core.services.import_file.is_image_file")
@patch("app.core.services.import_file.shutil")
@patch("app.core.services.import_file.os")
async def test_import_archive(
    mock_os,
    mock_shutil,
    mock_is_image_file,
    mock_get_image_dimensions,
    db: AsyncSession,
):
    """Test import_archive function."""
    # Mock os.path.splitext
    mock_os.path.splitext.return_value = ("test", ".cbz")

    # Mock os.path.join
    mock_os.path.join.side_effect = lambda *args: "/".join(args)

    # Mock os.makedirs
    mock_os.makedirs.return_value = None

    # Mock is_image_file
    mock_is_image_file.return_value = True

    # Mock get_image_dimensions
    mock_get_image_dimensions.return_value = (800, 1200)

    # Mock zipfile.ZipFile
    mock_zip = MagicMock()
    mock_zip.__enter__.return_value = mock_zip
    mock_zip.extractall.return_value = None

    # Mock os.walk
    mock_os.walk.return_value = [
        ("/tmp", [], ["page1.jpg", "page2.jpg"]),
    ]

    # Create test data
    user_id = uuid.uuid4()

    # Create a test manga first
    manga = Manga(
        title="Test Manga",
        description="Test description",
        type=MangaType.MANGA,
        status=MangaStatus.ONGOING,
    )
    db.add(manga)
    await db.flush()
    manga_id = manga.id

    # Create a temporary zip file
    with tempfile.NamedTemporaryFile(suffix=".cbz", delete=False) as temp_file:
        file_path = temp_file.name

    # Patch zipfile.ZipFile
    with patch("zipfile.ZipFile", return_value=mock_zip):
        # Call import_archive
        chapter = await import_archive(
            file_path=file_path,
            manga_id=manga_id,
            chapter_number="1",
            user_id=user_id,
            db=db,
            title="Test Chapter",
            volume="1",
            language="en",
        )

    # Check if chapter was created
    assert chapter is not None
    assert chapter.manga_id == manga_id
    assert chapter.title == "Test Chapter"
    assert chapter.number == "1"
    assert chapter.volume == "1"
    assert chapter.language == "en"
    assert chapter.pages_count == 2
    assert chapter.source == "import"

    # Clean up
    os.unlink(file_path)


@pytest.mark.asyncio
@patch("app.core.services.import_file.get_image_dimensions")
@patch("app.core.services.import_file.is_image_file")
@patch("app.core.services.import_file.shutil")
@patch("app.core.services.import_file.os")
async def test_import_directory(
    mock_os,
    mock_shutil,
    mock_is_image_file,
    mock_get_image_dimensions,
    db: AsyncSession,
):
    """Test import_directory function."""
    # Mock os.path.join
    mock_os.path.join.side_effect = lambda *args: "/".join(args)

    # Mock os.makedirs
    mock_os.makedirs.return_value = None

    # Mock is_image_file
    mock_is_image_file.return_value = True

    # Mock get_image_dimensions
    mock_get_image_dimensions.return_value = (800, 1200)

    # Mock os.walk
    mock_os.walk.return_value = [
        ("/tmp", [], ["page1.jpg", "page2.jpg"]),
    ]

    # Create test data
    user_id = uuid.uuid4()

    # Create a test manga first
    manga = Manga(
        title="Test Manga",
        description="Test description",
        type=MangaType.MANGA,
        status=MangaStatus.ONGOING,
    )
    db.add(manga)
    await db.flush()
    manga_id = manga.id

    # Call import_directory
    chapter = await import_directory(
        directory_path="/tmp",
        manga_id=manga_id,
        chapter_number="1",
        user_id=user_id,
        db=db,
        title="Test Chapter",
        volume="1",
        language="en",
    )

    # Check if chapter was created
    assert chapter is not None
    assert chapter.manga_id == manga_id
    assert chapter.title == "Test Chapter"
    assert chapter.number == "1"
    assert chapter.volume == "1"
    assert chapter.language == "en"
    assert chapter.pages_count == 2
    assert chapter.source == "import"


@pytest.mark.asyncio
@patch("app.core.services.import_file.shutil")
@patch("app.core.services.import_file.os")
async def test_create_manga_from_import(mock_os, mock_shutil, db: AsyncSession):
    """Test create_manga_from_import function."""
    # Mock os.path.join
    mock_os.path.join.side_effect = lambda *args: "/".join(args)

    # Mock os.makedirs
    mock_os.makedirs.return_value = None

    # Create test data - need to create a user first
    from app.models.user import User

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword",
        full_name="Test User",
    )
    db.add(user)
    await db.flush()
    user_id = user.id

    # Call create_manga_from_import
    manga, library_item = await create_manga_from_import(
        title="Test Manga",
        user_id=user_id,
        db=db,
        description="Test description",
        cover_path=None,
        manga_type=MangaType.MANGA,
        status=MangaStatus.ONGOING,
        year=2023,
        is_nsfw=False,
        genres=["Action", "Adventure"],
        authors=["Test Author"],
    )

    # Check if manga was created
    assert manga is not None
    assert manga.title == "Test Manga"
    assert manga.description == "Test description"
    assert manga.type == MangaType.MANGA
    assert manga.status == MangaStatus.ONGOING
    assert manga.year == 2023
    assert manga.is_nsfw is False

    # Check if library item was created
    assert library_item is not None
    assert library_item.user_id == user_id
    assert library_item.manga_id == manga.id
