"""API v2: sources (proxy to the extension host) and series (added from sources). Needs the test database.

The extension host is replaced by an httpx MockTransport, so no network is used.
"""
import json

import httpx
import pytest

from app.core.deps import get_current_user
from app.main import app
from app.sources.deps import get_host_client
from app.sources.host_client import ExtensionHostClient

MANGA = {
    "url": "/manga/one-piece.49",
    "title": "One Piece",
    "author": "Oda Eiichiro",
    "genre": "Action, Adventure",
    "status": 1,
    "description": "Pirates.",
    "thumbnail_url": "https://example.test/cover.jpg",
}

INSTALLED = {
    "extensions": {
        "en/mangakatana": {"module": "en/mangakatana", "enabled": True, "source": "upstream",
                           "package": "eu.kanade.tachiyomi.extension.en.mangakatana", "version_code": 106001},
        "en/off": {"module": "en/off", "enabled": False, "source": "upstream",
                   "package": "eu.kanade.tachiyomi.extension.en.off"},
    }
}


def fake_host_handler(down: bool = False):
    def handler(req: httpx.Request) -> httpx.Response:
        if down:
            raise httpx.ConnectError("refused", request=req)
        path = req.url.path
        if path == "/extensions":
            return httpx.Response(200, json=INSTALLED)
        if path == "/extensions/en/mangakatana/search":
            return httpx.Response(200, json={"source": "MangaKatana", "lang": "en", "has_next": False,
                                             "mangas": [{"url": MANGA["url"], "title": MANGA["title"]}]})
        if path == "/extensions/en/mangakatana/details":
            body = json.loads(req.content)
            assert body["url"] == MANGA["url"]
            return httpx.Response(200, json={"manga": MANGA, "chapters": []})
        if path == "/extensions/en/mangakatana/install":
            return httpx.Response(200, json={"module": "en/mangakatana", "source": "upstream"})
        if path == "/extensions/en/missing/details":
            return httpx.Response(404, json={"error": "not installed: en/missing"})
        return httpx.Response(404, json={"error": "no route"})
    return handler


@pytest.fixture
def host_down():
    return False


@pytest.fixture
def api(client, db, host_down):
    """TestClient with the DB override from conftest, a fake user, and the fake host."""
    async def fake_client():
        c = ExtensionHostClient("http://host", "tok", transport=httpx.MockTransport(fake_host_handler(host_down)))
        try:
            yield c
        finally:
            await c.aclose()

    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": 1})()
    app.dependency_overrides[get_host_client] = fake_client
    yield client
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_host_client, None)


def add_body(**over):
    body = {
        "module": "en/mangakatana",
        "source_name": "MangaKatana",
        "source_lang": "en",
        "source_id": "3170561626848540385",
        "manga": MANGA,
    }
    body.update(over)
    return body


def test_add_series_takes_package_from_host_and_stores_provider_metadata(api):
    r = api.post("/api/v2/series", json=add_body())
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "One Piece"
    assert data["package"] == "eu.kanade.tachiyomi.extension.en.mangakatana"
    assert data["module"] == "en/mangakatana" and data["in_library"] is True
    assert data["metadata"]["current"]["title"] == {"value": "One Piece", "origin": "provider"}
    assert data["metadata"]["current"]["authors"]["value"] == ["Oda Eiichiro"]
    assert data["metadata"]["has_mangaupdates"] is False


def test_adding_the_same_title_again_returns_the_existing_series(api):
    first = api.post("/api/v2/series", json=add_body()).json()
    r = api.post("/api/v2/series", json=add_body())
    assert r.status_code == 200
    assert r.json()["id"] == first["id"]


def test_not_installed_or_disabled_sources_are_refused(api):
    assert api.post("/api/v2/series", json=add_body(module="en/nope")).status_code == 404
    assert api.post("/api/v2/series", json=add_body(module="en/off")).status_code == 409


def test_manga_without_url_or_title_is_rejected(api):
    assert api.post("/api/v2/series", json=add_body(manga={"title": ""})).status_code == 422


def test_get_and_revert_series(api):
    created = api.post("/api/v2/series", json=add_body()).json()
    got = api.get(f"/api/v2/series/{created['id']}")
    assert got.status_code == 200 and got.json()["module"] == "en/mangakatana"
    reverted = api.post(f"/api/v2/series/{created['id']}/revert")
    assert reverted.status_code == 200
    assert reverted.json()["metadata"]["current"]["title"]["origin"] == "provider"
    assert api.get("/api/v2/series/00000000-0000-0000-0000-000000000000").status_code == 404


def test_migrate_moves_the_title_and_hides_the_old_entry(api):
    created = api.post("/api/v2/series", json=add_body()).json()
    body = {"module": "en/mangakatana", "source_name": "MangaKatana", "source_lang": "en",
            "manga": {**MANGA, "url": "/manga/other"}}
    r = api.post(f"/api/v2/series/{created['id']}/migrate", json=body)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["from"]["in_library"] is False
    assert data["to"]["in_library"] is True and data["to"]["id"] != created["id"]
    listed = api.get("/api/v2/series").json()["items"]
    assert [i["id"] for i in listed] == [data["to"]["id"]]
    removed = api.get("/api/v2/series?in_library=false").json()["items"]
    assert [i["id"] for i in removed] == [created["id"]]


def test_migrate_to_the_same_title_is_409(api):
    created = api.post("/api/v2/series", json=add_body()).json()
    body = {"module": "en/mangakatana", "source_name": "MangaKatana", "source_lang": "en", "manga": MANGA}
    assert api.post(f"/api/v2/series/{created['id']}/migrate", json=body).status_code == 409


def test_list_series_paginates(api):
    api.post("/api/v2/series", json=add_body())
    r = api.get("/api/v2/series?limit=10&offset=0")
    assert r.status_code == 200 and r.json()["total"] >= 1


def test_browse_search_proxies_through_a_slashed_module(api):
    r = api.post("/api/v2/sources/en/mangakatana/search?q=one")
    assert r.status_code == 200, r.text
    assert r.json()["mangas"][0]["title"] == "One Piece"


def test_details_proxies_and_host_404_passes_through(api):
    ok = api.post("/api/v2/sources/en/mangakatana/details", json={"url": MANGA["url"]})
    assert ok.status_code == 200 and ok.json()["manga"]["title"] == "One Piece"
    missing = api.post("/api/v2/sources/en/missing/details", json={"url": "/x"})
    assert missing.status_code == 404


def test_installed_and_catalog_routes_pass_host_json(api):
    assert api.get("/api/v2/sources/installed").json()["extensions"]["en/mangakatana"]["enabled"] is True
    # The fake host has no upstream route, so the catalog 404s through the proxy.
    assert api.get("/api/v2/sources/catalog").status_code == 404


def test_install_forwards_source_choice(api):
    r = api.post("/api/v2/sources/en/mangakatana/install?source=upstream")
    assert r.status_code == 200 and r.json()["source"] == "upstream"
    assert api.post("/api/v2/sources/en/mangakatana/install?source=bogus").status_code == 422


@pytest.mark.parametrize("host_down", [True])
def test_host_unreachable_is_503(api):
    assert api.get("/api/v2/sources/installed").status_code == 503
    assert api.post("/api/v2/series", json=add_body()).status_code == 503
