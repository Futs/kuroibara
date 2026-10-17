"""API v2: chapters with per-user state, read/bookmark/progress, stats, and read-state carry on migrate."""
import json

import httpx
import pytest

from app.core.deps import get_current_user
from app.main import app
from app.models.user import User
from app.sources.deps import get_host_client
from app.sources.host_client import ExtensionHostClient

INSTALLED = {"extensions": {
    "en/mangakatana": {"module": "en/mangakatana", "enabled": True, "package": "eu.kanade.tachiyomi.extension.en.mangakatana"},
    "en/toonily": {"module": "en/toonily", "enabled": True, "package": "eu.kanade.tachiyomi.extension.en.toonily"},
}}
CHAPTERS = [{"url": f"/c/{i}", "name": f"Chapter {i}", "chapter_number": float(i)} for i in range(1, 4)]


def host_handler(req):
    if req.url.path == "/extensions":
        return httpx.Response(200, json=INSTALLED)
    if req.url.path.endswith("/details"):
        url = json.loads(req.content)["url"]
        return httpx.Response(200, json={"manga": {"url": url, "title": "Series X"}, "chapters": CHAPTERS})
    return httpx.Response(404, json={"error": "no route"})


@pytest.fixture
async def api(client, db):
    user = User(username="api-reader", email="api-reader@example.test", hashed_password="x", is_active=True)
    db.add(user)
    await db.commit()
    user_id = user.id

    async def fake_client():
        c = ExtensionHostClient("http://host", "tok", transport=httpx.MockTransport(host_handler))
        try:
            yield c
        finally:
            await c.aclose()

    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": user_id})()
    app.dependency_overrides[get_host_client] = fake_client
    yield client
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_host_client, None)


def add(api, module="en/mangakatana", url="/manga/x"):
    body = {"module": module, "source_name": "S", "source_lang": "en",
            "manga": {"url": url, "title": "Series X"}}
    r = api.post("/api/v2/series", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def chapters(api, sid):
    return api.get(f"/api/v2/series/{sid}/chapters").json()["items"]


def test_chapters_come_from_the_source_newest_first_with_default_state(api):
    sid = add(api)
    items = chapters(api, sid)
    assert [c["chapter_number"] for c in items] == [3.0, 2.0, 1.0]
    assert all(c["read"] is False and c["bookmark"] is False and c["last_page"] is None for c in items)


def test_read_then_unread_updates_state_and_stats(api):
    sid = add(api)
    cid = chapters(api, sid)[0]["id"]
    r = api.put(f"/api/v2/series/{sid}/chapters/{cid}/read", json={"read": True})
    assert r.status_code == 200 and r.json()["read"] is True
    stats = api.get("/api/v2/reading/stats").json()
    assert stats["today"] == 1 and stats["latest"]["chapter_number"] == 3.0
    api.put(f"/api/v2/series/{sid}/chapters/{cid}/read", json={"read": False})
    assert api.get("/api/v2/reading/stats").json()["today"] == 0


def test_bookmark_and_progress_show_in_the_chapter_list(api):
    sid = add(api)
    cid = chapters(api, sid)[1]["id"]
    api.put(f"/api/v2/series/{sid}/chapters/{cid}/bookmark", json={"bookmark": True})
    api.put(f"/api/v2/series/{sid}/chapters/{cid}/progress", json={"page": 7})
    item = next(c for c in chapters(api, sid) if c["id"] == cid)
    assert item["bookmark"] is True and item["last_page"] == 7 and item["read"] is False


def test_chapter_from_another_series_is_404(api):
    a = add(api, url="/manga/a")
    b = add(api, url="/manga/b")
    cid = chapters(api, a)[0]["id"]
    assert api.put(f"/api/v2/series/{b}/chapters/{cid}/read", json={"read": True}).status_code == 404


def test_migrate_carries_read_state_by_chapter_number(api):
    old = add(api, url="/manga/old")
    cid = next(c["id"] for c in chapters(api, old) if c["chapter_number"] == 2.0)
    api.put(f"/api/v2/series/{old}/chapters/{cid}/read", json={"read": True})
    body = {"module": "en/toonily", "source_name": "Toonily", "source_lang": "en",
            "manga": {"url": "/series/new", "title": "Series X"}}
    r = api.post(f"/api/v2/series/{old}/migrate", json=body)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["reading"]["carried_read"] == 2  # chapters 1 and 2: at or below the highest read chapter
    new = data["to"]["id"]
    read_now = {c["chapter_number"]: c["read"] for c in chapters(api, new)}
    assert read_now == {3.0: False, 2.0: True, 1.0: True}
    assert api.get("/api/v2/reading/stats").json()["today"] == 1  # only the original read, not the carry


def test_migrate_can_skip_read_state(api):
    old = add(api, url="/manga/old2")
    cid = chapters(api, old)[0]["id"]
    api.put(f"/api/v2/series/{old}/chapters/{cid}/read", json={"read": True})
    body = {"module": "en/toonily", "source_name": "Toonily", "source_lang": "en",
            "manga": {"url": "/series/new2", "title": "Series X"}, "carry_read_state": False}
    data = api.post(f"/api/v2/series/{old}/migrate", json=body).json()
    assert data["reading"] is None
    assert all(c["read"] is False for c in chapters(api, data["to"]["id"]))
