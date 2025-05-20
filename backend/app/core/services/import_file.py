import os
import shutil
import tempfile
import zipfile
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID
from pyunpack import Archive

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.utils import (
    get_manga_storage_path,
    get_chapter_storage_path,
    get_cover_storage_path,
    get_page_storage_path,
    is_image_file,
    get_image_dimensions,
)
from app.models.manga import Manga, Chapter, Page, MangaType, MangaStatus
from app.models.library import MangaUserLibrary

logger = logging.getLogger(__name__)


async def import_archive(
    file_path: str,
    manga_id: UUID,
    chapter_number: str,
    user_id: UUID,
    db: AsyncSession,
    title: Optional[str] = None,
    volume: Optional[str] = None,
    language: str = "en",
) -> Chapter:
    """
    Import a CBZ/CBR/7Z archive as a chapter.

    Args:
        file_path: Path to the archive file
        manga_id: ID of the manga
        chapter_number: Chapter number
        user_id: ID of the user
        db: Database session
        title: Chapter title (optional)
        volume: Volume number (optional)
        language: Language code (default: "en")

    Returns:
        The imported chapter
    """
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract archive
        if file_ext in [".zip", ".cbz"]:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        elif file_ext in [".rar", ".cbr", ".7z"]:
            # Use pyunpack for RAR and 7z files
            Archive(file_path).extractall(temp_dir)
        else:
            raise ValueError(f"Unsupported archive format: {file_ext}")

        # Get all image files
        image_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if is_image_file(file_path):
                    image_files.append(file_path)

        # Sort image files by name
        image_files.sort()

        # Create chapter
        chapter = Chapter(
            manga_id=manga_id,
            title=title or f"Chapter {chapter_number}",
            number=chapter_number,
            volume=volume,
            language=language,
            pages_count=len(image_files),
            source="import",
        )

        db.add(chapter)
        await db.flush()

        # Create chapter directory
        chapter_path = get_chapter_storage_path(manga_id, chapter.id)
        os.makedirs(chapter_path, exist_ok=True)

        # Copy images to chapter directory
        pages = []
        for i, image_file in enumerate(image_files):
            # Get page number
            page_number = i + 1

            # Get image dimensions
            width, height = get_image_dimensions(image_file)

            # Get destination path
            dest_path = get_page_storage_path(manga_id, chapter.id, page_number)

            # Copy image
            shutil.copy2(image_file, dest_path)

            # Create page
            page = Page(
                chapter_id=chapter.id,
                number=page_number,
                file_path=dest_path,
                width=width,
                height=height,
            )

            pages.append(page)

        # Add pages to database
        db.add_all(pages)

        # Update chapter
        chapter.file_path = chapter_path

        # Commit changes
        await db.commit()
        await db.refresh(chapter)

        return chapter


async def import_directory(
    directory_path: str,
    manga_id: UUID,
    chapter_number: str,
    user_id: UUID,
    db: AsyncSession,
    title: Optional[str] = None,
    volume: Optional[str] = None,
    language: str = "en",
) -> Chapter:
    """
    Import a directory of images as a chapter.

    Args:
        directory_path: Path to the directory
        manga_id: ID of the manga
        chapter_number: Chapter number
        user_id: ID of the user
        db: Database session
        title: Chapter title (optional)
        volume: Volume number (optional)
        language: Language code (default: "en")

    Returns:
        The imported chapter
    """
    # Get all image files
    image_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            if is_image_file(file_path):
                image_files.append(file_path)

    # Sort image files by name
    image_files.sort()

    # Create chapter
    chapter = Chapter(
        manga_id=manga_id,
        title=title or f"Chapter {chapter_number}",
        number=chapter_number,
        volume=volume,
        language=language,
        pages_count=len(image_files),
        source="import",
    )

    db.add(chapter)
    await db.flush()

    # Create chapter directory
    chapter_path = get_chapter_storage_path(manga_id, chapter.id)
    os.makedirs(chapter_path, exist_ok=True)

    # Copy images to chapter directory
    pages = []
    for i, image_file in enumerate(image_files):
        # Get page number
        page_number = i + 1

        # Get image dimensions
        width, height = get_image_dimensions(image_file)

        # Get destination path
        dest_path = get_page_storage_path(manga_id, chapter.id, page_number)

        # Copy image
        shutil.copy2(image_file, dest_path)

        # Create page
        page = Page(
            chapter_id=chapter.id,
            number=page_number,
            file_path=dest_path,
            width=width,
            height=height,
        )

        pages.append(page)

    # Add pages to database
    db.add_all(pages)

    # Update chapter
    chapter.file_path = chapter_path

    # Commit changes
    await db.commit()
    await db.refresh(chapter)

    return chapter


async def create_manga_from_import(
    title: str,
    user_id: UUID,
    db: AsyncSession,
    description: Optional[str] = None,
    cover_path: Optional[str] = None,
    manga_type: MangaType = MangaType.MANGA,
    status: MangaStatus = MangaStatus.UNKNOWN,
    year: Optional[int] = None,
    is_nsfw: bool = False,
    genres: Optional[List[str]] = None,
    authors: Optional[List[str]] = None,
) -> Tuple[Manga, MangaUserLibrary]:
    """
    Create a new manga from imported files.

    Args:
        title: Manga title
        user_id: ID of the user
        db: Database session
        description: Manga description (optional)
        cover_path: Path to cover image (optional)
        manga_type: Manga type (default: MANGA)
        status: Manga status (default: UNKNOWN)
        year: Publication year (optional)
        is_nsfw: Whether the manga is NSFW (default: False)
        genres: List of genre names (optional)
        authors: List of author names (optional)

    Returns:
        The created manga and library item
    """
    from app.models.manga import Genre, Author

    # Create manga
    manga = Manga(
        title=title,
        description=description,
        type=manga_type,
        status=status,
        year=year,
        is_nsfw=is_nsfw,
    )

    db.add(manga)
    await db.flush()

    # Create manga directory
    manga_path = get_manga_storage_path(manga.id)
    os.makedirs(manga_path, exist_ok=True)

    # Copy cover image if provided
    if cover_path:
        dest_path = get_cover_storage_path(manga.id)
        shutil.copy2(cover_path, dest_path)
        manga.cover_image = dest_path

    # Add genres
    if genres:
        for genre_name in genres:
            # Check if genre exists
            result = await db.execute(select(Genre).where(Genre.name == genre_name))
            genre = result.scalars().first()

            # Create genre if it doesn't exist
            if not genre:
                genre = Genre(name=genre_name)
                db.add(genre)
                await db.flush()

            manga.genres.append(genre)

    # Add authors
    if authors:
        for author_name in authors:
            # Check if author exists
            result = await db.execute(select(Author).where(Author.name == author_name))
            author = result.scalars().first()

            # Create author if it doesn't exist
            if not author:
                author = Author(name=author_name)
                db.add(author)
                await db.flush()

            manga.authors.append(author)

    # Create library item
    library_item = MangaUserLibrary(
        user_id=user_id,
        manga_id=manga.id,
    )

    db.add(library_item)

    # Commit changes
    await db.commit()
    await db.refresh(manga)
    await db.refresh(library_item)

    return manga, library_item
