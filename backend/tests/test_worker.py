"""Source worker: atomic claims across sessions, startup recovery, a full batch, and folder naming.
Uses the test database and a fake host. Sessions are real, separate ones, so the row locks are real."""
import os

import httpx
from sqlalchemy import select

from app.models.extension_series import Series, SourceDownload
from app.sources.download_worker import SourceDownloadWorker, series_folder
from app.sources.host_client import ExtensionHostClient
from app.sources.series_service import SourceRef, add_series
from app.sources.worker_main import Worker
from tests.conftest import TestingAsyncSessionLocal
from tests.test_download_worker import FakeHost, MANGA, SOURCE

import pytest


async def seed_queue(chapters: int, title: str = "Series X", manga_url: str = "/manga/x"):
    async with TestingAsyncSessionLocal() as db:
        series, _ = await add_series(db, SOURCE, {**MANGA, "title": title, "url": manga_url})
        await db.commit()
        worker = SourceDownloadWorker(
            ExtensionHostClient("http://h", "t", transport=httpx.MockTransport(FakeHost().handler)), "/tmp/unused")
        await worker.enqueue(db, series, SOURCE.module,
                             [{"url": f"/c/{i}", "name": f"Chapter {i}", "chapter_number": i}
                              for i in range(1, chapters + 1)])
        await db.commit()
        return series.id


async def test_two_sessions_never_claim_the_same_row(db):
    await seed_queue(3)
    w = SourceDownloadWorker(None, "/tmp/unused", worker_id="a")
    b = SourceDownloadWorker(None, "/tmp/unused", worker_id="b")
    async with TestingAsyncSessionLocal() as sa, TestingAsyncSessionLocal() as sb:
        claimed_a = await w.claim_next(sa, limit=2)  # locked, not yet committed
        claimed_b = await b.claim_next(sb, limit=5)  # skips the rows A has locked
        ids_a = {r.id for r in claimed_a}
        ids_b = {r.id for r in claimed_b}
        assert len(ids_a) == 2 and len(ids_b) == 1
        assert ids_a.isdisjoint(ids_b)
        await sa.commit()
        await sb.commit()
    async with TestingAsyncSessionLocal() as s:
        statuses = (await s.execute(select(SourceDownload.status))).scalars().all()
        assert sorted(statuses) == ["downloading"] * 3
        assert await SourceDownloadWorker(None, "/x").claim_next(s, limit=5) == []


async def test_a_claimed_row_records_its_worker(db):
    await seed_queue(1)
    w = SourceDownloadWorker(None, "/tmp/unused", worker_id="worker-7")
    async with TestingAsyncSessionLocal() as s:
        rows = await w.claim_next(s, limit=1)
        await s.commit()
        assert rows[0].claimed_by == "worker-7" and rows[0].claimed_at is not None
        assert rows[0].attempts == 1


async def test_startup_puts_orphaned_downloads_back(db):
    await seed_queue(2)
    async with TestingAsyncSessionLocal() as s:
        rows = (await s.execute(select(SourceDownload))).scalars().all()
        for r in rows:
            r.status = "downloading"
            r.claimed_by = "dead-worker"
        await s.commit()
    host = ExtensionHostClient("http://h", "t", transport=httpx.MockTransport(FakeHost().handler))
    worker = Worker(TestingAsyncSessionLocal, host, "/tmp/unused")
    assert await worker.startup() == 2
    async with TestingAsyncSessionLocal() as s:
        statuses = (await s.execute(select(SourceDownload.status))).scalars().all()
        assert sorted(statuses) == ["queued", "queued"]


async def test_run_once_downloads_a_claimed_batch(db, tmp_path):
    await seed_queue(2)
    host = ExtensionHostClient("http://h", "t", transport=httpx.MockTransport(FakeHost().handler))
    worker = Worker(TestingAsyncSessionLocal, host, str(tmp_path), parallel_sources=5, parallel_pages=3)
    handled = await worker.run_once()
    assert handled == 2
    async with TestingAsyncSessionLocal() as s:
        rows = (await s.execute(select(SourceDownload))).scalars().all()
        assert all(r.status == "downloaded" and os.path.exists(r.path) for r in rows)
    assert await worker.run_once() == 0  # nothing left


async def test_stop_request_ends_the_run_loop(db, tmp_path):
    host = ExtensionHostClient("http://h", "t", transport=httpx.MockTransport(FakeHost().handler))
    worker = Worker(TestingAsyncSessionLocal, host, str(tmp_path), poll_seconds=0.01)
    worker.request_stop()
    await worker.run()  # returns at once instead of polling forever


async def test_same_title_different_series_get_different_folders(db):
    async with TestingAsyncSessionLocal() as s:
        a, _ = await add_series(s, SOURCE, {**MANGA, "url": "/manga/a"})
        b, _ = await add_series(s, SOURCE, {**MANGA, "url": "/manga/b"})
        await s.commit()
        assert a.title == b.title
        assert series_folder(a) != series_folder(b)
        assert series_folder(a).startswith("Series X [") and len(series_folder(a)) == len("Series X [") + 9
