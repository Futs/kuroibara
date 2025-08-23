import logging
import os
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.registry import provider_registry
from app.core.services.provider_matching import provider_matching_service
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


async def download_chapter_with_fallback(
    manga_id: UUID,
    chapter_id: UUID,
    primary_provider: str,
    external_manga_id: str,
    external_chapter_id: str,
    db: AsyncSession,
    fallback_providers: Optional[List[str]] = None,
    auto_discover_alternatives: bool = True,
) -> str:
    """
    Download a chapter with automatic fallback to alternative providers.

    Args:
        manga_id: The ID of the manga
        chapter_id: The ID of the chapter
        primary_provider: The primary provider to try first
        external_manga_id: The external ID of the manga on primary provider
        external_chapter_id: The external ID of the chapter on primary provider
        db: The database session
        fallback_providers: List of fallback providers to try
        auto_discover_alternatives: Whether to auto-discover alternatives if fallback fails

    Returns:
        The path to the downloaded chapter

    Raises:
        Exception: If all providers fail to download the chapter
    """
    # Get manga and chapter info for fallback discovery
    manga = await db.get(Manga, manga_id)
    chapter = await db.get(Chapter, chapter_id)

    if not manga or not chapter:
        raise ValueError(f"Manga or chapter not found: {manga_id}, {chapter_id}")

    # Try primary provider first
    try:
        logger.info(f"Attempting download from primary provider: {primary_provider}")
        result = await download_chapter(
            manga_id,
            chapter_id,
            primary_provider,
            external_manga_id,
            external_chapter_id,
            db,
        )

        # Update chapter with successful provider info
        chapter.source = primary_provider
        if not chapter.provider_external_ids:
            chapter.provider_external_ids = {}
        chapter.provider_external_ids[primary_provider.lower()] = external_chapter_id
        await db.commit()

        logger.info(
            f"Successfully downloaded chapter from primary provider: {primary_provider}"
        )
        return result

    except Exception as e:
        logger.warning(f"Primary provider {primary_provider} failed: {e}")

        # Update chapter with error info
        chapter.download_error = f"Primary provider failed: {str(e)}"
        await db.commit()

        # Try fallback providers
        if fallback_providers:
            for fallback_provider in fallback_providers:
                try:
                    logger.info(f"Trying fallback provider: {fallback_provider}")

                    # Check if we have external IDs for this provider
                    fallback_external_manga_id = external_manga_id
                    fallback_external_chapter_id = external_chapter_id

                    # If we have provider-specific external IDs, use them
                    if (
                        chapter.provider_external_ids
                        and fallback_provider.lower() in chapter.provider_external_ids
                    ):
                        fallback_external_chapter_id = chapter.provider_external_ids[
                            fallback_provider.lower()
                        ]

                    result = await download_chapter(
                        manga_id,
                        chapter_id,
                        fallback_provider,
                        fallback_external_manga_id,
                        fallback_external_chapter_id,
                        db,
                    )

                    # Update chapter with successful fallback provider info
                    chapter.source = fallback_provider
                    chapter.download_error = None
                    if not chapter.provider_external_ids:
                        chapter.provider_external_ids = {}
                    chapter.provider_external_ids[fallback_provider.lower()] = (
                        fallback_external_chapter_id
                    )
                    await db.commit()

                    logger.info(
                        f"Successfully downloaded chapter from fallback provider: {fallback_provider}"
                    )
                    return result

                except Exception as fallback_error:
                    logger.warning(
                        f"Fallback provider {fallback_provider} failed: {fallback_error}"
                    )
                    continue

        # Try auto-discovery of alternatives if enabled
        if auto_discover_alternatives:
            try:
                logger.info("Attempting auto-discovery of alternative sources")
                alternatives = (
                    await provider_matching_service.find_chapter_alternatives(
                        manga_title=manga.title,
                        chapter_number=chapter.number,
                        original_provider=primary_provider,
                        exclude_providers=fallback_providers or [],
                        max_alternatives=3,
                    )
                )

                for alternative in alternatives:
                    try:
                        logger.info(
                            f"Trying auto-discovered alternative: {alternative.provider_name} (confidence: {alternative.confidence:.2f})"
                        )

                        result = await download_chapter(
                            manga_id,
                            chapter_id,
                            alternative.provider_name,
                            alternative.external_manga_id,
                            alternative.external_chapter_id,
                            db,
                        )

                        # Update chapter with successful alternative provider info
                        chapter.source = alternative.provider_name
                        chapter.download_error = None
                        if not chapter.provider_external_ids:
                            chapter.provider_external_ids = {}
                        chapter.provider_external_ids[
                            alternative.provider_name.lower()
                        ] = alternative.external_chapter_id
                        await db.commit()

                        logger.info(
                            f"Successfully downloaded chapter from auto-discovered provider: {alternative.provider_name}"
                        )
                        return result

                    except Exception as alt_error:
                        logger.warning(
                            f"Auto-discovered provider {alternative.provider_name} failed: {alt_error}"
                        )
                        continue

            except Exception as discovery_error:
                logger.warning(f"Auto-discovery failed: {discovery_error}")

        # All providers failed
        error_msg = f"All providers failed to download chapter {chapter_id}. Primary: {primary_provider}, Fallbacks: {fallback_providers}"
        chapter.download_error = error_msg
        await db.commit()

        raise Exception(error_msg)


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
