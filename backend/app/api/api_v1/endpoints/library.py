from typing import Any, List, Optional, Dict
import uuid
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.manga import Manga, Chapter
from app.models.library import MangaUserLibrary, Category, ReadingProgress, Bookmark
from app.schemas.library import (
    MangaUserLibrary as MangaUserLibrarySchema,
    MangaUserLibraryCreate,
    MangaUserLibraryUpdate,
    ReadingProgress as ReadingProgressSchema,
    ReadingProgressCreate,
    ReadingProgressUpdate,
    Bookmark as BookmarkSchema,
    BookmarkCreate,
    BookmarkUpdate,
)

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
    query = select(MangaUserLibrary).where(MangaUserLibrary.user_id == current_user.id)

    # Filter by category
    if category_id:
        query = query.join(MangaUserLibrary.categories).where(Category.id == uuid.UUID(category_id))

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
            (MangaUserLibrary.user_id == current_user.id) &
            (MangaUserLibrary.manga_id == library_item.manga_id)
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

    # Add categories
    if library_item.category_ids:
        for category_id in library_item.category_ids:
            category = await db.get(Category, category_id)
            if category and (category.is_default or category.user_id == current_user.id):
                library_item_obj.categories.append(category)

    db.add(library_item_obj)
    await db.commit()
    await db.refresh(library_item_obj)

    return library_item_obj


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
    update_data = library_item_update.model_dump(exclude={"category_ids"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(library_item, field, value)

    # Update categories
    if library_item_update.category_ids is not None:
        # Clear existing categories
        library_item.categories = []

        # Add new categories
        for category_id in library_item_update.category_ids:
            category = await db.get(Category, category_id)
            if category and (category.is_default or category.user_id == current_user.id):
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
    from app.core.services.background import download_manga_task
    from app.core.providers.registry import provider_registry

    # Check if provider exists
    if not provider_registry.get_provider(provider):
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
        "message": "Download task has been queued"
    }


@router.post("/progress", response_model=ReadingProgressSchema)
async def update_reading_progress(
    progress_data: ReadingProgressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update reading progress for a manga chapter.
    """
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
            (ReadingProgress.user_id == current_user.id) &
            (ReadingProgress.manga_id == progress_data.manga_id) &
            (ReadingProgress.chapter_id == progress_data.chapter_id)
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

    return {
        "tasks": tasks,
        "count": len(tasks)
    }


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
    from app.core.services.background import get_download_task, cancel_download_task as cancel_task

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
