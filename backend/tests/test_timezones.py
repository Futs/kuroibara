"""Time zones: resolution order, local days at the boundaries, per-zone stats, and the settings API."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import httpx
import pytest
from sqlalchemy import select

from app.core.deps import get_current_user
from app.core.timezones import UTC, effective_zone, local_day, parse_zone, server_zone
from app.main import app
from app.models.reading import ReadingEvent, UserDayActivity
from app.models.user import User
from app.sources.reading_service import set_read, stats, sync_chapters
from app.sources.series_service import SourceRef, add_series

AMS = ZoneInfo("Europe/Amsterdam")
NY = ZoneInfo("America/New_York")
TOKYO = ZoneInfo("Asia/Tokyo")
SRC = SourceRef(module="en/mangakatana", package="eu.kanade.tachiyomi.extension.en.mangakatana",
                name="MangaKatana", lang="en", source_id=None)
# 23:30 UTC on 14 October: already the 15th in Amsterdam and Tokyo, still the 14th in New York
LATE = datetime(2026, 10, 14, 23, 30, tzinfo=timezone.utc)


def test_parse_zone_accepts_iana_and_rejects_nonsense():
    assert str(parse_zone("Europe/Amsterdam")) == "Europe/Amsterdam"
    with pytest.raises(ValueError):
        parse_zone("Not/AZone")
    with pytest.raises(ValueError):
        parse_zone("   ")


def test_resolution_order_user_then_server_then_utc(monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Berlin")
    assert effective_zone("Asia/Tokyo") == (TOKYO, "user")
    assert effective_zone(None) == (ZoneInfo("Europe/Berlin"), "server")
    assert effective_zone("Bad/Zone")[1] == "server"  # a stored name that is no longer valid falls back
    monkeypatch.delenv("TZ")
    assert effective_zone(None) == (UTC, "utc")
    monkeypatch.setenv("TZ", "Nope/Nope")
    assert server_zone() is UTC


def test_local_day_moves_with_the_zone():
    assert local_day(LATE, AMS) == date(2026, 10, 15)
    assert local_day(LATE, TOKYO) == date(2026, 10, 15)
    assert local_day(LATE, NY) == date(2026, 10, 14)
    assert local_day(LATE.replace(tzinfo=None), NY) == date(2026, 10, 14)  # naive is taken as UTC


async def make_user(db, zone_name):
    user = User(username=f"tz-{zone_name.replace('/', '-').lower()}", email=f"{zone_name.replace('/', '-').lower()}@t.test",
                hashed_password="x", is_active=True, timezone=zone_name)
    db.add(user)
    await db.flush()
    return user


async def test_event_and_rollup_use_the_users_local_day(db):
    user = await make_user(db, "Europe/Amsterdam")
    s, _ = await add_series(db, SRC, {"url": "/m/1", "title": "T"})
    await sync_chapters(db, s, [{"url": "/c/1", "name": "C1", "chapter_number": 1.0}])
    from app.models.reading import SeriesChapter
    ch = (await db.execute(select(SeriesChapter))).scalar_one()
    await set_read(db, user.id, ch, True, now=LATE, zone=AMS)
    await db.commit()
    ev = (await db.execute(select(ReadingEvent))).scalar_one()
    assert ev.local_day == date(2026, 10, 15) and ev.at == LATE  # UTC kept, local day stored
    day = (await db.execute(select(UserDayActivity))).scalar_one()
    assert day.day == date(2026, 10, 15) and day.chapters_read == 1


async def test_today_in_stats_follows_the_zone(db):
    user = await make_user(db, "America/New_York")
    s, _ = await add_series(db, SRC, {"url": "/m/2", "title": "T"})
    await sync_chapters(db, s, [{"url": "/c/1", "name": "C1", "chapter_number": 1.0}])
    from app.models.reading import SeriesChapter
    ch = (await db.execute(select(SeriesChapter))).scalar_one()
    await set_read(db, user.id, ch, True, now=LATE, zone=NY)
    await db.commit()
    now = datetime(2026, 10, 14, 23, 45, tzinfo=timezone.utc)
    assert (await stats(db, user.id, zone=NY, now=now)).today == 1  # still the 14th in New York
    assert (await stats(db, user.id, zone=AMS, now=now)).today == 0  # already the 15th in Amsterdam


@pytest.fixture
async def api(client, db):
    user = await make_user(db, "Asia/Tokyo")
    await db.commit()
    user_id = user.id

    class Current:
        id = user_id
        timezone = "Asia/Tokyo"

    app.dependency_overrides[get_current_user] = lambda: Current()
    yield client
    app.dependency_overrides.pop(get_current_user, None)


def test_settings_show_the_effective_zone_and_its_source(api, monkeypatch):
    monkeypatch.delenv("TZ", raising=False)
    body = api.get("/api/v2/me/settings").json()
    assert body["effective_timezone"] == "Asia/Tokyo" and body["timezone_source"] == "user"


def test_setting_a_zone_is_validated_and_clearing_falls_back(api):
    assert api.put("/api/v2/me/settings/timezone", json={"timezone": "Not/Zone"}).status_code == 422
    ok = api.put("/api/v2/me/settings/timezone", json={"timezone": "Europe/Amsterdam"})
    assert ok.status_code == 200 and ok.json()["effective_timezone"] == "Europe/Amsterdam"
    cleared = api.put("/api/v2/me/settings/timezone", json={"timezone": None}).json()
    assert cleared["timezone"] is None and cleared["timezone_source"] in ("server", "utc")
