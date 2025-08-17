import logging
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.registry import provider_registry
from app.core.utils import (
    create_cbz_from_directory,
    get_chapter_storage_path,
    get_cover_storage_path,
    get_manga_storage_path,
    get_page_storage_path,
)
from app.models.library import MangaUserLibrary
from app.models.manga import Chapter, Manga, Page

logger = logging.getLogger(__name__)


async def download_manga_cover(
    manga_id: UUID,
    provider_name: str,
    external_id: str,
    db: AsyncSession,
) -> str:
    """
    Download a manga cover.

    Args:
        manga_id: The ID of the manga
        provider_name: The name of the provider
        external_id: The external ID of the manga
        db: The database session

    Returns:
        The path to the downloaded cover
    """
    # Get provider
    provider = provider_registry.get_provider(provider_name)
    if not provider:
        raise ValueError(f"Provider '{provider_name}' not found")

    # Create manga storage directory
    manga_path = get_manga_storage_path(manga_id)
    os.makedirs(manga_path, exist_ok=True)

    # Download cover
    cover_data = await provider.download_cover(external_id)

    # Save cover
    cover_path = get_cover_storage_path(manga_id)
    with open(cover_path, "wb") as f:
        f.write(cover_data)

    # Update manga in database
    manga = await db.get(Manga, manga_id)
    if manga:
        manga.cover_image = cover_path
        await db.commit()

    return cover_path


async def download_chapter(
    manga_id: UUID,
    chapter_id: UUID,
    provider_name: str,
    external_manga_id: str,
    external_chapter_id: str,
    db: AsyncSession,
) -> str:
    """
    Download a chapter.

    Args:
        manga_id: The ID of the manga
        chapter_id: The ID of the chapter
        provider_name: The name of the provider
        external_manga_id: The external ID of the manga
        external_chapter_id: The external ID of the chapter
        db: The database session

    Returns:
        The path to the downloaded chapter
    """
    # Get provider
    provider = provider_registry.get_provider(provider_name)
    if not provider:
        raise ValueError(f"Provider '{provider_name}' not found")

    # Create chapter storage directory
    chapter_path = get_chapter_storage_path(manga_id, chapter_id)
    os.makedirs(chapter_path, exist_ok=True)

    # Get pages
    page_urls = await provider.get_pages(external_manga_id, external_chapter_id)

    # Download pages with optimized rate limiting for page downloads
    import asyncio

    # Provider-specific page download delays (much faster than API calls)
    page_delays = {
        "MangaDx": 0.5,  # 500ms for MangaDx pages (vs 5s for API)
        "MangaPill": 0.3,  # 300ms for MangaPill pages
        "Toonily": 0.4,  # 400ms for Toonily pages
        "MangaTown": 0.5,  # 500ms for MangaTown pages
        "ManhuaFast": 0.6,  # 600ms for ManhuaFast pages
        "ArcaneScans": 0.5,  # 500ms for ArcaneScans pages
        "Manga18FX": 0.7,  # 700ms for NSFW providers
        "MangaFreak": 0.5,  # 500ms for MangaFreak pages
        "MangaSail": 0.4,  # 400ms for MangaSail pages
        "MangaKakalotFun": 0.3,  # 300ms for MangaKakalotFun pages
        "MangaDNA": 0.5,  # 500ms for MangaDNA pages
    }

    page_delay = page_delays.get(provider_name, 0.5)  # Default 500ms

    pages = []
    for i, page_url in enumerate(page_urls):
        # Add delay between page downloads (much shorter than API delays)
        if i > 0:
            await asyncio.sleep(page_delay)

        # Download page
        page_data = await provider.download_page(page_url)

        # Save page
        page_number = i + 1
        # Determine file extension from URL or default to .jpg
        file_ext = ".jpg"
        if "." in page_url:
            url_ext = page_url.split(".")[-1].lower()
            if url_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                file_ext = f".{url_ext}"

        page_path = get_page_storage_path(manga_id, chapter_id, page_number, file_ext)

        # Only save if we got actual data
        if page_data and len(page_data) > 0:
            os.makedirs(os.path.dirname(page_path), exist_ok=True)
            with open(page_path, "wb") as f:
                f.write(page_data)
        else:
            # Create empty file to track failed download
            os.makedirs(os.path.dirname(page_path), exist_ok=True)
            with open(page_path, "wb") as f:
                f.write(b"")

        # Create page object
        page = Page(
            chapter_id=chapter_id,
            number=page_number,
            file_path=page_path,
        )

        # Add page to list
        pages.append(page)

    # Update chapter in database
    chapter = await db.get(Chapter, chapter_id)
    if chapter:
        # Update chapter
        chapter.pages_count = len(pages)
        chapter.file_path = chapter_path

        # Add pages to database
        db.add_all(pages)

        # Commit changes
        await db.commit()

    # Create CBZ file
    cbz_path = f"{chapter_path}.cbz"
    create_cbz_from_directory(chapter_path, cbz_path)

    return cbz_path


async def download_manga(
    manga_id: UUID,
    user_id: UUID,
    provider_name: str,
    external_id: str,
    db: AsyncSession,
) -> None:
    """
    Download a manga.

    Args:
        manga_id: The ID of the manga
        user_id: The ID of the user
        provider_name: The name of the provider
        external_id: The external ID of the manga
        db: The database session
    """
    # Get provider
    provider = provider_registry.get_provider(provider_name)
    if not provider:
        raise ValueError(f"Provider '{provider_name}' not found")

    # Get manga
    manga = await db.get(Manga, manga_id)
    if not manga:
        raise ValueError(f"Manga with ID '{manga_id}' not found")

    # Download cover
    await download_manga_cover(manga_id, provider_name, external_id, db)

    # Get chapters
    chapters, _, _ = await provider.get_chapters(external_id)

    # Download chapters
    for chapter_data in chapters:
        # Check if chapter already exists
        result = await db.execute(
            select(Chapter).where(
                (Chapter.manga_id == manga_id)
                & (Chapter.number == chapter_data["number"])
            )
        )
        chapter = result.scalars().first()

        if not chapter:
            # Create chapter
            chapter = Chapter(
                manga_id=manga_id,
                title=chapter_data["title"],
                number=chapter_data["number"],
                volume=chapter_data["volume"],
                language=chapter_data["language"],
                pages_count=chapter_data["pages_count"],
                source=provider_name,
            )

            db.add(chapter)
            await db.flush()

        # Download chapter
        await download_chapter(
            manga_id=manga_id,
            chapter_id=chapter.id,
            provider_name=provider_name,
            external_manga_id=external_id,
            external_chapter_id=chapter_data["id"],
            db=db,
        )

    # Update user library
    result = await db.execute(
        select(MangaUserLibrary).where(
            (MangaUserLibrary.user_id == user_id)
            & (MangaUserLibrary.manga_id == manga_id)
        )
    )
    library_item = result.scalars().first()

    if library_item:
        # Update library item
        library_item.is_downloaded = True
        library_item.download_path = get_manga_storage_path(manga_id)

        # Commit changes
        await db.commit()
