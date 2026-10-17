"""Reading state, bookmarks and progress per user, the activity rollup, and stats. Also carries state across a migration.

Rules (Mihon's, adapted):
- A user's read/unread change writes one reading_events row and adjusts user_day_activity for the UTC day.
  Setting the same value again does nothing. Unreading subtracts, so the day total is the net count.
- A migration is not activity. Carrying read state to a new entry writes no events and changes no rollup.
- Chapters are matched by chapter number. Chapters at or below the highest chapter the user had read
  are marked read on the target (Mihon's rule). Bookmarks are copied by number.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezones import UTC, local_day
from app.models.extension_series import Series
from app.models.reading import ReadingEvent, ReadingState, SeriesChapter, UserDayActivity


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def sync_chapters(db: AsyncSession, series: Series, chapters: list[dict[str, Any]]) -> list[SeriesChapter]:
    """Upserts the chapters the source lists. Chapters the source no longer lists are kept, so history stays."""
    existing = {c.url: c for c in (await db.execute(
        select(SeriesChapter).where(SeriesChapter.series_id == series.id))).scalars().all()}
    for ch in chapters:
        row = existing.get(ch["url"])
        if row is None:
            row = SeriesChapter(series_id=series.id, url=ch["url"])
            db.add(row)
            existing[ch["url"]] = row
        row.name = ch.get("name") or ""
        row.chapter_number = ch.get("chapter_number")
        row.date_upload = ch.get("date_upload")
        row.scanlator = ch.get("scanlator")
    await db.flush()
    return await list_chapters(db, series.id)


async def list_chapters(db: AsyncSession, series_id: UUID) -> list[SeriesChapter]:
    rows = (await db.execute(select(SeriesChapter).where(SeriesChapter.series_id == series_id))).scalars().all()
    return sorted(rows, key=lambda c: (c.chapter_number is None, -(c.chapter_number or 0), c.name))


async def get_state(db: AsyncSession, user_id: UUID, chapter: SeriesChapter) -> Optional[ReadingState]:
    return await db.get(ReadingState, (user_id, chapter.id))


async def _state_or_new(db: AsyncSession, user_id: UUID, chapter: SeriesChapter) -> ReadingState:
    state = await get_state(db, user_id, chapter)
    if state is None:
        state = ReadingState(user_id=user_id, chapter_id=chapter.id, series_id=chapter.series_id,
                             read=False, bookmark=False)
        db.add(state)
        await db.flush()  # so a second lookup in the same session finds it instead of adding a duplicate
    return state


async def _bump_day(db: AsyncSession, user_id: UUID, day: date, delta: int) -> None:
    stmt = insert(UserDayActivity).values(user_id=user_id, day=day, chapters_read=delta)
    stmt = stmt.on_conflict_do_update(
        index_elements=[UserDayActivity.user_id, UserDayActivity.day],
        set_={"chapters_read": UserDayActivity.chapters_read + delta},
    )
    await db.execute(stmt)


async def set_read(db: AsyncSession, user_id: UUID, chapter: SeriesChapter, read: bool,
                   *, now: Optional[datetime] = None, zone: ZoneInfo = UTC) -> ReadingState:
    """User marks a chapter read or unread. Writes an event and adjusts the day's total only on a real change.
    The day is the user's local day in `zone`, stored on the event."""
    now = now or utc_now()
    state = await _state_or_new(db, user_id, chapter)
    if state.read == read:
        return state
    state.read = read
    state.read_at = now if read else None
    day = local_day(now, zone)
    db.add(ReadingEvent(user_id=user_id, series_id=chapter.series_id, chapter_id=chapter.id,
                        kind="read" if read else "unread", at=now, local_day=day))
    await _bump_day(db, user_id, day, 1 if read else -1)
    await db.flush()
    return state


async def set_bookmark(db: AsyncSession, user_id: UUID, chapter: SeriesChapter, bookmark: bool) -> ReadingState:
    state = await _state_or_new(db, user_id, chapter)
    state.bookmark = bookmark
    await db.flush()
    return state


async def set_progress(db: AsyncSession, user_id: UUID, chapter: SeriesChapter, page: int) -> ReadingState:
    """Last page the user reached. Not activity, so no event."""
    state = await _state_or_new(db, user_id, chapter)
    state.last_page = page
    await db.flush()
    return state


@dataclass
class CarryResult:
    carried_read: int = 0
    carried_bookmarks: int = 0
    unmatched_old: list[float] = field(default_factory=list)  # old chapter numbers with no match on the new entry


async def carry_reading_state(db: AsyncSession, user_id: UUID, old_series_id: UUID, new_series_id: UUID) -> CarryResult:
    """Mihon's migration rule for reading state. Not activity: no events, no rollup change."""
    old_chapters = await list_chapters(db, old_series_id)
    new_chapters = await list_chapters(db, new_series_id)
    by_number = {c.chapter_number: c for c in new_chapters if c.chapter_number is not None}
    old_states = {s.chapter_id: s for s in (await db.execute(
        select(ReadingState).where(ReadingState.user_id == user_id, ReadingState.series_id == old_series_id)
    )).scalars().all()}

    read_numbers = [c.chapter_number for c in old_chapters
                    if c.chapter_number is not None and old_states.get(c.id) and old_states[c.id].read]
    max_read = max(read_numbers) if read_numbers else None

    result = CarryResult()
    for old in old_chapters:
        state = old_states.get(old.id)
        if state is None or (not state.read and not state.bookmark):
            continue
        if old.chapter_number is None or old.chapter_number not in by_number:
            result.unmatched_old.append(old.chapter_number if old.chapter_number is not None else -1.0)
            continue
        target = by_number[old.chapter_number]
        target_state = await _state_or_new(db, user_id, target)
        if state.bookmark and not target_state.bookmark:
            target_state.bookmark = True
            result.carried_bookmarks += 1
    for number, target in by_number.items():
        if max_read is not None and number <= max_read:
            target_state = await _state_or_new(db, user_id, target)
            if not target_state.read:
                target_state.read = True
                target_state.read_at = None  # not read today: the migration is not activity
                result.carried_read += 1
    await db.flush()
    return result


@dataclass
class Stats:
    latest: Optional[dict[str, Any]]
    today: int
    this_week: int
    this_month: int
    this_year: int
    heatmap: list[dict[str, Any]]


async def stats(db: AsyncSession, user_id: UUID, *, today: Optional[date] = None, zone: ZoneInfo = UTC,
                now: Optional[datetime] = None) -> Stats:
    """Latest read and counts for today, this week (Monday start), this month and this year, plus a 365-day heatmap.
    "Today" and the periods are the user's local days in `zone`."""
    today = today or local_day(now or utc_now(), zone)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    heat_start = today - timedelta(days=364)

    async def total_since(start: date) -> int:
        q = select(func.coalesce(func.sum(UserDayActivity.chapters_read), 0)).where(
            UserDayActivity.user_id == user_id, UserDayActivity.day >= start, UserDayActivity.day <= today)
        return int((await db.execute(q)).scalar_one())

    latest_event = (await db.execute(
        select(ReadingEvent).where(ReadingEvent.user_id == user_id, ReadingEvent.kind == "read")
        .order_by(ReadingEvent.at.desc()).limit(1)
    )).scalar_one_or_none()
    latest = None
    if latest_event is not None:
        chapter = await db.get(SeriesChapter, latest_event.chapter_id)
        series = await db.get(Series, latest_event.series_id)
        latest = {
            "series_id": str(latest_event.series_id),
            "series_title": series.title if series else None,
            "chapter_id": str(latest_event.chapter_id),
            "chapter_name": chapter.name if chapter else None,
            "chapter_number": chapter.chapter_number if chapter else None,
            "at": latest_event.at.isoformat(),
        }

    rows = (await db.execute(
        select(UserDayActivity.day, UserDayActivity.chapters_read).where(
            UserDayActivity.user_id == user_id, UserDayActivity.day >= heat_start, UserDayActivity.day <= today,
            UserDayActivity.chapters_read != 0)
        .order_by(UserDayActivity.day)
    )).all()
    return Stats(
        latest=latest,
        today=int((await db.execute(
            select(func.coalesce(func.sum(UserDayActivity.chapters_read), 0)).where(
                UserDayActivity.user_id == user_id, UserDayActivity.day == today))).scalar_one()),
        this_week=await total_since(week_start),
        this_month=await total_since(month_start),
        this_year=await total_since(year_start),
        heatmap=[{"day": d.isoformat(), "count": c} for d, c in rows],
    )
