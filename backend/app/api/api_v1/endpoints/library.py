import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.library import (
    Bookmark,
)
from app.models.library import LibraryCategory as Category
from app.models.library import (
    MangaUserLibrary,
    ReadingProgress,
)
from app.models.manga import Chapter, Manga
from app.models.user import User
from app.schemas.library import Bookmark as BookmarkSchema
from app.schemas.library import (
    BookmarkCreate,
)
from app.schemas.library import MangaUserLibrary as MangaUserLibrarySchema
from app.schemas.library import (
    MangaUserLibraryCreate,
    MangaUserLibraryUpdate,
)
from app.schemas.library import ReadingProgress as ReadingProgressSchema
from app.schemas.library import (
    ReadingProgressCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[MangaUserLibrarySchema])
async def read_library(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve user's library.
    """
    query = (
        select(MangaUserLibrary)
        .options(
            selectinload(MangaUserLibrary.manga).selectinload(Manga.genres),
            selectinload(MangaUserLibrary.manga).selectinload(Manga.authors),
            selectinload(MangaUserLibrary.manga).selectinload(Manga.chapters),
            selectinload(MangaUserLibrary.categories),
        )
        .where(MangaUserLibrary.user_id == current_user.id)
    )

    # Filter by category
    if category_id:
        query = query.join(MangaUserLibrary.categories).where(
            Category.id == uuid.UUID(category_id)
        )

    # Filter by favorite
    if is_favorite is not None:
        query = query.where(MangaUserLibrary.is_favorite == is_favorite)

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    library_items = result.scalars().all()

    return library_items


@router.post("", response_model=MangaUserLibrarySchema)
async def add_to_library(
    library_item: MangaUserLibraryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a manga to the user's library.
    """
    try:
        # Check if manga exists
        manga = await db.get(Manga, library_item.manga_id)
        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manga not found",
            )

        # Check if manga is already in library
        result = await db.execute(
            select(MangaUserLibrary).where(
                (MangaUserLibrary.user_id == current_user.id)
                & (MangaUserLibrary.manga_id == library_item.manga_id)
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Manga already in library",
            )

        # Create library item
        library_item_obj = MangaUserLibrary(
            **library_item.model_dump(exclude={"category_ids"}),
            user_id=current_user.id,
        )

        # Add categories using direct SQL to avoid greenlet issues
        if library_item.category_ids:
            from app.models.library import manga_user_library_category

            for category_id in library_item.category_ids:
                category = await db.get(Category, category_id)
                if category and (
                    category.is_default or category.user_id == current_user.id
                ):
                    # Use direct SQL insert instead of relationship append
                    await db.execute(
                        insert(manga_user_library_category).values(
                            manga_user_library_id=library_item_obj.id,
                            category_id=category.id,
                        )
                    )

        db.add(library_item_obj)
        await db.commit()
        await db.refresh(library_item_obj)

        # Load relationships explicitly to avoid greenlet issues during response serialization
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(MangaUserLibrary)
            .options(
                selectinload(MangaUserLibrary.manga).selectinload(Manga.genres),
                selectinload(MangaUserLibrary.manga).selectinload(Manga.authors),
                selectinload(MangaUserLibrary.manga).selectinload(Manga.chapters),
                selectinload(MangaUserLibrary.categories),
            )
            .where(MangaUserLibrary.id == library_item_obj.id)
        )
        library_item_with_relationships = result.scalars().first()

        return library_item_with_relationships

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error and return a generic error message
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error adding manga to library: {str(e)}")

        # Rollback the transaction
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add manga to library",
        )


@router.get("/{library_item_id}", response_model=MangaUserLibrarySchema)
async def read_library_item(
    library_item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a library item by ID.
    """
    library_item = await db.get(MangaUserLibrary, uuid.UUID(library_item_id))

    if not library_item or library_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found",
        )

    return library_item


@router.get("/{library_item_id}/detailed", response_model=Dict[str, Any])
async def read_library_item_detailed(
    library_item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get detailed library item information including chapters with download status.
    """
    # Get library item with all relationships
    result = await db.execute(
        select(MangaUserLibrary)
        .options(
            selectinload(MangaUserLibrary.manga).selectinload(Manga.genres),
            selectinload(MangaUserLibrary.manga).selectinload(Manga.authors),
            selectinload(MangaUserLibrary.manga).selectinload(Manga.chapters),
            selectinload(MangaUserLibrary.categories),
        )
        .where(MangaUserLibrary.id == uuid.UUID(library_item_id))
    )
    library_item = result.scalars().first()

    if not library_item or library_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found",
        )

    # Get reading progress for all chapters
    progress_result = await db.execute(
        select(ReadingProgress).where(
            (ReadingProgress.user_id == current_user.id)
            & (ReadingProgress.manga_id == library_item.manga_id)
        )
    )
    progress_by_chapter = {
        progress.chapter_id: progress for progress in progress_result.scalars().all()
    }

    # Enhance chapters with download and reading status
    enhanced_chapters = []
    for chapter in library_item.manga.chapters:
        progress = progress_by_chapter.get(chapter.id)

        # Determine download status
        download_status = "not_downloaded"
        if chapter.file_path:
            import os

            if os.path.exists(chapter.file_path):
                download_status = "downloaded"
            else:
                download_status = "error"  # File path exists but file is missing

        enhanced_chapters.append(
            {
                "id": str(chapter.id),
                "title": chapter.title,
                "number": chapter.number,
                "volume": chapter.volume,
                "language": chapter.language,
                "pages_count": chapter.pages_count,
                "file_path": chapter.file_path,
                "file_size": chapter.file_size,
                "source": chapter.source,
                "created_at": chapter.created_at,
                "updated_at": chapter.updated_at,
                "download_status": download_status,
                "reading_progress": (
                    {
                        "page": progress.page if progress else 1,
                        "is_completed": progress.is_completed if progress else False,
                    }
                    if progress
                    else None
                ),
            }
        )

    # Sort chapters by volume and number
    enhanced_chapters.sort(
        key=lambda x: (
            (
                float(x["volume"])
                if x["volume"] and x["volume"].replace(".", "").isdigit()
                else 0
            ),
            (
                float(x["number"])
                if x["number"] and x["number"].replace(".", "").isdigit()
                else 0
            ),
        )
    )

    return {
        "library_item": library_item,
        "chapters": enhanced_chapters,
        "download_summary": {
            "total_chapters": len(enhanced_chapters),
            "downloaded_chapters": len(
                [c for c in enhanced_chapters if c["download_status"] == "downloaded"]
            ),
            "failed_chapters": len(
                [c for c in enhanced_chapters if c["download_status"] == "error"]
            ),
        },
    }


@router.put("/{library_item_id}", response_model=MangaUserLibrarySchema)
async def update_library_item(
    library_item_id: str,
    library_item_update: MangaUserLibraryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a library item.
    """
    library_item = await db.get(MangaUserLibrary, uuid.UUID(library_item_id))

    if not library_item or library_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found",
        )

    # Update library item fields
    update_data = library_item_update.model_dump(
        exclude={"category_ids"}, exclude_unset=True
    )
    for field, value in update_data.items():
        setattr(library_item, field, value)

    # Update categories
    if library_item_update.category_ids is not None:
        # Clear existing categories
        library_item.categories = []

        # Add new categories
        for category_id in library_item_update.category_ids:
            category = await db.get(Category, category_id)
            if category and (
                category.is_default or category.user_id == current_user.id
            ):
                library_item.categories.append(category)

    await db.commit()
    await db.refresh(library_item)

    return library_item


@router.delete("/{library_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_library(
    library_item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a manga from the user's library.
    """
    library_item = await db.get(MangaUserLibrary, uuid.UUID(library_item_id))

    if not library_item or library_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found",
        )

    # Delete library item
    await db.delete(library_item)
    await db.commit()


@router.post("/{library_item_id}/download", response_model=Dict[str, Any])
async def download_manga(
    library_item_id: str,
    provider: str,
    external_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Download a manga to the user's library.

    Args:
        library_item_id: The ID of the library item
        provider: The name of the provider to use for downloading
        external_id: The external ID of the manga on the provider
        background_tasks: FastAPI background tasks
    """
    try:
        from app.core.providers.registry import provider_registry
        from app.core.services.background import download_manga_task

        # Check if provider exists
        provider_instance = provider_registry.get_provider(provider)
        if not provider_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{provider}' not found",
            )

        # Get library item
        library_item = await db.get(MangaUserLibrary, uuid.UUID(library_item_id))

        if not library_item or library_item.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Library item not found",
            )

        # Check if manga is already downloaded
        if library_item.is_downloaded:
            return {
                "task_id": f"{current_user.id}_{library_item.manga_id}",
                "manga_id": str(library_item.manga_id),
                "user_id": str(current_user.id),
                "provider": provider,
                "status": "already_downloaded",
                "message": "Manga is already downloaded",
            }

        # Create task ID
        task_id = f"{current_user.id}_{library_item.manga_id}"

        # Add download task to background tasks
        background_tasks.add_task(
            download_manga_task,
            manga_id=library_item.manga_id,
            user_id=current_user.id,
            provider_name=provider,
            external_id=external_id,
        )

        # Return task information
        return {
            "task_id": task_id,
            "manga_id": str(library_item.manga_id),
            "user_id": str(current_user.id),
            "provider": provider,
            "status": "queued",
            "message": "Download task has been queued",
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error and return a generic error message
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error starting download: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start download",
        )


@router.post("/progress", response_model=ReadingProgressSchema)
async def update_reading_progress(
    progress_data: ReadingProgressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update reading progress for a manga chapter.
    """
    try:
        # Check if manga and chapter exist
        manga = await db.get(Manga, progress_data.manga_id)
        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manga not found",
            )

        chapter = await db.get(Chapter, progress_data.chapter_id)
        if not chapter or chapter.manga_id != progress_data.manga_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found",
            )

        # Check if progress already exists
        result = await db.execute(
            select(ReadingProgress).where(
                (ReadingProgress.user_id == current_user.id)
                & (ReadingProgress.manga_id == progress_data.manga_id)
                & (ReadingProgress.chapter_id == progress_data.chapter_id)
            )
        )
        progress = result.scalars().first()

        if progress:
            # Update existing progress
            for field, value in progress_data.model_dump().items():
                setattr(progress, field, value)
        else:
            # Create new progress
            progress = ReadingProgress(
                **progress_data.model_dump(),
                user_id=current_user.id,
            )
            db.add(progress)

        await db.commit()
        await db.refresh(progress)

        return progress

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error and return a generic error message
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error updating reading progress: {str(e)}")

        # Rollback the transaction
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reading progress",
        )


@router.post("/{manga_id}/progress", response_model=ReadingProgressSchema)
async def update_manga_reading_progress(
    manga_id: str,
    progress_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update reading progress for a manga chapter (alternative endpoint for frontend).
    """
    try:
        # Convert to proper format
        progress_create = ReadingProgressCreate(
            manga_id=uuid.UUID(manga_id),
            chapter_id=uuid.UUID(progress_data.get("chapter_id")),
            page=progress_data.get("page", 1),
            completed=progress_data.get("completed", False),
        )

        return await update_reading_progress(progress_create, current_user, db)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error updating manga reading progress: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reading progress",
        )


@router.post("/bookmarks", response_model=BookmarkSchema)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a bookmark for a manga chapter.
    """
    # Check if manga and chapter exist
    manga = await db.get(Manga, bookmark_data.manga_id)
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    chapter = await db.get(Chapter, bookmark_data.chapter_id)
    if not chapter or chapter.manga_id != bookmark_data.manga_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    # Create bookmark
    bookmark = Bookmark(
        **bookmark_data.model_dump(),
        user_id=current_user.id,
    )

    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    return bookmark


@router.get("/bookmarks", response_model=List[BookmarkSchema])
async def read_bookmarks(
    manga_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve user's bookmarks.
    """
    query = select(Bookmark).where(Bookmark.user_id == current_user.id)

    # Filter by manga
    if manga_id:
        query = query.where(Bookmark.manga_id == uuid.UUID(manga_id))

    # Filter by chapter
    if chapter_id:
        query = query.where(Bookmark.chapter_id == uuid.UUID(chapter_id))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    bookmarks = result.scalars().all()

    return bookmarks


@router.get("/downloads", response_model=Dict[str, Any])
async def get_download_tasks(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all download tasks for the current user.
    """
    from app.core.services.background import get_user_download_tasks

    # Get user's download tasks
    tasks = get_user_download_tasks(current_user.id)

    return {"tasks": tasks, "count": len(tasks)}


@router.get("/downloads/{task_id}", response_model=Dict[str, Any])
async def get_download_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a download task by ID.
    """
    from app.core.services.background import get_download_task

    # Get task
    task = get_download_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download task not found",
        )

    # Check if task belongs to user
    if task["user_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return task


@router.delete("/downloads/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_download_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Cancel a download task.
    """
    from app.core.services.background import cancel_download_task as cancel_task
    from app.core.services.background import (
        get_download_task,
    )

    # Get task
    task = get_download_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download task not found",
        )

    # Check if task belongs to user
    if task["user_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Cancel task
    if not cancel_task(task_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel download task",
        )


@router.post("/{library_item_id}/download-chapter", response_model=Dict[str, Any])
async def download_chapter_endpoint(
    library_item_id: str,
    chapter_id: str,
    provider: str,
    external_manga_id: str,
    external_chapter_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Download a specific chapter for a manga in the user's library.
    """
    # Get library item
    library_item = await db.get(MangaUserLibrary, uuid.UUID(library_item_id))
    if not library_item or library_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found",
        )

    # Get chapter
    chapter = await db.get(Chapter, uuid.UUID(chapter_id))
    if not chapter or chapter.manga_id != library_item.manga_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    # Check if provider exists
    from app.core.providers.registry import provider_registry

    provider_instance = provider_registry.get_provider(provider)
    if not provider_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found",
        )

    try:
        # Import download function
        from app.core.services.download import download_chapter

        # Create task ID
        task_id = f"{current_user.id}_{library_item.manga_id}_{chapter_id}"

        # Add download task to background tasks
        background_tasks.add_task(
            download_chapter,
            manga_id=library_item.manga_id,
            chapter_id=chapter.id,
            provider_name=provider,
            external_manga_id=external_manga_id,
            external_chapter_id=external_chapter_id,
            db=db,
        )

        # Return task information
        return {
            "task_id": task_id,
            "manga_id": str(library_item.manga_id),
            "chapter_id": str(chapter.id),
            "user_id": str(current_user.id),
            "provider": provider,
            "status": "queued",
            "message": "Chapter download task has been queued",
        }

    except Exception as e:
        logger.error(f"Error starting chapter download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start chapter download",
        )


@router.get("/{library_item_id}/chapters/filter", response_model=Dict[str, Any])
async def get_filtered_chapters(
    library_item_id: str,
    language: Optional[str] = Query(None),
    volume: Optional[str] = Query(None),
    downloaded_only: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get filtered chapters for a library item.
    """
    # Get library item
    library_item = await db.get(MangaUserLibrary, uuid.UUID(library_item_id))
    if not library_item or library_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found",
        )

    # Build query
    query = select(Chapter).where(Chapter.manga_id == library_item.manga_id)

    if language:
        query = query.where(Chapter.language == language)

    if volume:
        query = query.where(Chapter.volume == volume)

    if downloaded_only:
        query = query.where(Chapter.file_path.isnot(None))

    # Execute query
    result = await db.execute(query.order_by(Chapter.volume, Chapter.number))
    chapters = result.scalars().all()

    # Get available languages and volumes for filtering
    all_chapters_result = await db.execute(
        select(Chapter).where(Chapter.manga_id == library_item.manga_id)
    )
    all_chapters = all_chapters_result.scalars().all()

    available_languages = list(set(c.language for c in all_chapters if c.language))
    available_volumes = list(set(c.volume for c in all_chapters if c.volume))
    available_volumes.sort(
        key=lambda x: float(x) if x and x.replace(".", "").isdigit() else 0
    )

    return {
        "chapters": [
            {
                "id": str(chapter.id),
                "title": chapter.title,
                "number": chapter.number,
                "volume": chapter.volume,
                "language": chapter.language,
                "pages_count": chapter.pages_count,
                "file_path": chapter.file_path,
                "is_downloaded": bool(chapter.file_path),
                "created_at": chapter.created_at,
                "updated_at": chapter.updated_at,
            }
            for chapter in chapters
        ],
        "filters": {
            "available_languages": available_languages,
            "available_volumes": available_volumes,
        },
        "total": len(chapters),
    }
