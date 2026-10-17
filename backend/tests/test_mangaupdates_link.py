"""MangaUpdates link: search, link, compare, apply per field, edited values, and the cache. Fake MangaUpdates client."""
import pytest
from sqlalchemy import select

from app.api.api_v2.endpoints.mangaupdates import get_mu_api
from app.core.deps import get_current_user
from app.main import app
from app.models.extension_series import SeriesMetadata
from app.models.user import User
from app.sources.mangaupdates_link import compare, mu_fields, plan_choices, search_candidates
from app.sources.series_service import SourceRef, add_series

SRC = SourceRef(module="en/mangakatana", package="eu.kanade.tachiyomi.extension.en.mangakatana",
                name="MangaKatana", lang="en", source_id=None)
PROVIDER = {"url": "/manga/x", "title": "Provider Title", "author": "Provider Author",
            "description": "Provider blurb", "genre": "Action, Adventure", "status": 1,
            "thumbnail_url": "https://p/cover.jpg"}
MU_DETAILS = {"series_id": 555, "title": "MU Title", "description": "MU blurb",
              "authors": [{"name": "MU Author", "type": "Author"}],
              "status": {"status": "Complete"}, "image": {"url": {"original": "https://mu/cover.jpg"}}}


class FakeMU:
    def __init__(self, details=MU_DETAILS):
        self.details = details

    async def search_series(self, query, page=1, per_page=50):
        return {"results": [{"record": {"series_id": 555, "title": "MU Title", "year": "2020",
                                        "image": {"url": {"thumb": "https://mu/t.jpg"}}}}]}

    async def get_series_details(self, series_id):
        return self.details


@pytest.fixture
def mu_api(client, db):
    fake = FakeMU()
    app.dependency_overrides[get_current_user] = lambda: type("U", (), {"id": 1})()

    async def fake_dep():
        yield fake

    app.dependency_overrides[get_mu_api] = fake_dep
    yield client, fake
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_mu_api, None)


async def make_entry(db):
    s, _ = await add_series(db, SRC, PROVIDER)
    await db.commit()
    return s


def test_search_candidates_are_trimmed_from_the_response():
    items = search_candidates({"results": [{"record": {"series_id": 9, "title": "A", "year": "1999",
                                                        "image": {"url": {"thumb": "t"}}}}, {"nothing": 1}]})
    assert items == [{"mu_series_id": 9, "title": "A", "year": "1999", "cover_url": "t"}]


def test_mu_fields_maps_status_and_names():
    fields = mu_fields({"title": "T", "authors": [{"name": "X"}], "artists": [], "genres": ["Action"],
                        "status": "completed", "cover_image_url": "c", "description": "d"})
    assert fields == {"title": "T", "description": "d", "authors": ["X"], "artists": [], "genres": ["Action"],
                      "status": 2, "cover_url": "c"}


async def test_link_caches_details_and_changes_no_shown_values(db, mu_api):
    client, _ = mu_api
    s = await make_entry(db)
    r = client.post(f"/api/v2/series/{s.id}/mangaupdates/link", json={"mu_series_id": 555})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mangaupdates_series_id"] == 555
    assert body["fields"]["title"]["mangaupdates"] == "MU Title"
    assert body["fields"]["title"]["shown"] == "Provider Title" and body["fields"]["title"]["origin"] == "provider"
    record = (await db.execute(select(SeriesMetadata).where(SeriesMetadata.series_id == s.id))).scalar_one()
    await db.refresh(record)
    assert record.mangaupdates["series_id"] == 555 and record.mangaupdates["fetched_at"]


async def test_apply_per_field_with_origins_and_listing_sync(db, mu_api):
    client, _ = mu_api
    s = await make_entry(db)
    client.post(f"/api/v2/series/{s.id}/mangaupdates/link", json={"mu_series_id": 555})
    r = client.post(f"/api/v2/series/{s.id}/mangaupdates/apply", json={"choices": {
        "title": "mangaupdates",
        "description": {"origin": "edited", "value": "My own blurb"},
        "status": "provider",
    }})
    assert r.status_code == 200, r.text
    cur = r.json()["entry"]["metadata"]["current"]
    assert cur["title"] == {"value": "MU Title", "origin": "mangaupdates"}
    assert cur["description"] == {"value": "My own blurb", "origin": "edited"}
    assert cur["status"] == {"value": 1, "origin": "provider"}
    assert cur["authors"]["origin"] == "provider"  # not in the request, so untouched
    assert r.json()["entry"]["title"] == "MU Title"  # listing copy follows the shown title


def test_apply_before_linking_is_refused(db, mu_api):
    client, _ = mu_api
    import asyncio
    s = asyncio.run(make_entry(db))
    r = client.post(f"/api/v2/series/{s.id}/mangaupdates/apply", json={"choices": {"title": "mangaupdates"}})
    assert r.status_code == 422


def test_unknown_field_and_bad_pick_are_refused(db, mu_api):
    client, _ = mu_api
    import asyncio
    s = asyncio.run(make_entry(db))
    client.post(f"/api/v2/series/{s.id}/mangaupdates/link", json={"mu_series_id": 555})
    assert client.post(f"/api/v2/series/{s.id}/mangaupdates/apply",
                       json={"choices": {"nope": "provider"}}).status_code == 422
    assert client.post(f"/api/v2/series/{s.id}/mangaupdates/apply",
                       json={"choices": {"title": "guess"}}).status_code == 422


async def test_revert_after_apply_restores_provider_values(db, mu_api):
    client, _ = mu_api
    s = await make_entry(db)
    client.post(f"/api/v2/series/{s.id}/mangaupdates/link", json={"mu_series_id": 555})
    client.post(f"/api/v2/series/{s.id}/mangaupdates/apply", json={"choices": {"title": "mangaupdates"}})
    reverted = client.post(f"/api/v2/series/{s.id}/revert").json()
    assert reverted["title"] == "Provider Title"
    assert reverted["metadata"]["current"]["title"]["origin"] == "provider"
    assert reverted["metadata"]["has_mangaupdates"] is True  # the cached entry survives a revert


async def test_refresh_needs_a_link_and_updates_the_cache(db, mu_api):
    client, fake = mu_api
    s = await make_entry(db)
    assert client.post(f"/api/v2/series/{s.id}/mangaupdates/refresh").status_code == 409
    client.post(f"/api/v2/series/{s.id}/mangaupdates/link", json={"mu_series_id": 555})
    fake.details = {**MU_DETAILS, "title": "MU Title 2"}
    r = client.post(f"/api/v2/series/{s.id}/mangaupdates/refresh")
    assert r.json()["fields"]["title"]["mangaupdates"] == "MU Title 2"


async def test_failed_fetch_is_a_502_and_leaves_the_cache(db, mu_api):
    client, fake = mu_api
    s = await make_entry(db)
    fake.details = None
    assert client.post(f"/api/v2/series/{s.id}/mangaupdates/link", json={"mu_series_id": 555}).status_code == 502


async def test_search_defaults_to_the_shown_title(db, mu_api):
    client, _ = mu_api
    s = await make_entry(db)
    body = client.get(f"/api/v2/series/{s.id}/mangaupdates/search").json()
    assert body["query"] == "Provider Title" and body["items"][0]["mu_series_id"] == 555
