import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.services.download import download_manga
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


# Dictionary to store download tasks
download_tasks: Dict[str, Dict[str, Any]] = {}


async def download_manga_task(
    manga_id,
    user_id,
    provider_name: str,
    external_id: str,
    task_id: str = None,
) -> None:
    """
    Background task to download a manga.

    Args:
        manga_id: The ID of the manga
        user_id: The ID of the user
        provider_name: The name of the provider
        external_id: The external ID of the manga
    """
    # Ensure IDs are UUIDs
    if isinstance(manga_id, str):
        manga_id = UUID(manga_id)
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    # Use provided task ID or create a unique one
    if task_id is None:
        task_id = f"{user_id}_{manga_id}_{int(time.time())}"

    # Get manga details for better task info
    manga_title = "Unknown Manga"
    total_chapters = 0

    try:
        # Create a new database session to get manga details
        async with AsyncSessionLocal() as db:
            from app.models.manga import Manga

            manga = await db.get(Manga, manga_id)
            if manga:
                manga_title = manga.title
                # Get chapter count if available
                if hasattr(manga, "chapters") and manga.chapters:
                    total_chapters = len(manga.chapters)
    except Exception as e:
        logger.warning(f"Could not get manga details for task: {e}")

    # Update task status
    download_tasks[task_id] = {
        "task_id": task_id,
        "manga_id": str(manga_id),
        "manga_title": manga_title,
        "user_id": str(user_id),
        "provider": provider_name,
        "external_id": external_id,
        "type": "bulk",
        "status": "downloading",
        "progress": 0,
        "total_chapters": total_chapters,
        "completed_chapters": 0,
        "started_at": datetime.now().isoformat(),
        "error": None,
    }

    try:
        # Create a new database session
        async with AsyncSessionLocal() as db:
            # Download manga
            await download_manga(
                manga_id=manga_id,
                user_id=user_id,
                provider_name=provider_name,
                external_id=external_id,
                db=db,
            )

            # Update task status
            download_tasks[task_id]["status"] = "completed"
            download_tasks[task_id]["progress"] = 100
    except Exception as e:
        # Log error
        logger.error(f"Error downloading manga: {e}")

        # Update task status
        download_tasks[task_id]["status"] = "failed"
        download_tasks[task_id]["error"] = str(e)


async def download_chapter_task(
    manga_id,
    chapter_id,
    provider_name: str,
    external_manga_id: str,
    external_chapter_id: str,
    user_id,
) -> str:
    """
    Background task to download a single chapter.

    Args:
        manga_id: The ID of the manga
        chapter_id: The ID of the chapter
        provider_name: The name of the provider
        external_manga_id: The external ID of the manga
        external_chapter_id: The external ID of the chapter
        user_id: The ID of the user

    Returns:
        The task ID
    """
    # Ensure IDs are UUIDs
    if isinstance(manga_id, str):
        manga_id = UUID(manga_id)
    if isinstance(chapter_id, str):
        chapter_id = UUID(chapter_id)
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    # Create a unique task ID
    task_id = f"{user_id}_{manga_id}_{chapter_id}_{int(time.time())}"

    # Get manga and chapter details for better task info
    manga_title = "Unknown Manga"
    chapter_number = "Unknown"
    chapter_title = ""

    try:
        # Create a new database session to get details
        async with AsyncSessionLocal() as db:
            from app.models.chapter import Chapter
            from app.models.manga import Manga

            manga = await db.get(Manga, manga_id)
            if manga:
                manga_title = manga.title

            chapter = await db.get(Chapter, chapter_id)
            if chapter:
                chapter_number = str(chapter.number)
                chapter_title = chapter.title or ""
    except Exception as e:
        logger.warning(f"Could not get chapter details for task: {e}")

    # Update task status
    download_tasks[task_id] = {
        "task_id": task_id,
        "manga_id": str(manga_id),
        "manga_title": manga_title,
        "chapter_id": str(chapter_id),
        "chapter_number": chapter_number,
        "chapter_title": chapter_title,
        "user_id": str(user_id),
        "provider": provider_name,
        "external_manga_id": external_manga_id,
        "external_chapter_id": external_chapter_id,
        "type": "chapter",
        "status": "downloading",
        "progress": 0,
        "total_pages": 0,
        "downloaded_pages": 0,
        "started_at": datetime.now().isoformat(),
        "error": None,
    }

    try:
        # Create a new database session
        async with AsyncSessionLocal() as db:
            # Download chapter
            from app.core.services.download import download_chapter

            await download_chapter(
                manga_id=manga_id,
                chapter_id=chapter_id,
                provider_name=provider_name,
                external_manga_id=external_manga_id,
                external_chapter_id=external_chapter_id,
                db=db,
            )

            # Update task status
            download_tasks[task_id]["status"] = "completed"
            download_tasks[task_id]["progress"] = 100
    except Exception as e:
        # Log error
        logger.error(f"Error downloading chapter: {e}")

        # Update task status
        download_tasks[task_id]["status"] = "failed"
        download_tasks[task_id]["error"] = str(e)

    return task_id


def get_download_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a download task by ID.

    Args:
        task_id: The ID of the task

    Returns:
        The task or None if not found
    """
    return download_tasks.get(task_id)


def get_user_download_tasks(user_id) -> Dict[str, Dict[str, Any]]:
    """
    Get all download tasks for a user.

    Args:
        user_id: The ID of the user

    Returns:
        A dictionary of tasks
    """
    user_tasks = {}
    for task_id, task in download_tasks.items():
        if task["user_id"] == str(user_id):
            user_tasks[task_id] = task

    return user_tasks


def cancel_download_task(task_id: str) -> bool:
    """
    Cancel a download task.

    Args:
        task_id: The ID of the task

    Returns:
        True if the task was cancelled, False otherwise
    """
    if task_id in download_tasks:
        # Update task status
        download_tasks[task_id]["status"] = "cancelled"
        return True

    return False


def update_download_task_status(task_id: str, status: str) -> bool:
    """
    Update the status of a download task.

    Args:
        task_id: The ID of the task
        status: The new status

    Returns:
        True if the task was updated, False otherwise
    """
    if task_id in download_tasks:
        download_tasks[task_id]["status"] = status
        return True

    return False
