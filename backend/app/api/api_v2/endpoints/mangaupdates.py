"""MangaUpdates for a library entry: search, link, refresh, compare, and apply per field."""
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.services.mangaupdates import MangaUpdatesAPI
from app.models.extension_series import Series
from app.models.user import User
from app.sources.mangaupdates_link import (
    compare,
    fetch_entry,
    plan_choices,
    search_candidates,
    store_snapshot,
)
from app.sources.series_service import apply_values
from app.api.api_v2.endpoints.series import _load, _series_json

router = APIRouter()


async def get_mu_api():
    """The MangaUpdates client. Tests replace this dependency; the live app uses the real API."""
    async with MangaUpdatesAPI() as api:
        yield api


class LinkBody(BaseModel):
    mu_series_id: int = Field(..., gt=0)


class ApplyBody(BaseModel):
    # field -> "provider" | "mangaupdates" | {"origin": "edited", "value": <any JSON value>}
    choices: dict[str, Any] = Field(..., min_length=1)


async def _entry(db: AsyncSession, series_id: UUID) -> Series:
    series = await _load(db, series_id)
    if series.metadata_record is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="entry has no metadata")
    return series


async def _fetch_or_502(api: MangaUpdatesAPI, mu_id: int) -> dict[str, Any]:
    fields = await fetch_entry(mu_id, api)
    if fields is None:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"MangaUpdates did not return series {mu_id}")
    return fields


@router.get("/series/{series_id}/mangaupdates/search")
async def search(
    series_id: UUID,
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    db: AsyncSession = Depends(get_db),
    api: MangaUpdatesAPI = Depends(get_mu_api),
    _user: User = Depends(get_current_user),
) -> Any:
    """Candidates for this title. Defaults to the shown title. The user picks one; nothing is linked yet."""
    series = await _load(db, series_id)
    raw = await api.search_series(q or series.title)
    return {"query": q or series.title, "items": search_candidates(raw)}


@router.post("/series/{series_id}/mangaupdates/link")
async def link(
    series_id: UUID,
    body: LinkBody,
    db: AsyncSession = Depends(get_db),
    api: MangaUpdatesAPI = Depends(get_mu_api),
    _user: User = Depends(get_current_user),
) -> Any:
    """Links a MangaUpdates series to this entry and caches its details. Changes no shown values."""
    series = await _entry(db, series_id)
    fields = await _fetch_or_502(api, body.mu_series_id)
    store_snapshot(series.metadata_record, body.mu_series_id, fields)
    await db.commit()
    return compare(series.metadata_record)


@router.post("/series/{series_id}/mangaupdates/refresh")
async def refresh(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    api: MangaUpdatesAPI = Depends(get_mu_api),
    _user: User = Depends(get_current_user),
) -> Any:
    """Fetches the linked MangaUpdates series again. Explicit only: never run automatically."""
    series = await _entry(db, series_id)
    mu = series.metadata_record.mangaupdates
    if not mu:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="no MangaUpdates entry is linked")
    fields = await _fetch_or_502(api, int(mu["series_id"]))
    store_snapshot(series.metadata_record, int(mu["series_id"]), fields)
    await db.commit()
    return compare(series.metadata_record)


@router.get("/series/{series_id}/mangaupdates/compare")
async def compare_view(
    series_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Any:
    """Provider value, MangaUpdates value and the shown value with its origin, per field. Works from the cache."""
    series = await _entry(db, series_id)
    return compare(series.metadata_record)


@router.post("/series/{series_id}/mangaupdates/apply")
async def apply(
    series_id: UUID,
    body: ApplyBody,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Any:
    """Applies the picks field by field. Fields not in the request keep their current value and origin."""
    series = await _entry(db, series_id)
    try:
        updates = plan_choices(body.choices, series.metadata_record)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    await apply_values(db, series, updates)
    await db.commit()
    series = await _load(db, series_id)
    return {"entry": _series_json(series, full=True), "compare": compare(series.metadata_record)}
