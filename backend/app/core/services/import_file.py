import logging
import os
import shutil
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pyunpack import Archive
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import (
    get_chapter_storage_path,
    get_cover_storage_path,
    get_image_dimensions,
    get_manga_storage_path,
    get_page_storage_path,
    is_image_file,
)
from app.models.library import MangaUserLibrary
from app.models.manga import Chapter, Manga, MangaStatus, MangaType, Page

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
    replace_existing: bool = False,
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
        replace_existing: Whether to replace existing chapter (default: False)

    Returns:
        The imported chapter

    Raises:
        ValueError: If chapter already exists and replace_existing is False
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

        # Check for existing chapter
        from sqlalchemy import select
        existing_chapter_result = await db.execute(
            select(Chapter).where(
                (Chapter.manga_id == manga_id) &
                (Chapter.number == chapter_number) &
                (Chapter.language == language)
            )
        )
        existing_chapter = existing_chapter_result.scalars().first()

        if existing_chapter:
            if not replace_existing:
                raise ValueError(
                    f"Chapter {chapter_number} already exists for this manga. "
                    f"Use replace_existing=True to overwrite."
                )
            else:
                # Delete existing chapter and its files
                await _delete_chapter_files(existing_chapter)
                await db.delete(existing_chapter)
                await db.flush()

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
    from app.models.manga import Author, Genre

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
        from app.models.manga import manga_genre

        for genre_name in genres:
            # Check if genre exists
            result = await db.execute(select(Genre).where(Genre.name == genre_name))
            genre = result.scalars().first()

            # Create genre if it doesn't exist
            if not genre:
                genre = Genre(name=genre_name)
                db.add(genre)
                await db.flush()

            # Insert into association table directly to avoid lazy loading issues
            await db.execute(
                insert(manga_genre).values(manga_id=manga.id, genre_id=genre.id)
            )

    # Add authors
    if authors:
        from app.models.manga import manga_author

        for author_name in authors:
            # Check if author exists
            result = await db.execute(select(Author).where(Author.name == author_name))
            author = result.scalars().first()

            # Create author if it doesn't exist
            if not author:
                author = Author(name=author_name)
                db.add(author)
                await db.flush()

            # Insert into association table directly to avoid lazy loading issues
            await db.execute(
                insert(manga_author).values(manga_id=manga.id, author_id=author.id)
            )

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


async def create_manga_from_external_source(
    provider_name: str,
    external_id: str,
    manga_details: Dict[str, Any],
    db: AsyncSession,
) -> Manga:
    """
    Create a new manga from external provider data.

    Args:
        provider_name: Name of the provider
        external_id: External ID of the manga
        manga_details: Manga details from the provider
        db: Database session

    Returns:
        The created manga
    """
    from app.models.manga import Author, Genre, Manga, manga_author, manga_genre

    try:
        # Create manga without relationships first
        manga = Manga(
            title=manga_details.get("title", "Unknown Title"),
            description=manga_details.get("description", ""),
            status=manga_details.get("status", "unknown"),
            year=manga_details.get("year"),
            provider=provider_name,
            external_id=external_id,
            external_url=manga_details.get("url", ""),
            cover_image=manga_details.get("cover_image", ""),
            is_nsfw=manga_details.get("is_nsfw", False)
            or manga_details.get("is_explicit", False),
        )

        db.add(manga)
        await db.flush()  # Get the manga ID
        await db.refresh(manga)

        # Handle genres using direct SQL inserts to avoid relationship issues
        genres = manga_details.get("genres", [])
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
                    await db.refresh(genre)

                # Check if relationship already exists before inserting
                existing_rel = await db.execute(
                    select(manga_genre).where(
                        (manga_genre.c.manga_id == manga.id)
                        & (manga_genre.c.genre_id == genre.id)
                    )
                )
                if not existing_rel.first():
                    # Insert into association table directly only if it doesn't exist
                    await db.execute(
                        insert(manga_genre).values(manga_id=manga.id, genre_id=genre.id)
                    )

        # Handle authors using direct SQL inserts to avoid relationship issues
        authors = manga_details.get("authors", [])
        if authors:
            for author_name in authors:
                # Check if author exists
                result = await db.execute(
                    select(Author).where(Author.name == author_name)
                )
                author = result.scalars().first()

                # Create author if it doesn't exist
                if not author:
                    author = Author(name=author_name)
                    db.add(author)
                    await db.flush()
                    await db.refresh(author)

                # Check if relationship already exists before inserting
                existing_rel = await db.execute(
                    select(manga_author).where(
                        (manga_author.c.manga_id == manga.id)
                        & (manga_author.c.author_id == author.id)
                    )
                )
                if not existing_rel.first():
                    # Insert into association table directly only if it doesn't exist
                    await db.execute(
                        insert(manga_author).values(
                            manga_id=manga.id, author_id=author.id
                        )
                    )

        # Commit all changes
        await db.commit()

        # Refresh and load relationships explicitly to avoid greenlet issues
        await db.refresh(manga)

        # Load relationships explicitly using selectinload to avoid lazy loading
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Manga)
            .options(
                selectinload(Manga.genres),
                selectinload(Manga.authors),
                selectinload(Manga.chapters),
            )
            .where(Manga.id == manga.id)
        )
        manga_with_relationships = result.scalars().first()

        return manga_with_relationships

    except Exception as e:
        await db.rollback()
        raise e


async def _delete_chapter_files(chapter: Chapter) -> None:
    """
    Delete all files associated with a chapter.

    Args:
        chapter: The chapter to delete files for
    """
    import shutil

    # Get chapter directory path
    chapter_path = get_chapter_storage_path(chapter.manga_id, chapter.id)

    # Delete chapter directory if it exists
    if os.path.exists(chapter_path):
        shutil.rmtree(chapter_path)


async def check_chapter_exists(
    manga_id: UUID,
    chapter_number: str,
    language: str,
    db: AsyncSession,
) -> Optional[Chapter]:
    """
    Check if a chapter already exists for the given manga.

    Args:
        manga_id: ID of the manga
        chapter_number: Chapter number to check
        language: Language code
        db: Database session

    Returns:
        Existing chapter if found, None otherwise
    """
    from sqlalchemy import select

    result = await db.execute(
        select(Chapter).where(
            (Chapter.manga_id == manga_id) &
            (Chapter.number == chapter_number) &
            (Chapter.language == language)
        )
    )
    return result.scalars().first()
