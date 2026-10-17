"""Download controls per chapter: retry, cancel, remove, and re-download."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.extension_series import Series, SourceDownload
from app.models.user import User
from app.sources import download_control as ctl

router = APIRouter()


async def _row(db: AsyncSession, series_id: UUID, download_id: UUID) -> SourceDownload:
    row = await db.get(SourceDownload, download_id)
    if row is None or row.series_id != series_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="download not found for this series")
    return row


def _json(row: SourceDownload) -> dict[str, Any]:
    return {"id": str(row.id), "chapter_url": row.chapter_url, "chapter_name": row.chapter_name,
            "status": row.status, "path": row.path, "last_error": row.last_error, "attempts": row.attempts}


async def _guard(fn):
    try:
        return await fn()
    except ctl.DownloadControlError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/series/{series_id}/downloads/{download_id}/retry")
async def retry(series_id: UUID, download_id: UUID, db: AsyncSession = Depends(get_db),
                _user: User = Depends(get_current_user)) -> Any:
    row = await _row(db, series_id, download_id)
    await _guard(lambda: ctl.retry(db, row))
    await db.commit()
    return _json(row)


@router.post("/series/{series_id}/downloads/{download_id}/cancel")
async def cancel(series_id: UUID, download_id: UUID, db: AsyncSession = Depends(get_db),
                 _user: User = Depends(get_current_user)) -> Any:
    row = await _row(db, series_id, download_id)
    await _guard(lambda: ctl.cancel(db, row))
    await db.commit()
    return _json(row)


@router.post("/series/{series_id}/downloads/{download_id}/redownload")
async def redownload(series_id: UUID, download_id: UUID, db: AsyncSession = Depends(get_db),
                     _user: User = Depends(get_current_user)) -> Any:
    row = await _row(db, series_id, download_id)
    await _guard(lambda: ctl.redownload(db, row, settings.SOURCE_DOWNLOAD_DIR))
    await db.commit()
    return _json(row)


@router.delete("/series/{series_id}/downloads/{download_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(series_id: UUID, download_id: UUID, db: AsyncSession = Depends(get_db),
                 _user: User = Depends(get_current_user)) -> None:
    row = await _row(db, series_id, download_id)
    await _guard(lambda: ctl.remove(db, row, settings.SOURCE_DOWNLOAD_DIR))
    await db.commit()
