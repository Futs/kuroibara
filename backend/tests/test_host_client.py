"""Extension host client, against an httpx MockTransport (no network, no database)."""
import asyncio
import json

import httpx
import pytest

from app.sources.host_client import ExtensionHostClient, ExtensionHostError

TOKEN = "t0k"


def run(coro):
    return asyncio.run(coro)


def make_client(handler):
    return ExtensionHostClient("http://extension-host:8800", TOKEN, transport=httpx.MockTransport(handler))


def test_requires_a_token():
    with pytest.raises(ExtensionHostError):
        ExtensionHostClient("http://x", "")


def test_sends_bearer_token_and_returns_json():
    seen = {}

    def handler(req):
        seen["auth"] = req.headers.get("authorization")
        return httpx.Response(200, json={"modules": {}})

    async def go():
        async with make_client(handler) as c:
            return await c.catalog()

    assert run(go()) == {"modules": {}}
    assert seen["auth"] == f"Bearer {TOKEN}"


def test_module_with_slash_is_kept_as_path_segments():
    seen = {}

    def handler(req):
        seen["path"] = req.url.path
        seen["params"] = dict(req.url.params)
        return httpx.Response(200, json={"module": "en/mangakatana"})

    async def go():
        async with make_client(handler) as c:
            return await c.install("en/mangakatana", source="upstream")

    run(go())
    assert seen["path"] == "/extensions/en/mangakatana/install"
    assert seen["params"] == {"source": "upstream"}


def test_install_with_pinned_version_and_hash():
    seen = {}

    def handler(req):
        seen["params"] = dict(req.url.params)
        return httpx.Response(200, json={})

    async def go():
        async with make_client(handler) as c:
            await c.install("en/x", source="local", version_code=3, hash="abc")

    run(go())
    assert seen["params"] == {"source": "local", "version_code": "3", "hash": "abc"}


def test_test_passes_query_and_returns_health():
    seen = {}

    def handler(req):
        seen["method"] = req.method
        seen["q"] = req.url.params.get("q")
        return httpx.Response(200, json={"health": {"ok": False, "error_class": "webview-needed"}})

    async def go():
        async with make_client(handler) as c:
            return await c.test("en/allanime", query="one piece")

    body = run(go())
    assert seen == {"method": "POST", "q": "one piece"}
    assert body["health"]["error_class"] == "webview-needed"


def test_error_status_raises_with_host_message():
    def handler(req):
        return httpx.Response(502, json={"error": "sha256 mismatch for x"})

    async def go():
        async with make_client(handler) as c:
            await c.install("en/x")

    with pytest.raises(ExtensionHostError) as e:
        run(go())
    assert e.value.status == 502
    assert "sha256 mismatch" in e.value.message


def test_unreachable_host_raises_and_health_is_false():
    def handler(req):
        raise httpx.ConnectError("refused", request=req)

    async def go():
        async with make_client(handler) as c:
            return await c.health(), await c.catalog()

    with pytest.raises(ExtensionHostError):
        run(go())

    async def health_only():
        async with make_client(handler) as c:
            return await c.health()

    assert run(health_only()) is False


def test_uninstall_enable_disable_use_the_right_verbs():
    calls = []

    def handler(req):
        calls.append((req.method, req.url.path))
        return httpx.Response(200, json={})

    async def go():
        async with make_client(handler) as c:
            await c.uninstall("en/x")
            await c.enable("en/x")
            await c.disable("en/x")

    run(go())
    assert calls == [
        ("DELETE", "/extensions/en/x"),
        ("POST", "/extensions/en/x/enable"),
        ("POST", "/extensions/en/x/disable"),
    ]
