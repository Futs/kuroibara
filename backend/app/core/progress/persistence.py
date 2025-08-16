"""
Progress persistence service for database operations.

This module provides database persistence for progress operations and events.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.progress import (
    ProgressEventModel,
    ProgressOperationModel,
    ProgressSessionModel,
)

from .events import (
    OperationType,
    ProgressEvent,
    ProgressEventType,
    ProgressOperation,
    ProgressStatus,
)

logger = logging.getLogger(__name__)


class ProgressPersistenceService:
    """
    Service for persisting progress operations and events to database.

    Features:
    - Operation CRUD operations
    - Event logging
    - Session management
    - Cleanup of old data
    """

    def __init__(self):
        self._cleanup_interval = 86400  # 24 hours
        self._max_operation_age_days = 30
        self._max_event_age_days = 7

        logger.info("ProgressPersistenceService initialized")

    async def save_operation(
        self, operation: ProgressOperation, db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Save or update a progress operation.

        Returns:
            True if operation was saved successfully
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            # Check if operation already exists
            existing = await db.get(ProgressOperationModel, operation.id)

            if existing:
                # Update existing operation
                existing.status = operation.status.value
                existing.progress_percentage = operation.progress_percentage
                existing.current_step = operation.current_step
                existing.current_step_number = operation.current_step_number
                existing.completed_at = operation.completed_at
                existing.estimated_completion = operation.estimated_completion
                existing.last_update = operation.last_update
                existing.error_message = operation.error_message
                existing.warning_messages = operation.warning_messages
                existing.operation_metadata = operation.metadata
                existing.processed_items = operation.processed_items
                existing.successful_items = operation.successful_items
                existing.failed_items = operation.failed_items
                existing.cancellation_token = operation.cancellation_token
            else:
                # Create new operation
                db_operation = ProgressOperationModel(
                    id=operation.id,
                    operation_type=operation.operation_type.value,
                    title=operation.title,
                    description=operation.description,
                    status=operation.status.value,
                    progress_percentage=operation.progress_percentage,
                    current_step=operation.current_step,
                    total_steps=operation.total_steps,
                    current_step_number=operation.current_step_number,
                    started_at=operation.started_at,
                    completed_at=operation.completed_at,
                    estimated_completion=operation.estimated_completion,
                    last_update=operation.last_update,
                    error_message=operation.error_message,
                    warning_messages=operation.warning_messages,
                    operation_metadata=operation.metadata,
                    user_id=UUID(operation.user_id) if operation.user_id else None,
                    session_id=operation.session_id,
                    parent_operation_id=(
                        UUID(operation.parent_operation_id)
                        if operation.parent_operation_id
                        else None
                    ),
                    total_items=operation.total_items,
                    processed_items=operation.processed_items,
                    successful_items=operation.successful_items,
                    failed_items=operation.failed_items,
                    is_cancellable=operation.is_cancellable,
                    cancellation_token=operation.cancellation_token,
                )
                db.add(db_operation)

            await db.commit()
            logger.debug(f"Saved operation {operation.id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving operation {operation.id}: {e}")
            return False
        finally:
            if should_close_db:
                await db.close()

    async def save_event(
        self, event: ProgressEvent, db: Optional[AsyncSession] = None
    ) -> bool:
        """
        Save a progress event.

        Returns:
            True if event was saved successfully
        """
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            db_event = ProgressEventModel(
                id=event.id,
                operation_id=UUID(event.operation_id),
                event_type=event.event_type.value,
                progress_percentage=event.progress_percentage,
                current_step=event.current_step,
                total_steps=event.total_steps,
                current_step_number=event.current_step_number,
                message=event.message,
                error_message=event.error_message,
                warning_message=event.warning_message,
                event_metadata=event.metadata,
                timestamp=event.timestamp,
                estimated_completion=event.estimated_completion,
                user_id=UUID(event.user_id) if event.user_id else None,
                session_id=event.session_id,
            )

            db.add(db_event)
            await db.commit()
            logger.debug(f"Saved event {event.id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving event {event.id}: {e}")
            return False
        finally:
            if should_close_db:
                await db.close()

    async def get_operation(
        self, operation_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[ProgressOperation]:
        """Get an operation by ID."""
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            db_operation = await db.get(ProgressOperationModel, UUID(operation_id))
            if not db_operation:
                return None

            return self._db_operation_to_progress_operation(db_operation)

        except Exception as e:
            logger.error(f"Error getting operation {operation_id}: {e}")
            return None
        finally:
            if should_close_db:
                await db.close()

    async def get_operations(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        operation_type: Optional[OperationType] = None,
        status: Optional[ProgressStatus] = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
        db: Optional[AsyncSession] = None,
    ) -> List[ProgressOperation]:
        """Get operations with filtering."""
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            query = db.query(ProgressOperationModel)

            # Apply filters
            if user_id:
                query = query.filter(ProgressOperationModel.user_id == UUID(user_id))

            if session_id:
                query = query.filter(ProgressOperationModel.session_id == session_id)

            if operation_type:
                query = query.filter(
                    ProgressOperationModel.operation_type == operation_type.value
                )

            if status:
                query = query.filter(ProgressOperationModel.status == status.value)

            if active_only:
                query = query.filter(
                    ProgressOperationModel.status.in_(["pending", "running", "paused"])
                )

            # Order by last update (most recent first)
            query = query.order_by(desc(ProgressOperationModel.last_update))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            result = await query.all()

            return [self._db_operation_to_progress_operation(op) for op in result]

        except Exception as e:
            logger.error(f"Error getting operations: {e}")
            return []
        finally:
            if should_close_db:
                await db.close()

    async def get_operation_events(
        self,
        operation_id: str,
        limit: int = 100,
        offset: int = 0,
        db: Optional[AsyncSession] = None,
    ) -> List[ProgressEvent]:
        """Get events for an operation."""
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            query = (
                db.query(ProgressEventModel)
                .filter(ProgressEventModel.operation_id == UUID(operation_id))
                .order_by(desc(ProgressEventModel.timestamp))
            )

            query = query.offset(offset).limit(limit)
            result = await query.all()

            return [self._db_event_to_progress_event(event) for event in result]

        except Exception as e:
            logger.error(f"Error getting events for operation {operation_id}: {e}")
            return []
        finally:
            if should_close_db:
                await db.close()

    async def delete_operation(
        self, operation_id: str, db: Optional[AsyncSession] = None
    ) -> bool:
        """Delete an operation and its events."""
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            db_operation = await db.get(ProgressOperationModel, UUID(operation_id))
            if not db_operation:
                return False

            await db.delete(db_operation)
            await db.commit()
            logger.debug(f"Deleted operation {operation_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting operation {operation_id}: {e}")
            return False
        finally:
            if should_close_db:
                await db.close()

    async def cleanup_old_data(
        self, db: Optional[AsyncSession] = None
    ) -> Dict[str, int]:
        """Clean up old operations and events."""
        should_close_db = db is None
        if db is None:
            db = AsyncSessionLocal()

        try:
            operation_cutoff = datetime.utcnow() - timedelta(
                days=self._max_operation_age_days
            )
            event_cutoff = datetime.utcnow() - timedelta(days=self._max_event_age_days)

            # Delete old completed operations
            old_operations = (
                await db.query(ProgressOperationModel)
                .filter(
                    and_(
                        ProgressOperationModel.completed_at < operation_cutoff,
                        ProgressOperationModel.status.in_(
                            ["completed", "failed", "cancelled"]
                        ),
                    )
                )
                .all()
            )

            operations_deleted = len(old_operations)
            for operation in old_operations:
                await db.delete(operation)

            # Delete old events (orphaned events will be deleted by cascade)
            events_deleted = (
                await db.query(ProgressEventModel)
                .filter(ProgressEventModel.timestamp < event_cutoff)
                .delete()
            )

            await db.commit()

            result = {
                "operations_deleted": operations_deleted,
                "events_deleted": events_deleted,
            }

            logger.info(f"Cleanup completed: {result}")
            return result

        except Exception as e:
            await db.rollback()
            logger.error(f"Error during cleanup: {e}")
            return {"operations_deleted": 0, "events_deleted": 0}
        finally:
            if should_close_db:
                await db.close()

    def _db_operation_to_progress_operation(
        self, db_operation: ProgressOperationModel
    ) -> ProgressOperation:
        """Convert database model to ProgressOperation."""
        operation = ProgressOperation(
            id=str(db_operation.id),
            operation_type=OperationType(db_operation.operation_type),
            title=db_operation.title,
            description=db_operation.description or "",
            status=ProgressStatus(db_operation.status),
            progress_percentage=db_operation.progress_percentage,
            current_step=db_operation.current_step or "",
            total_steps=db_operation.total_steps,
            current_step_number=db_operation.current_step_number,
            started_at=db_operation.started_at,
            completed_at=db_operation.completed_at,
            estimated_completion=db_operation.estimated_completion,
            last_update=db_operation.last_update,
            error_message=db_operation.error_message,
            warning_messages=db_operation.warning_messages or [],
            metadata=db_operation.operation_metadata or {},
            user_id=str(db_operation.user_id) if db_operation.user_id else None,
            session_id=db_operation.session_id,
            parent_operation_id=(
                str(db_operation.parent_operation_id)
                if db_operation.parent_operation_id
                else None
            ),
            total_items=db_operation.total_items,
            processed_items=db_operation.processed_items,
            successful_items=db_operation.successful_items,
            failed_items=db_operation.failed_items,
            is_cancellable=db_operation.is_cancellable,
            cancellation_token=db_operation.cancellation_token,
        )

        # Set child operations
        if hasattr(db_operation, "child_operations") and db_operation.child_operations:
            operation.child_operations = [
                str(child.id) for child in db_operation.child_operations
            ]

        return operation

    def _db_event_to_progress_event(
        self, db_event: ProgressEventModel
    ) -> ProgressEvent:
        """Convert database model to ProgressEvent."""
        return ProgressEvent(
            id=str(db_event.id),
            operation_id=str(db_event.operation_id),
            operation_type=OperationType(db_event.operation.operation_type),
            event_type=ProgressEventType(db_event.event_type),
            progress_percentage=db_event.progress_percentage,
            current_step=db_event.current_step or "",
            total_steps=db_event.total_steps,
            current_step_number=db_event.current_step_number,
            message=db_event.message or "",
            error_message=db_event.error_message,
            warning_message=db_event.warning_message,
            metadata=db_event.event_metadata or {},
            timestamp=db_event.timestamp,
            estimated_completion=db_event.estimated_completion,
            user_id=str(db_event.user_id) if db_event.user_id else None,
            session_id=db_event.session_id,
        )


# Global persistence service instance
persistence_service = ProgressPersistenceService()
