"""
Progress tracking API endpoints.

This module provides REST API endpoints for managing and monitoring
progress operations in real-time.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel

from app.core.progress import (
    OperationType,
    ProgressStatus,
    persistence_service,
    progress_tracker,
    websocket_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ProgressOperationResponse(BaseModel):
    """Response model for progress operations."""

    id: str
    operation_type: str
    title: str
    description: str
    status: str
    progress_percentage: float
    current_step: str
    total_steps: Optional[int]
    current_step_number: Optional[int]
    started_at: str
    completed_at: Optional[str]
    estimated_completion: Optional[str]
    last_update: str
    error_message: Optional[str]
    warning_messages: List[str]
    metadata: Dict[str, Any]
    user_id: Optional[str]
    session_id: Optional[str]
    parent_operation_id: Optional[str]
    child_operations: List[str]
    total_items: Optional[int]
    processed_items: int
    successful_items: int
    failed_items: int
    is_cancellable: bool
    duration: Optional[float]


class ProgressEventResponse(BaseModel):
    """Response model for progress events."""

    id: str
    operation_id: str
    operation_type: str
    event_type: str
    progress_percentage: float
    current_step: str
    total_steps: Optional[int]
    current_step_number: Optional[int]
    message: str
    error_message: Optional[str]
    warning_message: Optional[str]
    metadata: Dict[str, Any]
    timestamp: str
    estimated_completion: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]


class ProgressSummaryResponse(BaseModel):
    """Response model for progress summary."""

    total_operations: int
    active_operations: int
    completed_operations: int
    failed_operations: int
    cancelled_operations: int
    operations_by_type: Dict[str, int]
    operations_by_status: Dict[str, int]


@router.get("/summary", response_model=ProgressSummaryResponse)
async def get_progress_summary(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
):
    """Get a summary of all progress operations."""
    try:
        operations = progress_tracker.get_operations(
            user_id=user_id, session_id=session_id, limit=1000  # Get all for summary
        )

        # Calculate summary statistics
        total_operations = len(operations)
        active_operations = len([op for op in operations if op.is_active()])
        completed_operations = len(
            [op for op in operations if op.status == ProgressStatus.COMPLETED]
        )
        failed_operations = len(
            [op for op in operations if op.status == ProgressStatus.FAILED]
        )
        cancelled_operations = len(
            [op for op in operations if op.status == ProgressStatus.CANCELLED]
        )

        # Group by type and status
        operations_by_type = {}
        operations_by_status = {}

        for operation in operations:
            op_type = operation.operation_type.value
            op_status = operation.status.value

            operations_by_type[op_type] = operations_by_type.get(op_type, 0) + 1
            operations_by_status[op_status] = operations_by_status.get(op_status, 0) + 1

        return ProgressSummaryResponse(
            total_operations=total_operations,
            active_operations=active_operations,
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            cancelled_operations=cancelled_operations,
            operations_by_type=operations_by_type,
            operations_by_status=operations_by_status,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving progress summary: {str(e)}",
        )


@router.get("/operations", response_model=List[ProgressOperationResponse])
async def get_operations(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    active_only: bool = Query(False, description="Show only active operations"),
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of operations to return"
    ),
    offset: int = Query(0, ge=0, description="Number of operations to skip"),
):
    """Get progress operations with optional filtering."""
    try:
        # Convert string parameters to enums if provided
        operation_type_enum = None
        if operation_type:
            try:
                operation_type_enum = OperationType(operation_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid operation type: {operation_type}",
                )

        status_enum = None
        if status:
            try:
                status_enum = ProgressStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}",
                )

        operations = progress_tracker.get_operations(
            user_id=user_id,
            session_id=session_id,
            operation_type=operation_type_enum,
            status=status_enum,
            active_only=active_only,
        )

        # Apply pagination
        paginated_operations = operations[offset : offset + limit]

        return [
            ProgressOperationResponse(**operation.to_dict())
            for operation in paginated_operations
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving operations: {str(e)}",
        )


@router.get("/operations/{operation_id}", response_model=ProgressOperationResponse)
async def get_operation(operation_id: str):
    """Get details of a specific operation."""
    try:
        operation = progress_tracker.get_operation(operation_id)
        if not operation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation {operation_id} not found",
            )

        return ProgressOperationResponse(**operation.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving operation: {str(e)}",
        )


@router.post("/operations/{operation_id}/cancel")
async def cancel_operation(operation_id: str):
    """Cancel a progress operation."""
    try:
        success = await progress_tracker.cancel_operation(operation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation {operation_id} not found or cannot be cancelled",
            )

        return {"message": f"Operation {operation_id} cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling operation: {str(e)}",
        )


@router.get(
    "/operations/{operation_id}/events", response_model=List[ProgressEventResponse]
)
async def get_operation_events(
    operation_id: str,
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of events to return"
    ),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
):
    """Get events for a specific operation."""
    try:
        # Check if operation exists
        operation = progress_tracker.get_operation(operation_id)
        if not operation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation {operation_id} not found",
            )

        # Get events from persistence service if available
        if persistence_service:
            events = await persistence_service.get_operation_events(
                operation_id=operation_id, limit=limit, offset=offset
            )

            return [ProgressEventResponse(**event.to_dict()) for event in events]
        else:
            # If no persistence, return empty list
            return []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving operation events: {str(e)}",
        )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
):
    """WebSocket endpoint for real-time progress updates."""
    connection_id = await websocket_manager.connect(websocket, user_id, session_id)

    try:
        while True:
            # Wait for messages from client
            message = await websocket.receive_text()
            await websocket_manager.handle_message(connection_id, message)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
        await websocket_manager.disconnect(connection_id)


@router.get("/websocket/connections")
async def get_websocket_connections():
    """Get information about active WebSocket connections."""
    try:
        return {
            "total_connections": websocket_manager.get_connection_count(),
            "connections_by_user": {
                user_id: len(connections)
                for user_id, connections in websocket_manager._connections.items()
                if connections
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving WebSocket connections: {str(e)}",
        )
