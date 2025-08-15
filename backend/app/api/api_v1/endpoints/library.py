import logging
import math
import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, insert, select
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
from app.schemas.base import PaginatedResponse, PaginationInfo
from app.schemas.library import Bookmark as BookmarkSchema
from app.schemas.library import (
    BookmarkCreate,
    BulkDeleteRequest,
    BulkFavoritesRequest,
    BulkMarkReadRequest,
    BulkMarkUnreadRequest,
    BulkOperationResponse,
    BulkUpdateMetadataRequest,
    BulkUpdateTagsRequest,
    DownloadChapterRequest,
)
from app.schemas.library import MangaUserLibrary as MangaUserLibrarySchema
from app.schemas.library import (
    MangaUserLibraryCreate,
    MangaUserLibrarySummary,
    MangaUserLibraryUpdate,
)
from app.schemas.library import ReadingProgress as ReadingProgressSchema
from app.schemas.library import (
    ReadingProgressCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[MangaUserLibrarySummary])
async def read_library(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    manga_id: Optional[str] = None,
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

    # Filter by manga_id
    if manga_id:
        query = query.where(MangaUserLibrary.manga_id == uuid.UUID(manga_id))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Apply pagination
    paginated_query = query.offset(skip).limit(limit)

    result = await db.execute(paginated_query)
    library_items = result.scalars().all()

    # Calculate pagination info
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = math.ceil(total / limit) if limit > 0 else 1

    return PaginatedResponse(
        items=library_items,
        pagination=PaginationInfo(total=total, page=page, size=limit, pages=pages),
    )


@router.get("/check/{manga_id}", response_model=Dict[str, Any])
async def check_library_status(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Check if a manga is in the user's library.
    """
    try:
        # Check if manga exists in user's library
        result = await db.execute(
            select(MangaUserLibrary).where(
                (MangaUserLibrary.user_id == current_user.id)
                & (MangaUserLibrary.manga_id == uuid.UUID(manga_id))
            )
        )
        library_item = result.scalars().first()

        return {
            "manga_id": manga_id,
            "in_library": library_item is not None,
            "library_item_id": str(library_item.id) if library_item else None,
        }
    except Exception:
        # If there's any error (like invalid UUID), return not in library
        return {
            "manga_id": manga_id,
            "in_library": False,
            "library_item_id": None,
        }


@router.get("/check-external", response_model=Dict[str, Any])
async def check_external_library_status(
    provider: str = Query(...),
    external_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Check if an external manga is in the user's library by provider and external_id.
    """
    try:
        # Find manga by provider and external_id
        result = await db.execute(
            select(Manga).where(
                (Manga.provider == provider) & (Manga.external_id == external_id)
            )
        )
        manga = result.scalars().first()

        if not manga:
            return {
                "provider": provider,
                "external_id": external_id,
                "in_library": False,
                "manga_id": None,
                "library_item_id": None,
            }

        # Check if this manga is in user's library
        library_result = await db.execute(
            select(MangaUserLibrary).where(
                (MangaUserLibrary.user_id == current_user.id)
                & (MangaUserLibrary.manga_id == manga.id)
            )
        )
        library_item = library_result.scalars().first()

        return {
            "provider": provider,
            "external_id": external_id,
            "in_library": library_item is not None,
            "manga_id": str(manga.id),
            "library_item_id": str(library_item.id) if library_item else None,
        }
    except Exception as e:
        logger.error(f"Error checking external library status: {e}")
        return {
            "provider": provider,
            "external_id": external_id,
            "in_library": False,
            "manga_id": None,
            "library_item_id": None,
        }


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

        # Load relationships explicitly to avoid greenlet issues
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

        # Use the download_status field from the database, but verify file existence
        download_status = chapter.download_status
        if download_status == "downloaded" and chapter.file_path:
            import os

            # Verify the file actually exists
            if not os.path.exists(chapter.file_path):
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
                "download_error": chapter.download_error,
                "external_id": chapter.external_id,
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
        "library_item": {
            "id": str(library_item.id),
            "user_id": str(library_item.user_id),
            "manga_id": str(library_item.manga_id),
            "custom_title": library_item.custom_title,
            "custom_cover": library_item.custom_cover,
            "notes": library_item.notes,
            "is_favorite": library_item.is_favorite,
            "rating": library_item.rating,
            "is_downloaded": library_item.is_downloaded,
            "download_path": library_item.download_path,
            "created_at": library_item.created_at,
            "updated_at": library_item.updated_at,
            "manga": {
                "id": str(library_item.manga.id),
                "title": library_item.manga.title,
                "alternative_titles": library_item.manga.alternative_titles,
                "description": library_item.manga.description,
                "cover_image": library_item.manga.cover_image,
                "type": library_item.manga.type,
                "status": library_item.manga.status,
                "year": library_item.manga.year,
                "is_nsfw": library_item.manga.is_nsfw,
                "provider": library_item.manga.provider,
                "external_id": library_item.manga.external_id,
                "external_url": library_item.manga.external_url,
                "external_ids": library_item.manga.external_ids,
                "created_at": library_item.manga.created_at,
                "updated_at": library_item.manga.updated_at,
                "genres": [
                    {"id": str(g.id), "name": g.name, "description": g.description}
                    for g in library_item.manga.genres
                ],
                "authors": [
                    {
                        "id": str(a.id),
                        "name": a.name,
                        "alternative_names": a.alternative_names,
                        "biography": a.biography,
                    }
                    for a in library_item.manga.authors
                ],
            },
            "categories": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description,
                    "color": c.color,
                    "icon": c.icon,
                }
                for c in library_item.categories
            ],
        },
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
    provider: str = Query(...),
    external_id: str = Query(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
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
    try:
        # For now, return empty tasks list since background service needs fixing
        # TODO: Implement proper background task tracking
        return {"tasks": [], "count": 0}
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching download tasks: {e}")

        # Return empty tasks list on error
        return {"tasks": [], "count": 0}


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
    request: DownloadChapterRequest,
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

    # Get chapter if chapter_id is provided
    chapter = None
    if request.chapter_id:
        try:
            chapter = await db.get(Chapter, uuid.UUID(request.chapter_id))
            if chapter and chapter.manga_id != library_item.manga_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chapter not found",
                )
        except ValueError:
            # Invalid UUID format
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid chapter ID format",
            )

    # Check if provider exists
    from app.core.providers.registry import provider_registry

    provider_instance = provider_registry.get_provider(request.provider)
    if not provider_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{request.provider}' not found",
        )

    try:
        # Import download function
        from app.core.services.download import download_chapter

        # Create task ID
        chapter_id_for_task = chapter.id if chapter else "new"
        task_id = f"{current_user.id}_{library_item.manga_id}_{chapter_id_for_task}"

        # If no existing chapter, handle it in the download service
        if not chapter:
            # For new chapters from provider, let download service handle creation
            # Create a placeholder chapter ID for the task
            from uuid import uuid4

            chapter_id_for_download = uuid4()
        else:
            chapter_id_for_download = chapter.id

        # Add download task to background tasks
        background_tasks.add_task(
            download_chapter,
            manga_id=library_item.manga_id,
            chapter_id=chapter_id_for_download,
            provider_name=request.provider,
            external_manga_id=request.external_manga_id,
            external_chapter_id=request.external_chapter_id,
            db=db,
        )

        # Return task information
        return {
            "task_id": task_id,
            "manga_id": str(library_item.manga_id),
            "chapter_id": str(chapter_id_for_download),
            "user_id": str(current_user.id),
            "provider": request.provider,
            "status": "queued",
            "message": "Chapter download task has been queued",
        }

    except Exception as e:
        logger.error(f"Error starting chapter download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start chapter download: {str(e)}",
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_library_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get library statistics for the current user.
    """
    try:
        # Count total manga in user's library
        manga_result = await db.execute(
            select(func.count(MangaUserLibrary.manga_id)).where(
                MangaUserLibrary.user_id == current_user.id
            )
        )
        total_manga = manga_result.scalar() or 0

        # Count total chapters for manga in user's library
        chapters_result = await db.execute(
            select(func.count(Chapter.id))
            .join(Manga, Chapter.manga_id == Manga.id)
            .join(MangaUserLibrary, Manga.id == MangaUserLibrary.manga_id)
            .where(MangaUserLibrary.user_id == current_user.id)
        )
        total_chapters = chapters_result.scalar() or 0

        return {
            "total_manga": total_manga,
            "total_chapters": total_chapters,
        }
    except Exception as e:
        logger.error(f"Error fetching library stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch library statistics",
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


# Bulk Operations
@router.post("/bulk/mark-read", response_model=BulkOperationResponse)
async def bulk_mark_read(
    request: BulkMarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark multiple manga as read in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Update read status
                if not library_item.is_read:
                    library_item.is_read = True
                    updated_count += 1

            except Exception as e:
                logging.error(
                    f"Error marking library item {library_item_id} as read: {e}"
                )
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully marked {updated_count} manga as read",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk mark read operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark manga as read",
        )


@router.post("/bulk/mark-unread", response_model=BulkOperationResponse)
async def bulk_mark_unread(
    request: BulkMarkUnreadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark multiple manga as unread in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Update read status
                if library_item.is_read:
                    library_item.is_read = False
                    updated_count += 1

            except Exception as e:
                logging.error(
                    f"Error marking library item {library_item_id} as unread: {e}"
                )
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully marked {updated_count} manga as unread",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk mark unread operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark manga as unread",
        )


@router.post("/bulk/add-favorites", response_model=BulkOperationResponse)
async def bulk_add_favorites(
    request: BulkFavoritesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add multiple manga to favorites in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Update favorite status
                if not library_item.is_favorite:
                    library_item.is_favorite = True
                    updated_count += 1

            except Exception as e:
                logging.error(
                    f"Error adding library item {library_item_id} to favorites: {e}"
                )
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully added {updated_count} manga to favorites",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk add favorites operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add manga to favorites",
        )


@router.post("/bulk/remove-favorites", response_model=BulkOperationResponse)
async def bulk_remove_favorites(
    request: BulkFavoritesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove multiple manga from favorites in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Update favorite status
                if library_item.is_favorite:
                    library_item.is_favorite = False
                    updated_count += 1

            except Exception as e:
                logging.error(
                    f"Error removing library item {library_item_id} from favorites: {e}"
                )
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully removed {updated_count} manga from favorites",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk remove favorites operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove manga from favorites",
        )


@router.post("/bulk/delete", response_model=BulkOperationResponse)
async def bulk_delete(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Delete multiple manga from library in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Delete library item
                await db.delete(library_item)
                updated_count += 1

            except Exception as e:
                logging.error(f"Error deleting library item {library_item_id}: {e}")
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully deleted {updated_count} manga from library",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk delete operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete manga from library",
        )


@router.post("/bulk/update-tags", response_model=BulkOperationResponse)
async def bulk_update_tags(
    request: BulkUpdateTagsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update tags for multiple manga in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Update tags (assuming tags are stored as a JSON field or similar)
                # Note: This implementation assumes tags are stored in custom_tags
                if hasattr(library_item, "custom_tags"):
                    library_item.custom_tags = request.tags
                    updated_count += 1

            except Exception as e:
                logging.error(
                    f"Error updating tags for library item {library_item_id}: {e}"
                )
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully updated tags for {updated_count} manga",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk update tags operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tags",
        )


@router.post("/bulk/update-metadata", response_model=BulkOperationResponse)
async def bulk_update_metadata(
    request: BulkUpdateMetadataRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update metadata for multiple manga in bulk.
    """
    updated_count = 0
    failed_items = []

    try:
        for library_item_id in request.manga_ids:
            try:
                # Get library item
                library_item = await db.get(MangaUserLibrary, library_item_id)
                if not library_item or library_item.user_id != current_user.id:
                    failed_items.append(str(library_item_id))
                    continue

                # Update metadata fields
                for field, value in request.metadata.items():
                    if hasattr(library_item, field):
                        setattr(library_item, field, value)
                        updated_count += 1

            except Exception as e:
                logging.error(
                    f"Error updating metadata for library item {library_item_id}: {e}"
                )
                failed_items.append(str(library_item_id))

        await db.commit()

        return BulkOperationResponse(
            message=f"Successfully updated metadata for {updated_count} manga",
            updated_count=updated_count,
            total_requested=len(request.manga_ids),
            failed_items=failed_items,
        )

    except Exception as e:
        await db.rollback()
        logging.error(f"Error in bulk update metadata operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update metadata",
        )


@router.post("/read-external-chapter")
async def read_external_chapter(
    provider: str = Form(...),
    manga_id: str = Form(...),
    chapter_id: str = Form(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Read an external chapter without downloading it (temporary reading).
    """
    try:
        from app.core.providers.registry import provider_registry

        # Get the provider
        provider_instance = provider_registry.get_provider(provider)
        if not provider_instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider {provider} not found",
            )

        # Fetch chapter pages directly from provider
        pages = await provider_instance.get_pages(manga_id, chapter_id)

        if not pages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Chapter pages not found"
            )

        # Return temporary chapter data for the reader
        return {
            "id": f"temp_{chapter_id}",
            "title": f"Chapter from {provider}",
            "pages": pages,
            "is_temporary": True,
            "provider": provider,
            "external_manga_id": manga_id,
            "external_chapter_id": chapter_id,
        }

    except Exception as e:
        logging.error(f"Error reading external chapter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read external chapter",
        )
