"""Reading state, the activity rollup, carry-over on migration, and stats. Test database."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.models.extension_series import Series
from app.models.reading import ReadingEvent, ReadingState, UserDayActivity
from app.models.user import User
from app.sources.reading_service import (
    carry_reading_state,
    set_bookmark,
    set_progress,
    set_read,
    stats,
    sync_chapters,
)
from app.sources.series_service import SourceRef, add_series

SRC = SourceRef(module="en/mangakatana", package="eu.kanade.tachiyomi.extension.en.mangakatana",
                name="MangaKatana", lang="en", source_id=None)
OTHER = SourceRef(module="en/toonily", package="eu.kanade.tachiyomi.extension.en.toonily",
                  name="Toonily", lang="en", source_id=None)
MANGA = {"url": "/manga/x", "title": "Series X"}
CHAPTERS = [{"url": f"/c/{i}", "name": f"Chapter {i}", "chapter_number": float(i)} for i in range(1, 6)]
NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)  # a Wednesday


async def make_user(db, name="reader"):
    user = User(username=name, email=f"{name}@example.test", hashed_password="x", is_active=True)
    db.add(user)
    await db.flush()
    return user


async def entry(db, source=SRC, url="/manga/x"):
    s, _ = await add_series(db, source, {**MANGA, "url": url})
    await sync_chapters(db, s, CHAPTERS)
    await db.flush()
    return s


async def chapter(db, series, number):
    from app.models.reading import SeriesChapter
    return (await db.execute(select(SeriesChapter).where(
        SeriesChapter.series_id == series.id, SeriesChapter.chapter_number == number))).scalar_one()


async def test_sync_chapters_upserts_and_keeps_history(db):
    s = await entry(db)
    again = await sync_chapters(db, s, CHAPTERS[:3] + [{"url": "/c/9", "name": "Chapter 9", "chapter_number": 9.0}])
    assert len(again) == 6  # the source dropped nothing from our cache; it added one
    assert (await chapter(db, s, 1)).name == "Chapter 1"


async def test_read_writes_an_event_and_counts_the_day(db):
    user = await make_user(db)
    s = await entry(db)
    c1 = await chapter(db, s, 1)
    await set_read(db, user.id, c1, True, now=NOW)
    await db.commit()
    events = (await db.execute(select(ReadingEvent).where(ReadingEvent.user_id == user.id))).scalars().all()
    assert [e.kind for e in events] == ["read"]
    day = (await db.execute(select(UserDayActivity).where(UserDayActivity.user_id == user.id))).scalar_one()
    assert day.day == NOW.date() and day.chapters_read == 1


async def test_setting_the_same_value_again_does_nothing(db):
    user = await make_user(db)
    s = await entry(db)
    c1 = await chapter(db, s, 1)
    await set_read(db, user.id, c1, True, now=NOW)
    await set_read(db, user.id, c1, True, now=NOW + timedelta(minutes=1))
    await db.commit()
    assert len((await db.execute(select(ReadingEvent))).scalars().all()) == 1


async def test_unread_subtracts_so_the_day_total_is_net(db):
    user = await make_user(db)
    s = await entry(db)
    c1, c2 = await chapter(db, s, 1), await chapter(db, s, 2)
    await set_read(db, user.id, c1, True, now=NOW)
    await set_read(db, user.id, c2, True, now=NOW)
    await set_read(db, user.id, c1, False, now=NOW)
    await db.commit()
    day = (await db.execute(select(UserDayActivity).where(UserDayActivity.user_id == user.id))).scalar_one()
    assert day.chapters_read == 1


async def test_bookmark_and_progress_are_not_activity(db):
    user = await make_user(db)
    s = await entry(db)
    c1 = await chapter(db, s, 1)
    await set_bookmark(db, user.id, c1, True)
    await set_progress(db, user.id, c1, 12)
    await db.commit()
    state = await db.get(ReadingState, (user.id, c1.id))
    assert state.bookmark is True and state.last_page == 12 and state.read is False
    assert (await db.execute(select(ReadingEvent))).scalars().all() == []


async def test_state_is_per_user(db):
    a, b = await make_user(db, "a"), await make_user(db, "b")
    s = await entry(db)
    c1 = await chapter(db, s, 1)
    await set_read(db, a.id, c1, True, now=NOW)
    await db.commit()
    assert (await db.get(ReadingState, (b.id, c1.id))) is None


async def test_migration_carries_read_and_bookmarks_by_number_without_activity(db):
    user = await make_user(db)
    old = await entry(db)
    new_source = await add_series(db, OTHER, {**MANGA, "url": "/series/42"})
    new = new_source[0]
    await sync_chapters(db, new, CHAPTERS[:4])  # the target lists 1 to 4 only
    await set_read(db, user.id, await chapter(db, old, 3), True, now=NOW)
    await set_bookmark(db, user.id, await chapter(db, old, 2), True)
    await db.commit()
    events_before = len((await db.execute(select(ReadingEvent))).scalars().all())

    result = await carry_reading_state(db, user.id, old.id, new.id)
    await db.commit()
    assert result.carried_read == 3  # 1, 2 and 3: everything at or below the highest read chapter
    assert result.carried_bookmarks == 1
    assert result.unmatched_old == []  # chapter 5 has no state on the old entry, so nothing to report
    assert (await db.get(ReadingState, (user.id, (await chapter(db, new, 3)).id))).read is True
    assert (await db.get(ReadingState, (user.id, (await chapter(db, new, 4)).id))) is None
    assert len((await db.execute(select(ReadingEvent))).scalars().all()) == events_before


async def test_stats_periods_and_latest(db):
    user = await make_user(db)
    s = await entry(db)
    cs = [await chapter(db, s, i) for i in range(1, 6)]
    # Monday 2026-10-05 (last week), Tuesday 2026-10-13, Wednesday 2026-10-14 (today)
    await set_read(db, user.id, cs[0], True, now=datetime(2026, 9, 20, 9, tzinfo=timezone.utc))  # last month
    await set_read(db, user.id, cs[1], True, now=datetime(2026, 10, 5, 9, tzinfo=timezone.utc))  # last week
    await set_read(db, user.id, cs[2], True, now=datetime(2026, 10, 13, 9, tzinfo=timezone.utc))  # this week
    await set_read(db, user.id, cs[3], True, now=NOW)  # today
    await db.commit()
    st = await stats(db, user.id, today=date(2026, 10, 14))
    assert st.today == 1
    assert st.this_week == 2  # Monday 12th to today, i.e. the 13th and 14th
    assert st.this_month == 3  # October: the 5th, 13th and 14th
    assert st.this_year == 4
    assert st.latest["chapter_number"] == 4.0 and st.latest["series_title"] == "Series X"
    assert [h["day"] for h in st.heatmap] == ["2026-09-20", "2026-10-05", "2026-10-13", "2026-10-14"]
