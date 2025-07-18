"""
Chapter management endpoints.
"""

import os
import shutil
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.library import MangaUserLibrary
from app.models.manga import Chapter, Manga
from app.models.user import User
from app.schemas.manga import ChapterSummary

router = APIRouter()


def get_chapter_storage_path(manga_id: uuid.UUID, chapter_id: uuid.UUID) -> str:
    """Get the storage path for a chapter."""
    return os.path.join(
        settings.STORAGE_PATH, "manga", str(manga_id), "chapters", str(chapter_id)
    )


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a chapter and its associated files.
    """
    # Get the chapter
    chapter = await db.get(Chapter, uuid.UUID(chapter_id))
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    # Check if user has access to the manga
    result = await db.execute(
        select(MangaUserLibrary).where(
            (MangaUserLibrary.user_id == current_user.id)
            & (MangaUserLibrary.manga_id == chapter.manga_id)
        )
    )
    library_item = result.scalars().first()
    if not library_item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    try:
        # Delete chapter files
        chapter_path = get_chapter_storage_path(chapter.manga_id, chapter.id)
        if os.path.exists(chapter_path):
            shutil.rmtree(chapter_path)

        # Delete chapter from database
        await db.delete(chapter)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chapter: {str(e)}",
        )


@router.post("/{chapter_id}/redownload", response_model=ChapterSummary)
async def redownload_chapter(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Re-download a chapter (for downloaded chapters only).
    """
    # Get the chapter
    chapter = await db.get(Chapter, uuid.UUID(chapter_id))
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )

    # Check if user has access to the manga
    result = await db.execute(
        select(MangaUserLibrary).where(
            (MangaUserLibrary.user_id == current_user.id)
            & (MangaUserLibrary.manga_id == chapter.manga_id)
        )
    )
    library_item = result.scalars().first()
    if not library_item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Check if chapter is from import (can't re-download imported chapters)
    if chapter.source == "import":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot re-download imported chapters. Use the import function instead.",
        )

    # Get the manga to check for external source info
    manga = await db.get(Manga, chapter.manga_id)
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    if not manga.external_id or not manga.provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot re-download chapter: missing external source information",
        )

    try:
        # Delete existing chapter files
        chapter_path = get_chapter_storage_path(chapter.manga_id, chapter.id)
        if os.path.exists(chapter_path):
            shutil.rmtree(chapter_path)

        # Reset chapter status to trigger re-download
        chapter.download_status = "pending"
        chapter.download_error = None

        await db.commit()
        await db.refresh(chapter)

        # TODO: Trigger actual re-download through download service
        # This would typically involve queuing the chapter for download
        # For now, we just mark it as pending

        return chapter

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate re-download: {str(e)}",
        )
