import logging
import os
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.core.utils import (
    get_cover_storage_path,
    get_manga_storage_path,
)
from app.models.library import MangaUserLibrary
from app.models.manga import Author, Chapter, Genre, Manga, Page
from app.models.user import User
from app.schemas.manga import Chapter as ChapterSchema
from app.schemas.manga import (
    ChapterCreate,
)
from app.schemas.manga import Manga as MangaSchema
from app.schemas.manga import (
    MangaCreate,
    MangaSummary,
    MangaUpdate,
)

router = APIRouter()


@router.get("", response_model=List[MangaSchema])
async def read_manga(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve manga.
    """
    result = await db.execute(
        select(Manga)
        .options(
            selectinload(Manga.genres),
            selectinload(Manga.authors),
            selectinload(Manga.chapters).selectinload(Chapter.pages),
        )
        .offset(skip)
        .limit(limit)
    )
    manga_list = result.scalars().all()
    return manga_list


@router.post("", response_model=MangaSchema)
async def create_manga(
    manga_data: MangaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new manga.
    """
    # Create manga
    manga = Manga(**manga_data.model_dump(exclude={"genres", "authors"}))

    # Add genres
    if manga_data.genres:
        for genre_name in manga_data.genres:
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
    if manga_data.authors:
        for author_name in manga_data.authors:
            # Check if author exists
            result = await db.execute(select(Author).where(Author.name == author_name))
            author = result.scalars().first()

            # Create author if it doesn't exist
            if not author:
                author = Author(name=author_name)
                db.add(author)
                await db.flush()

            manga.authors.append(author)

    db.add(manga)
    await db.commit()
    await db.refresh(manga)

    return manga


@router.get("/{manga_id}", response_model=MangaSummary)
async def read_manga_by_id(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get manga by ID.
    """
    # Load manga with relationships explicitly to avoid greenlet issues during response serialization
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Manga)
        .options(
            selectinload(Manga.genres),
            selectinload(Manga.authors),
            selectinload(Manga.chapters).selectinload(Chapter.pages),
        )
        .where(Manga.id == uuid.UUID(manga_id))
    )
    manga = result.scalars().first()

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    return manga


@router.put("/{manga_id}", response_model=MangaSchema)
async def update_manga(
    manga_id: str,
    manga_update: MangaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Update manga fields
    update_data = manga_update.model_dump(
        exclude={"genres", "authors"}, exclude_unset=True
    )
    for field, value in update_data.items():
        setattr(manga, field, value)

    # Update genres
    if manga_update.genres is not None:
        # Clear existing genres
        manga.genres = []

        # Add new genres
        for genre_name in manga_update.genres:
            # Check if genre exists
            result = await db.execute(select(Genre).where(Genre.name == genre_name))
            genre = result.scalars().first()

            # Create genre if it doesn't exist
            if not genre:
                genre = Genre(name=genre_name)
                db.add(genre)
                await db.flush()

            manga.genres.append(genre)

    # Update authors
    if manga_update.authors is not None:
        # Clear existing authors
        manga.authors = []

        # Add new authors
        for author_name in manga_update.authors:
            # Check if author exists
            result = await db.execute(select(Author).where(Author.name == author_name))
            author = result.scalars().first()

            # Create author if it doesn't exist
            if not author:
                author = Author(name=author_name)
                db.add(author)
                await db.flush()

            manga.authors.append(author)

    await db.commit()
    await db.refresh(manga)

    return manga


@router.delete("/{manga_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Delete manga
    await db.delete(manga)
    await db.commit()


@router.post("/{manga_id}/cover", response_model=MangaSchema)
async def upload_manga_cover(
    manga_id: str,
    cover: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload a cover image for a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # In a real implementation, this would save the cover image to a storage system
    # and update the manga's cover_image field with the path to the image

    # For now, just update the manga with a placeholder path
    manga.cover_image = f"/covers/{manga_id}.jpg"

    await db.commit()
    await db.refresh(manga)

    return manga


@router.get("/{manga_id}/chapters", response_model=List[ChapterSchema])
async def read_manga_chapters(
    manga_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get chapters for a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.pages))
        .where(Chapter.manga_id == uuid.UUID(manga_id))
        .order_by(Chapter.number)
        .offset(skip)
        .limit(limit)
    )
    chapters = result.scalars().all()

    return chapters


@router.post("/{manga_id}/chapters", response_model=ChapterSchema)
async def create_manga_chapter(
    manga_id: str,
    chapter_data: ChapterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new chapter for a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Create chapter
    chapter = Chapter(**chapter_data.model_dump())

    db.add(chapter)
    await db.commit()

    # Load chapter with pages relationship
    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.pages))
        .where(Chapter.id == chapter.id)
    )
    chapter_with_pages = result.scalars().first()

    return chapter_with_pages


@router.post("/{manga_id}/refresh-chapters")
async def refresh_manga_chapters(
    manga_id: str,
    provider_id: str = Query(
        None, description="Override provider to use for fetching chapters"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh/fetch chapters for a manga from its provider.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Determine which provider to use
    if provider_id:
        # Use specified provider
        provider_name = provider_id
        external_id = manga.external_id
    elif manga.provider:
        # Use manga's existing provider (normalize to lowercase)
        provider_name = manga.provider.lower()
        external_id = manga.external_id
    else:
        # Try to find the manga on available providers
        # For now, try MangaDex as it's the most common
        provider_name = "mangadex"
        external_id = manga.external_id

    if not external_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manga has no external ID to fetch chapters from",
        )

    # Get provider
    provider = provider_registry.get_provider(provider_name)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_name}' not found",
        )

    try:
        # Fetch chapters from provider
        chapters_data, total_chapters, has_more = await provider.get_chapters(
            external_id
        )

        if not chapters_data:
            return {
                "message": "No chapters found for this manga",
                "chapters_added": 0,
                "total_chapters": 0,
            }

        # Update manga provider if not set
        if not manga.provider:
            manga.provider = provider_name
            await db.commit()

        chapters_added = 0
        for chapter_data in chapters_data:
            # Check if chapter already exists
            # Convert chapter number to string for comparison
            chapter_number = str(chapter_data.get("number", ""))
            result = await db.execute(
                select(Chapter).where(
                    (Chapter.manga_id == uuid.UUID(manga_id))
                    & (Chapter.number == chapter_number)
                )
            )
            existing_chapter = result.scalars().first()

            if not existing_chapter:
                # Create new chapter
                chapter = Chapter(
                    manga_id=uuid.UUID(manga_id),
                    title=chapter_data.get("title", f"Chapter {chapter_number}"),
                    number=chapter_number,
                    volume=chapter_data.get("volume"),
                    language=chapter_data.get("language", "en"),
                    pages_count=chapter_data.get("pages_count"),
                    source=provider_name,
                    external_id=chapter_data.get("id"),
                    publish_at=chapter_data.get("publish_at"),
                    readable_at=chapter_data.get("readable_at"),
                )
                db.add(chapter)
                chapters_added += 1

        await db.commit()

        return {
            "message": f"Successfully refreshed chapters for {manga.title}",
            "chapters_added": chapters_added,
            "total_chapters": len(chapters_data),
            "provider": provider_name,
        }

    except Exception as e:
        logging.error(f"Error refreshing chapters for manga {manga_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh chapters: {str(e)}",
        )


@router.get("/external/{provider}/{manga_id}")
async def get_external_manga_details(
    provider: str,
    manga_id: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get details for an external manga from a provider.
    """
    # Get the provider
    provider_instance = provider_registry.get_provider(provider)
    if not provider_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found",
        )

    try:
        # Get manga details from the provider
        manga_details = await provider_instance.get_manga_details(manga_id)

        # Get chapters from the provider
        chapters, _, _ = await provider_instance.get_chapters(manga_id)

        # Add chapters to the manga details
        manga_details["chapters"] = chapters

        return manga_details
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch manga details: {str(e)}",
        )


@router.get("/{manga_id}/cover")
async def get_manga_cover(
    manga_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Get the cover image for a manga.
    """
    # Check if manga exists
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # First, check if we have a local cover file
    cover_path = get_cover_storage_path(uuid.UUID(manga_id))

    if os.path.exists(cover_path):
        # Return local cover file
        return FileResponse(
            path=cover_path, media_type="image/jpeg", filename=f"cover_{manga_id}.jpg"
        )

    # If no local file, check if we have an external cover URL
    if manga.cover_image and (
        manga.cover_image.startswith("http://")
        or manga.cover_image.startswith("https://")
    ):
        # Download and cache the external cover
        pass

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(manga.cover_image, timeout=10.0)
                response.raise_for_status()

                # Create manga storage directory if it doesn't exist
                manga_storage_path = get_manga_storage_path(uuid.UUID(manga_id))
                os.makedirs(manga_storage_path, exist_ok=True)

                # Save the cover locally for future requests
                with open(cover_path, "wb") as f:
                    f.write(response.content)

                # Determine media type from response headers or file extension
                media_type = response.headers.get("content-type", "image/jpeg")
                if not media_type.startswith("image/"):
                    media_type = "image/jpeg"

                return FileResponse(
                    path=cover_path,
                    media_type=media_type,
                    filename=f"cover_{manga_id}.jpg",
                )
        except Exception:
            # If download fails, fall through to 404
            pass

    # No cover available
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Cover image not found",
    )


@router.get("/{manga_id}/chapters/{chapter_id}/pages/{page_number}")
async def get_manga_page(
    manga_id: str,
    chapter_id: str,
    page_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Get a specific page from a manga chapter.
    """
    # Check if manga exists
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if chapter exists
    chapter = await db.get(Chapter, uuid.UUID(chapter_id))
    if not chapter or chapter.manga_id != uuid.UUID(manga_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    # Get page from database
    result = await db.execute(
        select(Page).where(
            (Page.chapter_id == uuid.UUID(chapter_id)) & (Page.number == page_number)
        )
    )
    page = result.scalars().first()

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found",
        )

    # Check if page file exists
    if not os.path.exists(page.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page file not found",
        )

    # Determine media type based on file extension
    file_ext = os.path.splitext(page.file_path)[1].lower()
    media_type = "image/jpeg"
    if file_ext == ".png":
        media_type = "image/png"
    elif file_ext == ".gif":
        media_type = "image/gif"
    elif file_ext == ".webp":
        media_type = "image/webp"

    return FileResponse(
        path=page.file_path,
        media_type=media_type,
        filename=f"page_{page_number}{file_ext}",
    )


@router.get("/{manga_id}/chapters/{chapter_id}")
async def get_chapter_by_id(
    manga_id: str,
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChapterSchema:
    """
    Get a specific chapter by ID.
    """
    # Check if manga exists
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if chapter exists with eager loading
    result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.pages))
        .where(Chapter.id == uuid.UUID(chapter_id))
    )
    chapter = result.scalars().first()

    if not chapter or chapter.manga_id != uuid.UUID(manga_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    return chapter


@router.get("/{manga_id}/chapters/{chapter_id}/pages")
async def get_chapter_pages(
    manga_id: str,
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get pages for a specific chapter.
    """
    # Check if manga exists
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if chapter exists
    chapter = await db.get(Chapter, uuid.UUID(chapter_id))
    if not chapter or chapter.manga_id != uuid.UUID(manga_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    # Get pages
    result = await db.execute(
        select(Page)
        .where(Page.chapter_id == uuid.UUID(chapter_id))
        .order_by(Page.number)
    )
    pages = result.scalars().all()

    # Return page data with URLs
    page_data = []
    for page in pages:
        page_data.append(
            {
                "id": str(page.id),
                "number": page.number,
                "url": f"/api/v1/manga/{manga_id}/chapters/{chapter_id}/pages/{page.number}",
                "file_path": page.file_path,
            }
        )

    return page_data


@router.post("/from-external", response_model=MangaSummary)
async def create_manga_from_external(
    provider: str,
    external_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a local manga record from external provider data.
    """
    try:
        # Get the provider
        provider_instance = provider_registry.get_provider(provider)
        if not provider_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider}' not found",
            )

        # Check if manga already exists
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Manga)
            .options(
                selectinload(Manga.genres),
                selectinload(Manga.authors),
                selectinload(Manga.chapters).selectinload(Chapter.pages),
            )
            .where((Manga.provider == provider) & (Manga.external_id == external_id))
        )
        existing_manga = result.scalars().first()
        if existing_manga:
            return existing_manga

        # Get manga details from the provider
        manga_details = await provider_instance.get_manga_details(external_id)

        # Create manga record using the service function
        from app.core.services.import_file import create_manga_from_external_source

        manga = await create_manga_from_external_source(
            provider_name=provider,
            external_id=external_id,
            manga_details=manga_details,
            db=db,
        )

        return manga

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create manga from external source: {str(e)}",
        )


@router.post("/{manga_id}/organize-chapters")
async def organize_chapters(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Organize and rename chapters based on smart matching.

    This endpoint will:
    1. Analyze chapter titles and numbers
    2. Match imported chapters with downloaded chapters
    3. Rename chapters to have consistent naming
    4. Sort chapters properly
    """
    # Check if manga exists and belongs to user
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if user has access to manga
    result = await db.execute(
        select(MangaUserLibrary).where(
            (MangaUserLibrary.user_id == current_user.id)
            & (MangaUserLibrary.manga_id == uuid.UUID(manga_id))
        )
    )
    library_item = result.scalars().first()
    if not library_item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Get all chapters for this manga
    chapters_result = await db.execute(
        select(Chapter)
        .where(Chapter.manga_id == uuid.UUID(manga_id))
        .order_by(Chapter.number.asc())
    )
    chapters = chapters_result.scalars().all()

    changes = []

    try:
        # Organize chapters by smart matching and renaming
        for chapter in chapters:
            original_title = chapter.title

            # Smart title cleaning and normalization
            new_title = _normalize_chapter_title(chapter.title, chapter.number)

            if new_title != original_title:
                chapter.title = new_title
                changes.append(
                    {
                        "id": str(chapter.id),
                        "description": f"Chapter {chapter.number}: '{original_title}' → '{new_title}'",
                    }
                )

        await db.commit()

        return {
            "message": f"Organized {len(changes)} chapters successfully",
            "changes": changes,
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to organize chapters: {str(e)}",
        )


def _normalize_chapter_title(title: str, chapter_number: str) -> str:
    """
    Normalize chapter title by removing redundant information and cleaning up formatting.
    """
    import re

    if not title:
        return ""

    # Remove file extensions
    title = re.sub(r"\.(cbz|cbr|zip|rar|7z)$", "", title, flags=re.IGNORECASE)

    # Remove chapter number if it's at the beginning
    title = re.sub(
        rf"^ch\.?\s*{re.escape(chapter_number)}\s*:?\s*", "", title, flags=re.IGNORECASE
    )
    title = re.sub(
        rf"^chapter\s*{re.escape(chapter_number)}\s*:?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(rf"^{re.escape(chapter_number)}\s*:?\s*", "", title)

    # Remove volume information
    title = re.sub(r"vol\.?\s*\d+\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"volume\s*\d+\s*", "", title, flags=re.IGNORECASE)

    # Remove scan group information in brackets/parentheses at the end
    title = re.sub(r"\s*\([^)]*scan[^)]*\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\[[^\]]*scan[^\]]*\]\s*$", "", title, flags=re.IGNORECASE)

    # Remove language codes
    title = re.sub(r"\s*\(en\)\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\[en\]\s*", "", title, flags=re.IGNORECASE)

    # Clean up extra whitespace and dashes
    title = re.sub(r"\s*-\s*$", "", title)  # Remove trailing dash
    title = re.sub(r"^\s*-\s*", "", title)  # Remove leading dash
    title = re.sub(r"\s+", " ", title)  # Normalize whitespace
    title = title.strip()

    return title


@router.patch("/{manga_id}/chapters/batch-update")
async def batch_update_chapters(
    manga_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Batch update chapter titles.
    """
    # Check if manga exists and belongs to user
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if user has access to manga
    result = await db.execute(
        select(MangaUserLibrary).where(
            (MangaUserLibrary.user_id == current_user.id)
            & (MangaUserLibrary.manga_id == uuid.UUID(manga_id))
        )
    )
    library_item = result.scalars().first()
    if not library_item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    try:
        updated_count = 0
        for update in updates.get("updates", []):
            chapter_id = update.get("id")
            new_title = update.get("title")

            if not chapter_id or new_title is None:
                continue

            chapter = await db.get(Chapter, uuid.UUID(chapter_id))
            if chapter and chapter.manga_id == uuid.UUID(manga_id):
                chapter.title = new_title
                updated_count += 1

        await db.commit()

        return {
            "message": f"Updated {updated_count} chapters successfully",
            "updated_count": updated_count,
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chapters: {str(e)}",
        )
