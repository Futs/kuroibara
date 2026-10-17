"""API v2: queue chapters for a series, list them, and run the queue. Fake host, real test database."""
import json
import os

import httpx
import pytest

from app.core.config import settings
from app.core.deps import get_current_user
from app.main import app
from app.sources.deps import get_host_client
from app.sources.host_client import ExtensionHostClient

JPEG = b"\xff\xd8\xff\xe0" + b"x" * 64

INSTALLED = {"extensions": {"en/mangakatana": {
    "module": "en/mangakatana", "enabled": True, "source": "upstream",
    "package": "eu.kanade.tachiyomi.extension.en.mangakatana"}}}


def host_handler(req: httpx.Request) -> httpx.Response:
    path = req.url.path
    if path == "/extensions":
        return httpx.Response(200, json=INSTALLED)
    if path.endswith("/details"):
        return httpx.Response(200, json={"manga": {"url": "/manga/x", "title": "Series X"}, "chapters": [
            {"url": "/c/1", "name": "Chapter 1", "chapter_number": 1},
            {"url": "/c/2", "name": "Chapter 2", "chapter_number": 2},
        ]})
    if path.endswith("/pages"):
        return httpx.Response(200, json={"pages": [
            {"index": 0, "url": "", "image_url": "https://img.test/0"},
            {"index": 1, "url": "", "image_url": "https://img.test/1"},
        ]})
    if path.endswith("/image"):
        return httpx.Response(200, content=JPEG, headers={"Content-Type": "image/jpeg", "X-Upstream-Status": "200"})
    return httpx.Response(404, json={"error": "no route"})


@pytest.fixture
def api(client, db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SOURCE_DOWNLOAD_DIR", str(tmp_path / "dl"))

    async def fake_client():
        c = ExtensionHostClient("http://host", "tok", transport=httpx.MockTransport(host_handler))
        try:
            yield c
        finally:
            await c.aclose()

    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": 1})()
    app.dependency_overrides[get_host_client] = fake_client
    yield client
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_host_client, None)


def make_series(api):
    body = {"module": "en/mangakatana", "source_name": "MangaKatana", "source_lang": "en",
            "manga": {"url": "/manga/x", "title": "Series X"}}
    r = api.post("/api/v2/series", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_enqueue_explicit_chapters(api):
    sid = make_series(api)
    r = api.post(f"/api/v2/series/{sid}/downloads", json={"chapters": [{"url": "/c/1", "name": "Chapter 1"}]})
    assert r.status_code == 202, r.text
    assert r.json()["queued"] == 1
    again = api.post(f"/api/v2/series/{sid}/downloads", json={"chapters": [{"url": "/c/1", "name": "Chapter 1"}]})
    assert again.json()["queued"] == 0


def test_enqueue_all_chapters_uses_the_source_list(api):
    sid = make_series(api)
    r = api.post(f"/api/v2/series/{sid}/downloads", json={})
    assert r.json()["queued"] == 2
    listed = api.get(f"/api/v2/series/{sid}/downloads").json()["items"]
    assert [i["chapter_url"] for i in listed] == ["/c/1", "/c/2"]
    assert all(i["status"] == "queued" for i in listed)


def test_process_downloads_chapters_to_cbz(api):
    sid = make_series(api)
    api.post(f"/api/v2/series/{sid}/downloads", json={"chapters": [{"url": "/c/1", "name": "Chapter 1"}]})
    r = api.post("/api/v2/series/downloads/process?limit=5")
    assert r.status_code == 200, r.text
    assert r.json() == {"attempted": 1, "downloaded": 1, "failed": 0}
    item = api.get(f"/api/v2/series/{sid}/downloads").json()["items"][0]
    assert item["status"] == "downloaded" and item["page_count"] == 2
    assert item["path"].endswith("Chapter 1.cbz") and os.path.exists(item["path"])


def test_unknown_series_is_404(api):
    r = api.post("/api/v2/series/00000000-0000-0000-0000-000000000000/downloads", json={})
    assert r.status_code == 404
