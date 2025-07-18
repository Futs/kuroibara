import uuid
from unittest.mock import patch

import pytest

from app.core.services.background import (
    cancel_download_task,
    download_manga_task,
    get_download_task,
    get_user_download_tasks,
)


@pytest.mark.asyncio
@patch("app.core.services.background.download_manga")
async def test_download_manga_task(mock_download_manga):
    """Test download manga task."""
    # Mock download_manga function
    mock_download_manga.return_value = None

    # Create test data
    manga_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider_name = "test_provider"
    external_id = "test_external_id"

    # Call download_manga_task
    await download_manga_task(
        manga_id=manga_id,
        user_id=user_id,
        provider_name=provider_name,
        external_id=external_id,
    )

    # Check if download_manga was called with correct arguments
    mock_download_manga.assert_called_once_with(
        manga_id=manga_id,
        user_id=user_id,
        provider_name=provider_name,
        external_id=external_id,
        db=mock_download_manga.call_args[1]["db"],
    )

    # Check if task was created
    task_id = f"{user_id}_{manga_id}"
    task = get_download_task(task_id)

    assert task is not None
    assert task["manga_id"] == str(manga_id)
    assert task["user_id"] == str(user_id)
    assert task["provider"] == provider_name
    assert task["external_id"] == external_id
    assert task["status"] == "completed"
    assert task["progress"] == 100
    assert task["error"] is None


@pytest.mark.asyncio
@patch("app.core.services.background.download_manga")
async def test_download_manga_task_error(mock_download_manga):
    """Test download manga task with error."""
    # Mock download_manga function to raise an exception
    mock_download_manga.side_effect = Exception("Test error")

    # Create test data
    manga_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider_name = "test_provider"
    external_id = "test_external_id"

    # Call download_manga_task
    await download_manga_task(
        manga_id=manga_id,
        user_id=user_id,
        provider_name=provider_name,
        external_id=external_id,
    )

    # Check if task was created with error
    task_id = f"{user_id}_{manga_id}"
    task = get_download_task(task_id)

    assert task is not None
    assert task["manga_id"] == str(manga_id)
    assert task["user_id"] == str(user_id)
    assert task["provider"] == provider_name
    assert task["external_id"] == external_id
    assert task["status"] == "failed"
    assert task["error"] == "Test error"


def test_get_user_download_tasks():
    """Test get_user_download_tasks."""
    # Create test data
    user_id = uuid.uuid4()
    manga_id1 = uuid.uuid4()
    manga_id2 = uuid.uuid4()

    # Create tasks
    task_id1 = f"{user_id}_{manga_id1}"
    task_id2 = f"{user_id}_{manga_id2}"

    # Add tasks to download_tasks
    from app.core.services.background import download_tasks

    download_tasks[task_id1] = {
        "manga_id": str(manga_id1),
        "user_id": str(user_id),
        "provider": "test_provider",
        "external_id": "test_external_id_1",
        "status": "completed",
        "progress": 100,
        "error": None,
    }
    download_tasks[task_id2] = {
        "manga_id": str(manga_id2),
        "user_id": str(user_id),
        "provider": "test_provider",
        "external_id": "test_external_id_2",
        "status": "running",
        "progress": 50,
        "error": None,
    }

    # Get user tasks
    user_tasks = get_user_download_tasks(user_id)

    # Check if tasks were returned
    assert len(user_tasks) == 2
    assert task_id1 in user_tasks
    assert task_id2 in user_tasks
    assert user_tasks[task_id1]["manga_id"] == str(manga_id1)
    assert user_tasks[task_id2]["manga_id"] == str(manga_id2)


def test_cancel_download_task():
    """Test cancel_download_task."""
    # Create test data
    user_id = uuid.uuid4()
    manga_id = uuid.uuid4()

    # Create task
    task_id = f"{user_id}_{manga_id}"

    # Add task to download_tasks
    from app.core.services.background import download_tasks

    download_tasks[task_id] = {
        "manga_id": str(manga_id),
        "user_id": str(user_id),
        "provider": "test_provider",
        "external_id": "test_external_id",
        "status": "running",
        "progress": 50,
        "error": None,
    }

    # Cancel task
    result = cancel_download_task(task_id)

    # Check if task was cancelled
    assert result is True
    assert download_tasks[task_id]["status"] == "cancelled"

    # Try to cancel non-existent task
    result = cancel_download_task("non_existent_task")

    # Check if result is False
    assert result is False
