import asyncio
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.download import download_manga
from app.db.session import AsyncSessionLocal
from app.models.library import MangaUserLibrary
from app.models.manga import Manga

logger = logging.getLogger(__name__)


# Dictionary to store download tasks
download_tasks: Dict[str, Dict[str, Any]] = {}


async def download_manga_task(
    manga_id: UUID,
    user_id: UUID,
    provider_name: str,
    external_id: str,
) -> None:
    """
    Background task to download a manga.

    Args:
        manga_id: The ID of the manga
        user_id: The ID of the user
        provider_name: The name of the provider
        external_id: The external ID of the manga
    """
    # Create a unique task ID
    task_id = f"{user_id}_{manga_id}"

    # Update task status
    download_tasks[task_id] = {
        "manga_id": str(manga_id),
        "user_id": str(user_id),
        "provider": provider_name,
        "external_id": external_id,
        "status": "running",
        "progress": 0,
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


def get_download_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a download task by ID.

    Args:
        task_id: The ID of the task

    Returns:
        The task or None if not found
    """
    return download_tasks.get(task_id)


def get_user_download_tasks(user_id: UUID) -> Dict[str, Dict[str, Any]]:
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
