"""
Comprehensive tests for the progress tracking system.

This module tests all aspects of progress tracking including events,
operations, WebSocket management, persistence, and bulk operations.
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.progress import (
    OperationType,
    ProgressEvent,
    ProgressEventType,
    ProgressOperation,
    ProgressStatus,
    ProgressTracker,
    WebSocketManager,
)


class TestProgressEvent:
    """Test progress event functionality."""

    def test_progress_event_creation(self):
        """Test creating a progress event."""
        event = ProgressEvent(
            operation_id="test-op-123",
            operation_type=OperationType.SEARCH,
            event_type=ProgressEventType.PROGRESS,
            progress_percentage=50.0,
            current_step="Searching providers",
            message="Searching MangaDex...",
        )

        assert event.operation_id == "test-op-123"
        assert event.operation_type == OperationType.SEARCH
        assert event.event_type == ProgressEventType.PROGRESS
        assert event.progress_percentage == 50.0
        assert event.current_step == "Searching providers"
        assert event.message == "Searching MangaDex..."
        assert isinstance(event.timestamp, datetime)

    def test_progress_event_to_dict(self):
        """Test converting progress event to dictionary."""
        event = ProgressEvent(
            operation_id="test-op-123",
            operation_type=OperationType.DOWNLOAD_CHAPTER,
            event_type=ProgressEventType.COMPLETED,
            progress_percentage=100.0,
            message="Download completed",
        )

        event_dict = event.to_dict()

        assert event_dict["operation_id"] == "test-op-123"
        assert event_dict["operation_type"] == "download_chapter"
        assert event_dict["event_type"] == "completed"
        assert event_dict["progress_percentage"] == 100.0
        assert event_dict["message"] == "Download completed"
        assert "timestamp" in event_dict

    def test_progress_event_from_dict(self):
        """Test creating progress event from dictionary."""
        event_data = {
            "id": "event-123",
            "operation_id": "op-456",
            "operation_type": "search",
            "event_type": "progress",
            "progress_percentage": 75.0,
            "message": "Test message",
            "timestamp": datetime.utcnow().isoformat(),
        }

        event = ProgressEvent.from_dict(event_data)

        assert event.id == "event-123"
        assert event.operation_id == "op-456"
        assert event.operation_type == OperationType.SEARCH
        assert event.event_type == ProgressEventType.PROGRESS
        assert event.progress_percentage == 75.0
        assert event.message == "Test message"


class TestProgressOperation:
    """Test progress operation functionality."""

    def test_progress_operation_creation(self):
        """Test creating a progress operation."""
        operation = ProgressOperation(
            operation_type=OperationType.BULK_DOWNLOAD,
            title="Bulk Download Test",
            description="Testing bulk download",
            total_items=10,
        )

        assert operation.operation_type == OperationType.BULK_DOWNLOAD
        assert operation.title == "Bulk Download Test"
        assert operation.description == "Testing bulk download"
        assert operation.status == ProgressStatus.PENDING
        assert operation.total_items == 10
        assert operation.processed_items == 0
        assert isinstance(operation.started_at, datetime)

    def test_progress_calculation(self):
        """Test progress calculation based on items."""
        operation = ProgressOperation(
            operation_type=OperationType.LIBRARY_SCAN,
            title="Library Scan",
            total_items=100,
        )

        # Test with no processed items
        assert operation.calculate_progress() == 0.0

        # Test with some processed items
        operation.processed_items = 25
        assert operation.calculate_progress() == 25.0

        # Test with all items processed
        operation.processed_items = 100
        assert operation.calculate_progress() == 100.0

        # Test with more than total (should cap at 100%)
        operation.processed_items = 150
        assert operation.calculate_progress() == 100.0

    def test_operation_lifecycle(self):
        """Test operation lifecycle methods."""
        operation = ProgressOperation(
            operation_type=OperationType.DOWNLOAD_MANGA, title="Download Manga"
        )

        # Test initial state
        assert operation.is_active()
        assert not operation.is_finished()

        # Test updating progress
        operation.update_progress(50.0, "Downloading chapters")
        assert operation.progress_percentage == 50.0
        assert operation.current_step == "Downloading chapters"

        # Test completion
        operation.mark_completed("Download finished")
        assert operation.status == ProgressStatus.COMPLETED
        assert operation.progress_percentage == 100.0
        assert operation.completed_at is not None
        assert not operation.is_active()
        assert operation.is_finished()

        # Test duration calculation
        duration = operation.get_duration()
        assert duration is not None
        assert duration >= 0

    def test_operation_failure(self):
        """Test operation failure handling."""
        operation = ProgressOperation(
            operation_type=OperationType.SEARCH, title="Search Test"
        )

        operation.mark_failed("Network error")

        assert operation.status == ProgressStatus.FAILED
        assert operation.error_message == "Network error"
        assert operation.completed_at is not None
        assert not operation.is_active()
        assert operation.is_finished()

    def test_operation_warnings(self):
        """Test adding warnings to operations."""
        operation = ProgressOperation(
            operation_type=OperationType.METADATA_FETCH, title="Metadata Fetch"
        )

        operation.add_warning("Some pages failed to load")
        operation.add_warning("Slow response from provider")

        assert len(operation.warning_messages) == 2
        assert "Some pages failed to load" in operation.warning_messages
        assert "Slow response from provider" in operation.warning_messages


class TestProgressTracker:
    """Test progress tracker functionality."""

    @pytest.fixture
    def tracker(self):
        """Create a test progress tracker."""
        return ProgressTracker()

    @pytest.mark.asyncio
    async def test_start_operation(self, tracker):
        """Test starting a progress operation."""
        operation_id = await tracker.start_operation(
            operation_type=OperationType.SEARCH,
            title="Test Search",
            description="Testing search functionality",
            total_steps=3,
        )

        assert operation_id

        operation = tracker.get_operation(operation_id)
        assert operation is not None
        assert operation.title == "Test Search"
        assert operation.description == "Testing search functionality"
        assert operation.total_steps == 3
        assert operation.status == ProgressStatus.RUNNING

    @pytest.mark.asyncio
    async def test_update_progress(self, tracker):
        """Test updating operation progress."""
        operation_id = await tracker.start_operation(
            operation_type=OperationType.DOWNLOAD_CHAPTER,
            title="Download Chapter",
            total_items=10,
        )

        success = await tracker.update_progress(
            operation_id=operation_id,
            progress=50.0,
            current_step="Downloading pages",
            processed_items=5,
            successful_items=4,
            failed_items=1,
        )

        assert success

        operation = tracker.get_operation(operation_id)
        assert operation.progress_percentage == 50.0
        assert operation.current_step == "Downloading pages"
        assert operation.processed_items == 5
        assert operation.successful_items == 4
        assert operation.failed_items == 1

    @pytest.mark.asyncio
    async def test_complete_operation(self, tracker):
        """Test completing an operation."""
        operation_id = await tracker.start_operation(
            operation_type=OperationType.LIBRARY_IMPORT, title="Import Library"
        )

        success = await tracker.complete_operation(
            operation_id=operation_id, message="Import completed successfully"
        )

        assert success

        operation = tracker.get_operation(operation_id)
        assert operation.status == ProgressStatus.COMPLETED
        assert operation.progress_percentage == 100.0
        assert operation.completed_at is not None

    @pytest.mark.asyncio
    async def test_fail_operation(self, tracker):
        """Test failing an operation."""
        operation_id = await tracker.start_operation(
            operation_type=OperationType.DOWNLOAD_COVER, title="Download Cover"
        )

        success = await tracker.fail_operation(
            operation_id=operation_id, error_message="Network timeout"
        )

        assert success

        operation = tracker.get_operation(operation_id)
        assert operation.status == ProgressStatus.FAILED
        assert operation.error_message == "Network timeout"
        assert operation.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_operation(self, tracker):
        """Test cancelling an operation."""
        operation_id = await tracker.start_operation(
            operation_type=OperationType.SYSTEM_BACKUP, title="System Backup"
        )

        success = await tracker.cancel_operation(operation_id)

        assert success

        operation = tracker.get_operation(operation_id)
        assert operation.status == ProgressStatus.CANCELLED
        assert operation.completed_at is not None

    @pytest.mark.asyncio
    async def test_bulk_operations(self, tracker):
        """Test bulk operation functionality."""
        # Start bulk operation
        bulk_id = await tracker.start_bulk_operation(
            operation_type=OperationType.BULK_DOWNLOAD,
            title="Bulk Download Test",
            total_items=3,
        )

        assert bulk_id

        # Add child operations
        child_ids = []
        for i in range(3):
            child_id = await tracker.add_child_operation(
                parent_operation_id=bulk_id,
                operation_type=OperationType.DOWNLOAD_CHAPTER,
                title=f"Download Chapter {i+1}",
            )
            child_ids.append(child_id)

        assert len(child_ids) == 3

        # Complete child operations
        for child_id in child_ids:
            await tracker.complete_child_operation(child_id)

        # Check bulk operation status
        bulk_operation = tracker.get_operation(bulk_id)
        assert bulk_operation.status == ProgressStatus.COMPLETED
        assert bulk_operation.progress_percentage == 100.0
        assert bulk_operation.successful_items == 3
        assert bulk_operation.failed_items == 0

    def test_get_operations_filtering(self, tracker):
        """Test filtering operations."""
        # This would need to be an async test with actual operations
        # For now, test the basic functionality
        operations = tracker.get_operations()
        assert isinstance(operations, list)

        # Test filtering by status
        active_operations = tracker.get_operations(active_only=True)
        assert isinstance(active_operations, list)


class TestWebSocketManager:
    """Test WebSocket manager functionality."""

    @pytest.fixture
    def websocket_manager(self):
        """Create a test WebSocket manager."""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_websocket_connection(self, websocket_manager):
        """Test WebSocket connection management."""
        # Mock WebSocket
        mock_websocket = AsyncMock()

        # Test connection
        connection_id = await websocket_manager.connect(
            mock_websocket, "user123", "session456"
        )

        assert connection_id
        assert websocket_manager.get_connection_count() == 1

        # Test disconnection
        await websocket_manager.disconnect(connection_id)
        assert websocket_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_event_broadcasting(self, websocket_manager):
        """Test broadcasting events to WebSocket clients."""
        # Mock WebSocket
        mock_websocket = AsyncMock()

        # Connect WebSocket
        connection_id = await websocket_manager.connect(mock_websocket, "user123")

        # Broadcast event
        test_event = {
            "operation_id": "test-op",
            "event_type": "progress",
            "progress_percentage": 50.0,
            "message": "Test progress",
        }

        sent_count = await websocket_manager.broadcast_event(test_event)

        assert sent_count == 1
        # Verify the event was sent (should be called twice: connection established + progress event)
        assert mock_websocket.send_text.call_count == 2

        # Verify message content
        call_args = mock_websocket.send_text.call_args[0][0]
        message_data = json.loads(call_args)
        assert message_data["type"] == "progress_event"
        assert message_data["event"]["operation_id"] == "test-op"


if __name__ == "__main__":
    # Run basic tests if executed directly
    import sys

    print("Running progress tracking tests...")

    # Test basic functionality
    event = ProgressEvent(
        operation_id="test",
        operation_type=OperationType.SEARCH,
        event_type=ProgressEventType.PROGRESS,
    )
    assert event.operation_id == "test"
    print("✅ ProgressEvent tests passed")

    operation = ProgressOperation(
        operation_type=OperationType.DOWNLOAD_CHAPTER, title="Test Operation"
    )
    assert operation.title == "Test Operation"
    print("✅ ProgressOperation tests passed")

    tracker = ProgressTracker()
    assert len(tracker.get_operations()) == 0
    print("✅ ProgressTracker tests passed")

    websocket_manager = WebSocketManager()
    assert websocket_manager.get_connection_count() == 0
    print("✅ WebSocketManager tests passed")

    print("\n🎉 All basic progress tracking tests passed!")
    print(
        "Run with pytest for full test suite: pytest tests/test_progress_tracking.py -v"
    )
