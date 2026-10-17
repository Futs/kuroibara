"""API v2: catalog settings, refresh and JAR import, proxied to a fake host. No network."""
import json

import httpx
import pytest

from app.core.deps import get_current_user
from app.main import app
from app.sources.deps import get_host_client
from app.sources.host_client import ExtensionHostClient

SEEN = {}


def handler(req: httpx.Request) -> httpx.Response:
    path = req.url.path
    SEEN["last"] = (req.method, path, req.content)
    if path == "/catalog/settings" and req.method == "GET":
        return httpx.Response(200, json={"catalog_url": "https://default.test/index.json", "is_default": True})
    if path == "/catalog/settings" and req.method == "PUT":
        body = json.loads(req.content)
        return httpx.Response(200, json={"catalog_url": body["url"] or "https://default.test/index.json",
                                         "is_default": body["url"] is None})
    if path == "/catalog/refresh":
        return httpx.Response(SEEN.get("refresh_status", 200), json={"extensions": 3} if SEEN.get("refresh_status", 200) == 200 else {"error": "catalog answered HTTP 500"})
    if path.endswith("/import"):
        if req.content.startswith(b"not-a-jar"):
            return httpx.Response(422, json={"error": "not a JAR (zip) file"})
        return httpx.Response(200, json={"module": "en/x", "source": "import", "package": "eu.kanade.tachiyomi.extension.en.x"})
    return httpx.Response(404, json={"error": "no route"})


@pytest.fixture
def api(client):
    SEEN.clear()

    async def fake_client():
        c = ExtensionHostClient("http://host", "tok", transport=httpx.MockTransport(handler))
        try:
            yield c
        finally:
            await c.aclose()

    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": 1, "is_superuser": True})()
    app.dependency_overrides[get_host_client] = fake_client
    yield client
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_host_client, None)


def test_settings_are_proxied(api):
    r = api.get("/api/v2/sources/catalog/settings")
    assert r.status_code == 200 and r.json()["is_default"] is True


def test_only_https_catalogs_are_accepted_by_the_backend(api):
    assert api.put("/api/v2/sources/catalog/settings", json={"url": "http://x.test/i.json"}).status_code == 422
    ok = api.put("/api/v2/sources/catalog/settings", json={"url": "https://x.test/i.json"})
    assert ok.status_code == 200 and ok.json()["catalog_url"] == "https://x.test/i.json"
    assert json.loads(SEEN["last"][2])["url"] == "https://x.test/i.json"


def test_resetting_to_the_default_sends_null(api):
    r = api.put("/api/v2/sources/catalog/settings", json={"url": None})
    assert r.status_code == 200 and r.json()["is_default"] is True


def test_refresh_is_proxied_and_host_errors_pass_through(api):
    assert api.post("/api/v2/sources/catalog/refresh").json()["extensions"] == 3
    SEEN["refresh_status"] = 502
    assert api.post("/api/v2/sources/catalog/refresh").status_code == 502


def test_import_forwards_the_jar_to_the_module_path(api):
    r = api.post("/api/v2/sources/en/x/import", files={"file": ("x.jar", b"PK\x03\x04fake", "application/octet-stream")})
    assert r.status_code == 200, r.text
    method, path, content = SEEN["last"]
    assert (method, path) == ("POST", "/extensions/en/x/import")
    assert content == b"PK\x03\x04fake"
    assert r.json()["source"] == "import"


def test_import_rejects_non_jars_from_the_host(api):
    r = api.post("/api/v2/sources/en/x/import", files={"file": ("x.jar", b"not-a-jar", "application/octet-stream")})
    assert r.status_code == 422 and "not a JAR" in r.json()["detail"]


def test_import_refuses_oversized_uploads_before_forwarding(api):
    big = b"PK" + b"0" * 30_000_001
    r = api.post("/api/v2/sources/en/x/import", files={"file": ("big.jar", big, "application/octet-stream")})
    assert r.status_code == 413
    assert "last" not in SEEN or SEEN["last"][1] != "/extensions/en/x/import"


@pytest.fixture
def regular_user(client):
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": 2, "is_superuser": False})()
    yield client
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": 1, "is_superuser": True})()


def test_regular_users_cannot_change_global_source_state(api, regular_user):
    assert api.put("/api/v2/sources/catalog/settings", json={"url": None}).status_code == 403
    assert api.post("/api/v2/sources/catalog/refresh").status_code == 403
    assert api.post("/api/v2/sources/en/x/import", files={"file": ("x.jar", b"PK", "application/octet-stream")}).status_code == 403
    assert api.post("/api/v2/sources/en/x/install").status_code == 403
    assert api.delete("/api/v2/sources/en/x").status_code == 403
    assert api.post("/api/v2/sources/en/x/enable").status_code == 403
    assert api.post("/api/v2/sources/en/x/disable").status_code == 403


def test_regular_users_can_still_read_and_browse(api, regular_user):
    assert api.get("/api/v2/sources/catalog/settings").status_code == 200
    # The fake host has no search route, so the proxy's 404 is expected. The point is that access is not refused.
    assert api.post("/api/v2/sources/en/x/search?q=one").status_code not in (401, 403)
