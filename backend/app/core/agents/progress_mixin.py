"""
Progress tracking mixin for agents.

This module provides a mixin class that agents can inherit from to
automatically emit progress events during operations.
"""

import logging
from typing import Any, Dict, Optional

from ..progress import (
    OperationType,
    progress_tracker,
)

logger = logging.getLogger(__name__)


class ProgressAwareMixin:
    """
    Mixin class for agents to emit progress events.

    This mixin provides methods for agents to track and report progress
    during long-running operations like searches and downloads.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_operations: Dict[str, str] = {}  # operation_name -> operation_id
        self._operation_metadata: Dict[str, Dict[str, Any]] = {}

    async def start_progress_operation(
        self,
        operation_name: str,
        operation_type: OperationType,
        title: str,
        description: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        total_steps: Optional[int] = None,
        total_items: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start a new progress operation for this agent.

        Args:
            operation_name: Internal name for the operation (e.g., "search", "download")
            operation_type: Type of operation
            title: Human-readable title
            description: Detailed description
            user_id: User ID if applicable
            session_id: Session ID if applicable
            total_steps: Total number of steps
            total_items: Total number of items to process
            metadata: Additional metadata

        Returns:
            Operation ID
        """
        try:
            # Add agent information to metadata
            agent_metadata = {
                "agent_name": getattr(self, "name", "unknown"),
                "agent_type": self.__class__.__name__,
                **(metadata or {}),
            }

            operation_id = await progress_tracker.start_operation(
                operation_type=operation_type,
                title=f"[{getattr(self, 'name', 'Agent')}] {title}",
                description=description,
                user_id=user_id,
                session_id=session_id,
                total_steps=total_steps,
                total_items=total_items,
                metadata=agent_metadata,
            )

            # Track the operation
            self._current_operations[operation_name] = operation_id
            self._operation_metadata[operation_id] = {
                "operation_name": operation_name,
                "started_by": getattr(self, "name", "unknown"),
            }

            agent_name = getattr(self, "name", "unknown")
            logger.debug(
                f"Started progress operation {operation_name} ({operation_id}) "
                f"for agent {agent_name}"
            )
            return operation_id

        except Exception as e:
            logger.error(f"Error starting progress operation {operation_name}: {e}")
            return ""

    async def update_progress(
        self,
        operation_name: str,
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

        Args:
            operation_name: Name of the operation to update
            progress: Progress percentage (0-100)
            current_step: Current step description
            current_step_number: Current step number
            message: Progress message
            processed_items: Number of processed items
            successful_items: Number of successful items
            failed_items: Number of failed items
            metadata: Additional metadata

        Returns:
            True if progress was updated successfully
        """
        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            logger.warning(f"No active operation found for {operation_name}")
            return False

        try:
            return await progress_tracker.update_progress(
                operation_id=operation_id,
                progress=progress,
                current_step=current_step,
                current_step_number=current_step_number,
                message=message,
                processed_items=processed_items,
                successful_items=successful_items,
                failed_items=failed_items,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error updating progress for {operation_name}: {e}")
            return False

    async def complete_operation(
        self,
        operation_name: str,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark an operation as completed.

        Args:
            operation_name: Name of the operation to complete
            message: Completion message
            metadata: Additional metadata

        Returns:
            True if operation was completed successfully
        """
        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            logger.warning(f"No active operation found for {operation_name}")
            return False

        try:
            success = await progress_tracker.complete_operation(
                operation_id=operation_id, message=message, metadata=metadata
            )

            if success:
                # Clean up tracking
                del self._current_operations[operation_name]
                if operation_id in self._operation_metadata:
                    del self._operation_metadata[operation_id]

                logger.debug(f"Completed operation {operation_name} ({operation_id})")

            return success

        except Exception as e:
            logger.error(f"Error completing operation {operation_name}: {e}")
            return False

    async def fail_operation(
        self,
        operation_name: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark an operation as failed.

        Args:
            operation_name: Name of the operation that failed
            error_message: Error description
            metadata: Additional metadata

        Returns:
            True if operation was marked as failed successfully
        """
        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            logger.warning(f"No active operation found for {operation_name}")
            return False

        try:
            success = await progress_tracker.fail_operation(
                operation_id=operation_id,
                error_message=error_message,
                metadata=metadata,
            )

            if success:
                # Clean up tracking
                del self._current_operations[operation_name]
                if operation_id in self._operation_metadata:
                    del self._operation_metadata[operation_id]

                logger.debug(
                    f"Failed operation {operation_name} ({operation_id}): {error_message}"
                )

            return success

        except Exception as e:
            logger.error(f"Error failing operation {operation_name}: {e}")
            return False

    async def add_operation_warning(
        self,
        operation_name: str,
        warning_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a warning to an operation.

        Args:
            operation_name: Name of the operation
            warning_message: Warning description
            metadata: Additional metadata

        Returns:
            True if warning was added successfully
        """
        operation_id = self._current_operations.get(operation_name)
        if not operation_id:
            logger.warning(f"No active operation found for {operation_name}")
            return False

        try:
            return await progress_tracker.add_warning(
                operation_id=operation_id,
                warning_message=warning_message,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error adding warning to operation {operation_name}: {e}")
            return False

    def get_active_operations(self) -> Dict[str, str]:
        """Get all active operations for this agent."""
        return self._current_operations.copy()

    def has_active_operation(self, operation_name: str) -> bool:
        """Check if an operation is currently active."""
        return operation_name in self._current_operations

    async def cleanup_operations(self) -> None:
        """Clean up any remaining operations (called on agent shutdown)."""
        for operation_name, operation_id in list(self._current_operations.items()):
            try:
                await progress_tracker.cancel_operation(
                    operation_id=operation_id, message="Agent shutdown"
                )
                logger.debug(
                    f"Cancelled operation {operation_name} due to agent shutdown"
                )
            except Exception as e:
                logger.error(
                    f"Error cancelling operation {operation_name} during cleanup: {e}"
                )

        self._current_operations.clear()
        self._operation_metadata.clear()

    async def _execute_with_progress(
        self,
        operation_name: str,
        operation_type: OperationType,
        title: str,
        operation_func,
        *args,
        description: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        total_steps: Optional[int] = None,
        total_items: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Execute a function with automatic progress tracking.

        This is a convenience method that starts an operation, executes a function,
        and automatically completes or fails the operation based on the result.
        """
        operation_id = await self.start_progress_operation(
            operation_name=operation_name,
            operation_type=operation_type,
            title=title,
            description=description,
            user_id=user_id,
            session_id=session_id,
            total_steps=total_steps,
            total_items=total_items,
            metadata=metadata,
        )

        if not operation_id:
            # If we can't start progress tracking, still execute the function
            return await operation_func(*args, **kwargs)

        try:
            result = await operation_func(*args, **kwargs)
            await self.complete_operation(
                operation_name, "Operation completed successfully"
            )
            return result

        except Exception as e:
            await self.fail_operation(operation_name, str(e))
            raise
