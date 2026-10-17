"""Reading state per user: chapters with their state, read/bookmark/progress, and activity stats."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.timezones import effective_zone
from app.models.extension_series import Series
from app.models.reading import ReadingState, SeriesChapter
from app.models.user import User
from app.sources.deps import get_host_client, host_error
from app.sources.host_client import ExtensionHostClient, ExtensionHostError
from app.sources.reading_service import (
    get_state,
    list_chapters,
    set_bookmark,
    set_progress,
    set_read,
    stats,
    sync_chapters,
)

router = APIRouter()


class ReadBody(BaseModel):
    read: bool


class BookmarkBody(BaseModel):
    bookmark: bool


class ProgressBody(BaseModel):
    page: int = Field(..., ge=0, le=100000)


def chapter_json(chapter: SeriesChapter, state: ReadingState | None) -> dict[str, Any]:
    return {
        "id": str(chapter.id),
        "name": chapter.name,
        "chapter_number": chapter.chapter_number,
        "url": chapter.url,
        "date_upload": chapter.date_upload,
        "scanlator": chapter.scanlator,
        "read": bool(state and state.read),
        "bookmark": bool(state and state.bookmark),
        "last_page": state.last_page if state else None,
    }


async def _series_or_404(db: AsyncSession, series_id: UUID) -> Series:
    series = await db.get(Series, series_id)
    if series is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="series not found")
    return series


async def _chapter_or_404(db: AsyncSession, series: Series, chapter_id: UUID) -> SeriesChapter:
    chapter = await db.get(SeriesChapter, chapter_id)
    if chapter is None or chapter.series_id != series.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="chapter not found for this series")
    return chapter


async def refresh_chapters(db: AsyncSession, host: ExtensionHostClient, series: Series) -> None:
    """Pulls the chapter list from the source into the cache."""
    try:
        details = await host.details(series.module, series.series_url)
    except ExtensionHostError as e:
        raise host_error(e)
    await sync_chapters(db, series, details.get("chapters", []))


@router.get("/series/{series_id}/chapters")
async def chapters(
    series_id: UUID,
    refresh: bool = Query(False, description="pull the chapter list from the source first"),
    db: AsyncSession = Depends(get_db),
    host: ExtensionHostClient = Depends(get_host_client),
    user: User = Depends(get_current_user),
) -> Any:
    series = await _series_or_404(db, series_id)
    if refresh or not await list_chapters(db, series.id):
        await refresh_chapters(db, host, series)
        await db.commit()
    rows = await list_chapters(db, series.id)
    states = {s.chapter_id: s for s in (await db.execute(
        select(ReadingState).where(ReadingState.user_id == user.id, ReadingState.series_id == series.id)
    )).scalars().all()}
    return {"series_id": str(series.id), "items": [chapter_json(c, states.get(c.id)) for c in rows]}


@router.put("/series/{series_id}/chapters/{chapter_id}/read")
async def mark_read(
    series_id: UUID,
    chapter_id: UUID,
    body: ReadBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    series = await _series_or_404(db, series_id)
    chapter = await _chapter_or_404(db, series, chapter_id)
    state = await set_read(db, user.id, chapter, body.read, zone=effective_zone(getattr(user, "timezone", None))[0])
    await db.commit()
    return chapter_json(chapter, state)


@router.put("/series/{series_id}/chapters/{chapter_id}/bookmark")
async def mark_bookmark(
    series_id: UUID,
    chapter_id: UUID,
    body: BookmarkBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    series = await _series_or_404(db, series_id)
    chapter = await _chapter_or_404(db, series, chapter_id)
    state = await set_bookmark(db, user.id, chapter, body.bookmark)
    await db.commit()
    return chapter_json(chapter, state)


@router.put("/series/{series_id}/chapters/{chapter_id}/progress")
async def save_progress(
    series_id: UUID,
    chapter_id: UUID,
    body: ProgressBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    series = await _series_or_404(db, series_id)
    chapter = await _chapter_or_404(db, series, chapter_id)
    state = await set_progress(db, user.id, chapter, body.page)
    await db.commit()
    return chapter_json(chapter, state)


@router.get("/reading/stats")
async def reading_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    st = await stats(db, user.id, zone=effective_zone(getattr(user, "timezone", None))[0])
    return {
        "latest": st.latest,
        "today": st.today,
        "this_week": st.this_week,
        "this_month": st.this_month,
        "this_year": st.this_year,
        "heatmap": st.heatmap,
    }
