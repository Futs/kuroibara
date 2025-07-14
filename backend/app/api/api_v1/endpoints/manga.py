import os
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.core.utils import (
    get_cover_storage_path,
    get_manga_storage_path,
)
from app.models.manga import Author, Chapter, Genre, Manga, Page
from app.models.user import User
from app.schemas.manga import Chapter as ChapterSchema
from app.schemas.manga import (
    ChapterCreate,
)
from app.schemas.manga import Manga as MangaSchema
from app.schemas.manga import (
    MangaCreate,
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
    result = await db.execute(select(Manga).offset(skip).limit(limit))
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


@router.get("/{manga_id}", response_model=MangaSchema)
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
            selectinload(Manga.chapters),
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
    await db.refresh(chapter)

    return chapter


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

    # Check if chapter exists
    chapter = await db.get(Chapter, uuid.UUID(chapter_id))
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


@router.post("/from-external", response_model=MangaSchema)
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
                selectinload(Manga.chapters),
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
