import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.progress.websocket import websocket_manager
from app.core.providers.registry import provider_registry
from app.core.services.download_queue import PriorityDownload, queue_manager
from app.db.session import get_db
from app.models.manga import Manga

router = APIRouter(prefix="/downloads", tags=["downloads"])


class DownloadRequest(BaseModel):
    manga_id: UUID
    provider_name: str
    external_id: str
    priority: int = 3


@router.post("/enqueue")
async def enqueue_download(
    request: DownloadRequest, db: AsyncSession = Depends(get_db)
):
    """
    Enqueue a new download task.
    """
    provider = provider_registry.get_provider(request.provider_name)
    if not provider:
        raise HTTPException(
            status_code=404, detail=f"Provider '{request.provider_name}' not found"
        )

    manga = await db.get(Manga, request.manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")

    # Create the PriorityDownload item
    download_item = PriorityDownload(
        priority=request.priority,
        download_id=uuid.uuid4(),
        manga_id=request.manga_id,
        chapter_id=None,
        provider_name=request.provider_name,
        external_manga_id=request.external_id,
        external_chapter_id="",
        task_id=None,
        retry_count=0,
    )

    # Add to the queue manager
    await queue_manager.add_to_queue(download_item)

    return {
        "message": "Download enqueued successfully",
        "download_id": str(download_item.download_id),
        "priority": request.priority,
    }


@router.get("/status/{download_id}")
async def get_download_status(download_id: UUID):
    """
    Get the status of a specific download task.
    """
    # In a full implementation, this would query the database or a status cache
    return {
        "download_id": str(download_id),
        "status": "pending",
        "message": "Status retrieval from database or cache is not yet implemented.",
    }


@router.get("/queue_status")
async def get_queue_status():
    """
    Get the current status of the download queue.
    """
    status = await queue_manager.get_queue_status()
    return status


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for receiving progress updates.
    """
    await websocket_manager.connect(websocket, user_id=user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.handle_message(str(uuid.uuid4()), data)
    except WebSocketDisconnect:
        # Disconnect is handled by the manager
        pass
