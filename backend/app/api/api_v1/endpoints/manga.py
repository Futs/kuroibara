import logging
import os
import uuid
from typing import Any, Dict, List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.core.services.provider_matching import provider_matching_service
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

logger = logging.getLogger(__name__)
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
                # Fix date parsing - convert string dates to timezone-naive datetime objects
                publish_at = chapter_data.get("publish_at")
                if publish_at and isinstance(publish_at, str):
                    from datetime import datetime

                    dt = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
                    publish_at = dt.replace(tzinfo=None)  # Remove timezone info

                readable_at = chapter_data.get("readable_at")
                if readable_at and isinstance(readable_at, str):
                    from datetime import datetime

                    dt = datetime.fromisoformat(readable_at.replace("Z", "+00:00"))
                    readable_at = dt.replace(tzinfo=None)  # Remove timezone info

                chapter = Chapter(
                    manga_id=uuid.UUID(manga_id),
                    title=chapter_data.get("title", f"Chapter {chapter_number}"),
                    number=chapter_number,
                    volume=chapter_data.get("volume"),
                    language=chapter_data.get("language", "en"),
                    pages_count=chapter_data.get("pages_count"),
                    source=provider_name,
                    external_id=chapter_data.get("id"),
                    publish_at=publish_at,
                    readable_at=readable_at,
                )
                db.add(chapter)
                chapters_added += 1
            else:
                # Update existing chapter with new external_id and other data
                existing_chapter.external_id = chapter_data.get("id")
                existing_chapter.title = chapter_data.get(
                    "title", f"Chapter {chapter_number}"
                )
                existing_chapter.volume = chapter_data.get("volume")
                existing_chapter.language = chapter_data.get("language", "en")
                existing_chapter.pages_count = chapter_data.get("pages_count")
                existing_chapter.source = provider_name
                # Fix date parsing - convert string dates to timezone-naive datetime objects
                if chapter_data.get("publish_at"):
                    from datetime import datetime

                    if isinstance(chapter_data.get("publish_at"), str):
                        dt = datetime.fromisoformat(
                            chapter_data.get("publish_at").replace("Z", "+00:00")
                        )
                        existing_chapter.publish_at = dt.replace(
                            tzinfo=None
                        )  # Remove timezone info
                    else:
                        existing_chapter.publish_at = chapter_data.get("publish_at")
                if chapter_data.get("readable_at"):
                    from datetime import datetime

                    if isinstance(chapter_data.get("readable_at"), str):
                        dt = datetime.fromisoformat(
                            chapter_data.get("readable_at").replace("Z", "+00:00")
                        )
                        existing_chapter.readable_at = dt.replace(
                            tzinfo=None
                        )  # Remove timezone info
                    else:
                        existing_chapter.readable_at = chapter_data.get("readable_at")

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


@router.post("/{manga_id}/sync-download-status")
async def sync_chapter_download_status(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Sync chapter download status by checking the filesystem.
    Updates chapters to 'downloaded' if they have files on disk.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    try:
        # Get all chapters for this manga
        result = await db.execute(
            select(Chapter).where(Chapter.manga_id == uuid.UUID(manga_id))
        )
        chapters = result.scalars().all()

        updated_count = 0
        already_correct = 0

        for chapter in chapters:
            # Check if chapter has a file_path
            if chapter.file_path and os.path.exists(chapter.file_path):
                # Check if directory has image files
                image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
                has_images = False

                if os.path.isdir(chapter.file_path):
                    for file in os.listdir(chapter.file_path):
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            has_images = True
                            break

                # Update status if needed
                if has_images and chapter.download_status != "downloaded":
                    chapter.download_status = "downloaded"
                    updated_count += 1
                    logger.info(
                        f"Updated chapter {chapter.number} to downloaded status"
                    )
                elif has_images and chapter.download_status == "downloaded":
                    already_correct += 1
                elif not has_images and chapter.download_status == "downloaded":
                    # Directory exists but no images - mark as error
                    chapter.download_status = "error"
                    chapter.download_error = (
                        "Chapter directory exists but contains no images"
                    )
                    updated_count += 1
                    logger.warning(
                        f"Chapter {chapter.number} directory exists but has no images"
                    )
            elif chapter.file_path and not os.path.exists(chapter.file_path):
                # File path set but doesn't exist - mark as error
                if chapter.download_status == "downloaded":
                    chapter.download_status = "error"
                    chapter.download_error = "Chapter files not found on disk"
                    updated_count += 1
                    logger.warning(
                        f"Chapter {chapter.number} marked as downloaded but files not found"
                    )

        await db.commit()

        return {
            "message": f"Synced download status for {manga.title}",
            "total_chapters": len(chapters),
            "updated": updated_count,
            "already_correct": already_correct,
        }

    except Exception as e:
        logger.error(f"Error syncing chapter download status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync download status: {str(e)}",
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


@router.get("/{manga_id}/chapters/{chapter_id}/alternatives")
async def get_chapter_alternatives(
    manga_id: str,
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get alternative sources for a chapter.
    """
    try:
        # Get manga and chapter
        manga = await db.get(Manga, uuid.UUID(manga_id))
        chapter = await db.get(Chapter, uuid.UUID(chapter_id))

        if not manga or not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manga or chapter not found",
            )

        # Find alternatives with optimized settings
        alternatives = await provider_matching_service.find_chapter_alternatives(
            manga_title=manga.title,
            chapter_number=chapter.number,
            original_provider=manga.provider
            or "mangadex",  # Fixed: mangadex not mangadx
            max_alternatives=3,  # Reduced for speed
            timeout_per_provider=8,  # 8 second timeout per provider
            max_providers_to_search=6,  # Only search top 6 providers
        )

        # Format response
        alternative_list = []
        for alt in alternatives:
            alternative_list.append(
                {
                    "provider_name": alt.provider_name,
                    "external_manga_id": alt.external_manga_id,
                    "external_chapter_id": alt.external_chapter_id,
                    "confidence": alt.confidence,
                    "chapter_title": alt.chapter_title,
                    "chapter_number": alt.chapter_number,
                }
            )

        return {
            "alternatives": alternative_list,
            "total": len(alternative_list),
        }

    except Exception as e:
        logger.error(f"Error getting chapter alternatives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chapter alternatives: {str(e)}",
        )


@router.post("/{manga_id}/chapters/{chapter_id}/download-from-provider")
async def download_chapter_from_specific_provider(
    manga_id: str,
    chapter_id: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Download chapter from a specific alternative provider.
    """
    try:
        provider_name = request.get("provider_name")
        external_manga_id = request.get("external_manga_id")
        external_chapter_id = request.get("external_chapter_id")

        if not all([provider_name, external_manga_id, external_chapter_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: provider_name, external_manga_id, external_chapter_id",
            )

        # Get manga and chapter
        manga = await db.get(Manga, uuid.UUID(manga_id))
        chapter = await db.get(Chapter, uuid.UUID(chapter_id))

        if not manga or not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manga or chapter not found",
            )

        # Verify provider exists
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_name}' not found",
            )

        # Add download task with specific provider
        from app.core.services.background import add_download_task

        task_id = add_download_task(
            user_id=current_user.id,
            manga_id=uuid.UUID(manga_id),
            chapter_id=uuid.UUID(chapter_id),
            provider=provider_name,
            external_manga_id=external_manga_id,
            external_chapter_id=external_chapter_id,
        )

        return {
            "message": f"Chapter download from {provider_name} has been queued",
            "task_id": task_id,
            "provider": provider_name,
            "status": "queued",
        }

    except Exception as e:
        logger.error(f"Error downloading chapter from specific provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download chapter: {str(e)}",
        )


@router.post("/{manga_id}/discover-alternatives")
async def discover_chapter_alternatives(
    manga_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Discover and store alternative sources for all chapters in a manga.
    This is a background task that may take several minutes for large manga.
    """
    try:
        # Get manga
        manga = await db.get(Manga, uuid.UUID(manga_id))
        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manga not found",
            )

        # Get all chapters
        result = await db.execute(
            select(Chapter).where(Chapter.manga_id == uuid.UUID(manga_id))
        )
        chapters = result.scalars().all()

        if not chapters:
            return {
                "message": "No chapters found for this manga",
                "discovered_count": 0,
                "total_chapters": 0,
                "status": "completed",
            }

        # For small number of chapters (< 10), process immediately
        if len(chapters) < 10:
            discovered_count = 0

            for chapter in chapters:
                try:
                    # Find alternatives for this chapter with optimized settings
                    alternatives = (
                        await provider_matching_service.find_chapter_alternatives(
                            manga_title=manga.title,
                            chapter_number=chapter.number,
                            original_provider=manga.provider or "mangadex",
                            max_alternatives=2,  # Reduced for speed
                            timeout_per_provider=5,  # 5 second timeout per provider
                            max_providers_to_search=4,  # Only search top 4 providers
                        )
                    )

                    if alternatives:
                        # Store provider external IDs
                        if not chapter.provider_external_ids:
                            chapter.provider_external_ids = {}

                        # Store fallback providers
                        fallback_providers = []

                        for alt in alternatives:
                            chapter.provider_external_ids[alt.provider_name.lower()] = (
                                alt.external_chapter_id
                            )
                            fallback_providers.append(alt.provider_name)

                        chapter.fallback_providers = fallback_providers
                        discovered_count += 1

                except Exception as e:
                    logger.warning(
                        f"Error discovering alternatives for chapter {chapter.id}: {e}"
                    )
                    continue

            await db.commit()

            return {
                "message": f"Discovered alternatives for {discovered_count} chapters",
                "discovered_count": discovered_count,
                "total_chapters": len(chapters),
                "status": "completed",
            }

        # For large number of chapters, queue as background task
        else:
            # Add background task
            from app.core.services.background import discover_alternatives_task

            background_tasks.add_task(
                discover_alternatives_task,
                manga_id=uuid.UUID(manga_id),
                manga_title=manga.title,
                provider=manga.provider or "mangadex",
            )

            return {
                "message": f"Alternative discovery queued for {len(chapters)} chapters. This may take several minutes.",
                "discovered_count": 0,
                "total_chapters": len(chapters),
                "status": "queued",
            }

    except Exception as e:
        logger.error(f"Error discovering chapter alternatives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover alternatives: {str(e)}",
        )
