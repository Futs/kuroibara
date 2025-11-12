"""
Progress tracker service for managing operations and events.

This module provides the core progress tracking functionality including
operation management, event emission, and ETA calculation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .events import (
    OperationType,
    ProgressEvent,
    ProgressEventType,
    ProgressOperation,
    ProgressStatus,
)

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Central service for tracking progress of operations.

    Features:
    - Operation lifecycle management
    - Real-time event emission
    - ETA calculation
    - Hierarchical operations
    - Cancellation support
    """

    def __init__(self):
        self._operations: Dict[str, ProgressOperation] = {}
        self._event_handlers: List[Callable[[ProgressEvent], None]] = []
        self._websocket_handlers: List[Callable[[Dict[str, Any]], None]] = []
        self._cleanup_interval = 3600  # 1 hour
        self._max_completed_operations = 100
        self._cleanup_task: Optional[asyncio.Task] = None
        self._persistence_service = None
        self._websocket_manager = None

        logger.info("ProgressTracker initialized")

    def set_persistence_service(self, persistence_service) -> None:
        """Set the persistence service for saving operations and events."""
        self._persistence_service = persistence_service
        logger.debug("Persistence service set")

    def set_websocket_manager(self, websocket_manager) -> None:
        """Set the WebSocket manager for real-time updates."""
        self._websocket_manager = websocket_manager
        logger.debug("WebSocket manager set")

    def add_event_handler(self, handler: Callable[[ProgressEvent], None]) -> None:
        """Add an event handler for progress events."""
        self._event_handlers.append(handler)
        logger.debug(f"Added event handler: {handler.__name__}")

    def add_websocket_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Add a WebSocket handler for real-time updates."""
        self._websocket_handlers.append(handler)
        logger.debug(f"Added WebSocket handler: {handler.__name__}")

    def remove_event_handler(self, handler: Callable[[ProgressEvent], None]) -> None:
        """Remove an event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
            logger.debug(f"Removed event handler: {handler.__name__}")

    async def start_operation(
        self,
        operation_type: OperationType,
        title: str,
        description: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_operation_id: Optional[str] = None,
        total_steps: Optional[int] = None,
        total_items: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_cancellable: bool = True,
    ) -> str:
        """
        Start a new progress operation.

        Returns:
            Operation ID
        """
        operation_id = str(uuid4())

        operation = ProgressOperation(
            id=operation_id,
            operation_type=operation_type,
            title=title,
            description=description,
            status=ProgressStatus.RUNNING,
            user_id=user_id,
            session_id=session_id,
            parent_operation_id=parent_operation_id,
            total_steps=total_steps,
            total_items=total_items,
            metadata=metadata or {},
            is_cancellable=is_cancellable,
        )

        self._operations[operation_id] = operation

        # Add to parent's children if applicable
        if parent_operation_id and parent_operation_id in self._operations:
            self._operations[parent_operation_id].child_operations.append(operation_id)

        # Emit started event
        await self._emit_event(
            ProgressEvent(
                operation_id=operation_id,
                operation_type=operation_type,
                event_type=ProgressEventType.STARTED,
                message=f"Started: {title}",
                user_id=user_id,
                session_id=session_id,
                metadata={"operation": operation.to_dict()},
            )
        )

        logger.info(f"Started operation {operation_id}: {title}")
        return operation_id

    async def update_progress(
        self,
        operation_id: str,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        current_step_number: Optional[int] = None,
        message: Optional[str] = None,
        processed_items: Optional[int] = None,
        successful_items: Optional[int] = None,
        failed_items: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update progress for an operation.

        Returns:
            True if operation was found and updated
        """
        operation = self._operations.get(operation_id)
        if not operation:
            logger.warning(f"Operation {operation_id} not found for progress update")
            return False

        # Update operation
        if progress is not None:
            operation.update_progress(
                progress, current_step, current_step_number, message
            )

        if processed_items is not None:
            operation.processed_items = processed_items
        if successful_items is not None:
            operation.successful_items = successful_items
        if failed_items is not None:
            operation.failed_items = failed_items

        if metadata:
            operation.metadata.update(metadata)

        # Calculate actual progress if we have item counts
        actual_progress = operation.calculate_progress()

        # Emit progress event
        await self._emit_event(
            ProgressEvent(
                operation_id=operation_id,
                operation_type=operation.operation_type,
                event_type=ProgressEventType.PROGRESS,
                progress_percentage=actual_progress,
                current_step=operation.current_step,
                total_steps=operation.total_steps,
                current_step_number=operation.current_step_number,
                message=message or f"Progress: {actual_progress:.1f}%",
                estimated_completion=operation.estimated_completion,
                user_id=operation.user_id,
                session_id=operation.session_id,
                metadata={
                    "processed_items": operation.processed_items,
                    "total_items": operation.total_items,
                    "successful_items": operation.successful_items,
                    "failed_items": operation.failed_items,
                    **(metadata or {}),
                },
            )
        )

        return True

    async def complete_operation(
        self,
        operation_id: str,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark an operation as completed.

        Returns:
            True if operation was found and completed
        """
        operation = self._operations.get(operation_id)
        if not operation:
            logger.warning(f"Operation {operation_id} not found for completion")
            return False

        operation.mark_completed(message)

        if metadata:
            operation.metadata.update(metadata)

        # Emit completed event
        await self._emit_event(
            ProgressEvent(
                operation_id=operation_id,
                operation_type=operation.operation_type,
                event_type=ProgressEventType.COMPLETED,
                progress_percentage=100.0,
                message=message or f"Completed: {operation.title}",
                user_id=operation.user_id,
                session_id=operation.session_id,
                metadata={
                    "duration": operation.get_duration(),
                    "successful_items": operation.successful_items,
                    "failed_items": operation.failed_items,
                    **(metadata or {}),
                },
            )
        )

        logger.info(f"Completed operation {operation_id}: {operation.title}")
        return True

    async def fail_operation(
        self,
        operation_id: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark an operation as failed.

        Returns:
            True if operation was found and marked as failed
        """
        operation = self._operations.get(operation_id)
        if not operation:
            logger.warning(f"Operation {operation_id} not found for failure")
            return False

        operation.mark_failed(error_message)

        if metadata:
            operation.metadata.update(metadata)

        # Emit failed event
        await self._emit_event(
            ProgressEvent(
                operation_id=operation_id,
                operation_type=operation.operation_type,
                event_type=ProgressEventType.FAILED,
                error_message=error_message,
                message=f"Failed: {operation.title}",
                user_id=operation.user_id,
                session_id=operation.session_id,
                metadata={"duration": operation.get_duration(), **(metadata or {})},
            )
        )

        logger.error(f"Failed operation {operation_id}: {error_message}")
        return True

    async def cancel_operation(
        self, operation_id: str, message: Optional[str] = None
    ) -> bool:
        """
        Cancel an operation.

        Returns:
            True if operation was found and cancelled
        """
        operation = self._operations.get(operation_id)
        if not operation:
            logger.warning(f"Operation {operation_id} not found for cancellation")
            return False

        if not operation.is_cancellable:
            logger.warning(f"Operation {operation_id} is not cancellable")
            return False

        operation.mark_cancelled()

        # Cancel child operations
        for child_id in operation.child_operations:
            await self.cancel_operation(child_id, "Parent operation cancelled")

        # Emit cancelled event
        await self._emit_event(
            ProgressEvent(
                operation_id=operation_id,
                operation_type=operation.operation_type,
                event_type=ProgressEventType.CANCELLED,
                message=message or f"Cancelled: {operation.title}",
                user_id=operation.user_id,
                session_id=operation.session_id,
                metadata={"duration": operation.get_duration()},
            )
        )

        logger.info(f"Cancelled operation {operation_id}: {operation.title}")
        return True

    async def add_warning(
        self,
        operation_id: str,
        warning_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a warning to an operation.

        Returns:
            True if operation was found and warning added
        """
        operation = self._operations.get(operation_id)
        if not operation:
            return False

        operation.add_warning(warning_message)

        # Emit warning event
        await self._emit_event(
            ProgressEvent(
                operation_id=operation_id,
                operation_type=operation.operation_type,
                event_type=ProgressEventType.WARNING,
                warning_message=warning_message,
                message=f"Warning: {warning_message}",
                user_id=operation.user_id,
                session_id=operation.session_id,
                metadata=metadata or {},
            )
        )

        return True

    def get_operation(self, operation_id: str) -> Optional[ProgressOperation]:
        """Get an operation by ID."""
        return self._operations.get(operation_id)

    def get_operations(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        operation_type: Optional[OperationType] = None,
        status: Optional[ProgressStatus] = None,
        active_only: bool = False,
    ) -> List[ProgressOperation]:
        """Get operations with optional filtering."""
        operations = list(self._operations.values())

        if user_id:
            operations = [op for op in operations if op.user_id == user_id]

        if session_id:
            operations = [op for op in operations if op.session_id == session_id]

        if operation_type:
            operations = [
                op for op in operations if op.operation_type == operation_type
            ]

        if status:
            operations = [op for op in operations if op.status == status]

        if active_only:
            operations = [op for op in operations if op.is_active()]

        # Sort by last update (most recent first)
        operations.sort(key=lambda op: op.last_update, reverse=True)

        return operations

    async def _emit_event(self, event: ProgressEvent) -> None:
        """Emit a progress event to all handlers."""
        # Save event to database if persistence is available
        if self._persistence_service:
            try:
                await self._persistence_service.save_event(event)
            except Exception as e:
                logger.error(f"Error saving event to database: {e}")

        # Save operation to database if persistence is available
        if self._persistence_service and event.operation_id in self._operations:
            try:
                operation = self._operations[event.operation_id]
                await self._persistence_service.save_operation(operation)
            except Exception as e:
                logger.error(f"Error saving operation to database: {e}")

        # Send to WebSocket clients
        if self._websocket_manager:
            try:
                event_dict = event.to_dict()
                await self._websocket_manager.broadcast_event(event_dict)
            except Exception as e:
                logger.error(f"Error broadcasting event via WebSocket: {e}")

        # Call event handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}")

        # Call WebSocket handlers (legacy support)
        event_dict = event.to_dict()
        for handler in self._websocket_handlers:
            try:
                handler(event_dict)
            except Exception as e:
                logger.error(f"Error in WebSocket handler {handler.__name__}: {e}")

    async def start_cleanup_task(self) -> None:
        """Start the cleanup task for old operations."""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Started progress tracker cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop the cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped progress tracker cleanup task")

    async def _cleanup_loop(self) -> None:
        """Cleanup loop for removing old completed operations."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_old_operations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_old_operations(self) -> None:
        """Remove old completed operations to prevent memory bloat."""
        completed_operations = [
            op for op in self._operations.values() if op.is_finished()
        ]

        if len(completed_operations) <= self._max_completed_operations:
            return

        # Sort by completion time (oldest first)
        completed_operations.sort(key=lambda op: op.completed_at or datetime.min)

        # Remove oldest operations
        to_remove = len(completed_operations) - self._max_completed_operations
        for i in range(to_remove):
            operation = completed_operations[i]
            del self._operations[operation.id]
            logger.debug(f"Cleaned up old operation: {operation.id}")

        logger.info(f"Cleaned up {to_remove} old operations")

    async def start_bulk_operation(
        self,
        operation_type: OperationType,
        title: str,
        description: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        total_items: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start a bulk operation that will contain multiple child operations.

        Returns:
            Bulk operation ID
        """
        bulk_operation_id = await self.start_operation(
            operation_type=operation_type,
            title=title,
            description=description,
            user_id=user_id,
            session_id=session_id,
            total_items=total_items,
            metadata={"is_bulk_operation": True, **(metadata or {})},
        )

        logger.info(f"Started bulk operation {bulk_operation_id}: {title}")
        return bulk_operation_id

    async def add_child_operation(
        self,
        parent_operation_id: str,
        operation_type: OperationType,
        title: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a child operation to a bulk operation.

        Returns:
            Child operation ID
        """
        parent_operation = self.get_operation(parent_operation_id)
        if not parent_operation:
            logger.warning(f"Parent operation {parent_operation_id} not found")
            return ""

        child_operation_id = await self.start_operation(
            operation_type=operation_type,
            title=title,
            description=description,
            user_id=parent_operation.user_id,
            session_id=parent_operation.session_id,
            parent_operation_id=parent_operation_id,
            metadata={
                "parent_operation_id": parent_operation_id,
                "is_child_operation": True,
                **(metadata or {}),
            },
        )

        # Update parent operation's child list (avoid duplicates)
        if (
            child_operation_id
            and child_operation_id not in parent_operation.child_operations
        ):
            parent_operation.child_operations.append(child_operation_id)

        return child_operation_id

    async def update_bulk_progress(self, bulk_operation_id: str) -> bool:
        """
        Update bulk operation progress based on child operations.

        Returns:
            True if bulk operation was updated successfully
        """
        bulk_operation = self.get_operation(bulk_operation_id)
        if not bulk_operation:
            return False

        if not bulk_operation.child_operations:
            return True

        # Calculate progress based on child operations
        total_children = len(bulk_operation.child_operations)
        completed_children = 0
        failed_children = 0
        total_progress = 0.0

        for child_id in bulk_operation.child_operations:
            child_operation = self.get_operation(child_id)
            if child_operation:
                if child_operation.status == ProgressStatus.COMPLETED:
                    completed_children += 1
                    total_progress += 100.0
                elif child_operation.status == ProgressStatus.FAILED:
                    failed_children += 1
                    total_progress += 0.0
                else:
                    total_progress += child_operation.progress_percentage

        # Calculate overall progress
        if total_children > 0:
            overall_progress = total_progress / total_children
        else:
            overall_progress = 0.0

        # Update bulk operation
        bulk_operation.processed_items = completed_children + failed_children
        bulk_operation.successful_items = completed_children
        bulk_operation.failed_items = failed_children

        # Update progress
        await self.update_progress(
            operation_id=bulk_operation_id,
            progress=overall_progress,
            current_step=f"Processing {bulk_operation.processed_items}/{total_children} items",
            processed_items=bulk_operation.processed_items,
            successful_items=bulk_operation.successful_items,
            failed_items=bulk_operation.failed_items,
            metadata={
                "completed_children": completed_children,
                "failed_children": failed_children,
                "total_children": total_children,
            },
        )

        # Check if bulk operation is complete
        if bulk_operation.processed_items >= total_children:
            if failed_children == 0:
                await self.complete_operation(
                    bulk_operation_id,
                    f"Bulk operation completed successfully: {completed_children}/{total_children} items",
                )
            elif completed_children == 0:
                await self.fail_operation(
                    bulk_operation_id,
                    f"Bulk operation failed: {failed_children}/{total_children} items failed",
                )
            else:
                message = (
                    f"Bulk operation completed with warnings: {completed_children} "
                    f"succeeded, {failed_children} failed"
                )
                await self.complete_operation(bulk_operation_id, message)

        return True

    async def complete_child_operation(
        self,
        child_operation_id: str,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Complete a child operation and update the parent bulk operation.

        Returns:
            True if child operation was completed successfully
        """
        child_operation = self.get_operation(child_operation_id)
        if not child_operation:
            return False

        # Complete the child operation
        success = await self.complete_operation(child_operation_id, message, metadata)

        # Update parent bulk operation if it exists
        if success and child_operation.parent_operation_id:
            await self.update_bulk_progress(child_operation.parent_operation_id)

        return success

    async def fail_child_operation(
        self,
        child_operation_id: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Fail a child operation and update the parent bulk operation.

        Returns:
            True if child operation was failed successfully
        """
        child_operation = self.get_operation(child_operation_id)
        if not child_operation:
            return False

        # Fail the child operation
        success = await self.fail_operation(child_operation_id, error_message, metadata)

        # Update parent bulk operation if it exists
        if success and child_operation.parent_operation_id:
            await self.update_bulk_progress(child_operation.parent_operation_id)

        return success


# Global progress tracker instance
progress_tracker = ProgressTracker()
