"""Series added from extension sources, with their provider metadata and revert."""
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.extension_series import Series, SourceDownload
from app.models.user import User
from app.sources.deps import get_host_client, host_error, make_download_worker
from app.sources.host_client import ExtensionHostClient, ExtensionHostError
from app.sources.series_service import SourceRef, add_series, migrate_to_source, revert_to_provider

router = APIRouter()


class AddSeriesBody(BaseModel):
    module: str = Field(..., min_length=3, max_length=120)
    source_name: str = Field(..., min_length=1, max_length=255)
    source_lang: str = Field(..., min_length=1, max_length=20)
    source_id: Optional[str] = Field(None, max_length=40)
    content_warning: Optional[str] = Field(None, max_length=40)
    # The manga object returned by POST /sources/{module}/details (its "manga" field).
    manga: dict[str, Any]


def _series_json(series: Series, *, full: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": str(series.id),
        "title": series.title,
        "cover_url": series.cover_url,
        "is_nsfw": series.is_nsfw,
        "content_warning": series.content_warning,
        "in_library": series.in_library,
        "module": series.module,
        "source_name": series.source_name,
        "source_lang": series.source_lang,
        "created_at": series.created_at.isoformat() if series.created_at else None,
    }
    if full:
        meta = series.metadata_record
        out["series_url"] = series.series_url
        out["package"] = series.package
        out["metadata"] = {
            "current": meta.current if meta else None,
            "base": meta.base if meta else None,
            "has_mangaupdates": bool(meta and meta.mangaupdates),
        }
    return out


async def _load(db: AsyncSession, series_id: UUID) -> Series:
    result = await db.execute(
        select(Series)
        .where(Series.id == series_id)
        .options(selectinload(Series.metadata_record))
    )
    series = result.scalar_one_or_none()
    if series is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="series not found")
    return series


async def _installed_or_error(host: ExtensionHostClient, module: str) -> dict[str, Any]:
    try:
        installed = (await host.installed()).get("extensions", {}).get(module)
    except ExtensionHostError as e:
        raise host_error(e)
    if installed is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"not installed: {module}")
    if not installed.get("enabled", False):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"disabled: {module}")
    if not installed.get("package"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"no package recorded for {module}")
    return installed


@router.post("", status_code=status.HTTP_201_CREATED)
async def add(
    body: AddSeriesBody,
    response: Response,
    db: AsyncSession = Depends(get_db),
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    """Adds a title from an installed, enabled extension. The package comes from the host, not the client."""
    installed = await _installed_or_error(host, body.module)
    package = installed["package"]
    if not body.manga.get("url") or not body.manga.get("title"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="manga needs url and title")

    ref = SourceRef(module=body.module, package=package, name=body.source_name,
                    lang=body.source_lang, source_id=body.source_id)
    series, created = await add_series(db, ref, body.manga, content_warning=body.content_warning)
    await db.commit()
    if not created:
        response.status_code = status.HTTP_200_OK
    series = await _load(db, series.id)
    return _series_json(series, full=True)


@router.get("")
async def list_series(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    in_library: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Any:
    where = Series.in_library.is_(in_library)
    total = (await db.execute(select(func.count()).select_from(Series).where(where))).scalar_one()
    rows = (await db.execute(
        select(Series).where(where).order_by(Series.title).limit(limit).offset(offset)
    )).scalars().all()
    return {"total": total, "items": [_series_json(s) for s in rows]}


@router.get("/{series_id}")
async def get_series(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Any:
    return _series_json(await _load(db, series_id), full=True)


@router.post("/{series_id}/revert")
async def revert(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Any:
    """Resets the shown metadata to the provider snapshot."""
    series = await _load(db, series_id)
    await revert_to_provider(db, series)
    await db.commit()
    return _series_json(await _load(db, series_id), full=True)


class MigrateBody(AddSeriesBody):
    replace: bool = True  # False keeps the old entry in the library too (Mihon's "copy")
    carry_metadata: bool = False  # copy the values chosen from MangaUpdates or edited, keeping their origin
    carry_read_state: bool = True  # Mihon's CHAPTER flag: read and bookmark by chapter number


@router.post("/{series_id}/migrate", status_code=status.HTTP_201_CREATED)
async def migrate(
    series_id: UUID,
    body: MigrateBody,
    response: Response,
    db: AsyncSession = Depends(get_db),
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    """Moves a title to another installed source, as Mihon does: a new entry for the target, and the old one
    leaves the library (unless replace=false). Read state and downloads are not moved here (see TODO)."""
    old = await _load(db, series_id)
    installed = await _installed_or_error(host, body.module)
    ref = SourceRef(module=body.module, package=installed["package"], name=body.source_name,
                    lang=body.source_lang, source_id=body.source_id)
    if not body.manga.get("url") or not body.manga.get("title"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="manga needs url and title")
    try:
        new, created = await migrate_to_source(
            db, old, ref, body.manga, content_warning=body.content_warning,
            replace=body.replace, carry_metadata=body.carry_metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    reading = None
    if body.carry_read_state:
        from app.api.api_v2.endpoints.reading import refresh_chapters
        from app.sources.reading_service import carry_reading_state

        await refresh_chapters(db, host, old)
        await refresh_chapters(db, host, new)
        result = await carry_reading_state(db, _user.id, old.id, new.id)
        reading = {"carried_read": result.carried_read, "carried_bookmarks": result.carried_bookmarks,
                   "unmatched_old_chapters": result.unmatched_old}
    await db.commit()
    if not created:
        response.status_code = status.HTTP_200_OK
    new = await _load(db, new.id)
    return {"from": _series_json(old), "to": _series_json(new, full=True), "reading": reading}


class DownloadChapter(BaseModel):
    url: str = Field(..., min_length=1)
    name: str = Field("", max_length=500)
    chapter_number: Optional[float] = None


class EnqueueBody(BaseModel):
    # Empty list means every chapter the source lists for this title.
    chapters: list[DownloadChapter] = Field(default_factory=list)


def _download_json(row: SourceDownload) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "module": row.module,
        "chapter_url": row.chapter_url,
        "chapter_name": row.chapter_name,
        "chapter_number": row.chapter_number,
        "status": row.status,
        "page_count": row.page_count,
        "path": row.path,
        "attempts": row.attempts,
        "last_error": row.last_error,
    }


@router.post("/{series_id}/downloads", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_downloads(
    series_id: UUID,
    body: EnqueueBody,
    db: AsyncSession = Depends(get_db),
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    """Queues chapters from this entry's source. Already queued or downloaded ones are skipped."""
    series = await _load(db, series_id)
    if not series.in_library:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not in the library")

    chapters = [c.model_dump() for c in body.chapters]
    if not chapters:
        try:
            details = await host.details(series.module, series.series_url)
        except ExtensionHostError as e:
            raise host_error(e)
        chapters = [
            {"url": c["url"], "name": c.get("name", ""), "chapter_number": c.get("chapter_number")}
            for c in details.get("chapters", [])
        ]
    worker = make_download_worker(host)
    added = await worker.enqueue(db, series, series.module, chapters)
    await db.commit()
    return {"queued": len(added), "rows": [_download_json(r) for r in added]}


@router.get("/{series_id}/downloads")
async def list_downloads(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Any:
    await _load(db, series_id)
    rows = (await db.execute(
        select(SourceDownload).where(SourceDownload.series_id == series_id)
        .order_by(SourceDownload.chapter_number, SourceDownload.created_at)
    )).scalars().all()
    return {"items": [_download_json(r) for r in rows]}


@router.post("/downloads/process")
async def process_downloads(
    limit: int = Query(5, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    """Runs the queue once: downloads up to `limit` queued chapters. Rows left downloading by a restart are
    put back by the worker's recover() at startup, not here, so a manual run never resets active work."""
    worker = make_download_worker(host)
    result = await worker.process(db, limit=limit)
    return {"attempted": result.attempted, "downloaded": result.downloaded, "failed": result.failed}
