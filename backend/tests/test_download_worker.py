"""Source download worker against a fake host and the test database. Sleeps are no-ops."""
import os
import zipfile

import httpx
import pytest
from sqlalchemy import select

from app.models.extension_series import Series, SourceDownload
from app.sources.download_worker import SourceDownloadWorker, image_extension
from app.sources.host_client import ExtensionHostClient
from app.sources.series_service import SourceRef, add_series

JPEG = b"\xff\xd8\xff\xe0" + b"x" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"y" * 64

SOURCE = SourceRef(module="en/mangakatana", package="eu.kanade.tachiyomi.extension.en.mangakatana",
                   name="MangaKatana", lang="en", source_id=None)
MANGA = {"url": "/manga/x", "title": "Series X"}


class FakeHost:
    """Serves a page list of three pages. `fail_plan[index]` is the number of image failures before success."""

    def __init__(self, fail_plan=None, pages=3):
        self.fail_plan = dict(fail_plan or {})
        self.pages = pages
        self.image_calls = {}
        self.page_list_calls = 0

    def handler(self, req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/pages"):
            self.page_list_calls += 1
            return httpx.Response(200, json={"pages": [
                {"index": i, "url": "", "image_url": f"https://img.test/{i}.bin"} for i in range(self.pages)
            ]})
        if req.url.path.endswith("/image"):
            import json
            body = json.loads(req.content)
            index = body["index"]
            n = self.image_calls.get(index, 0)
            self.image_calls[index] = n + 1
            if self.fail_plan.get(index, 0) > 0:
                self.fail_plan[index] -= 1
                return httpx.Response(503, json={"error": "upstream busy"})
            data = PNG if index == 1 else JPEG
            ctype = "image/png" if index == 1 else "image/jpeg"
            return httpx.Response(200, content=data, headers={"Content-Type": ctype, "X-Upstream-Status": "200"})
        return httpx.Response(404, json={"error": "no route"})


def make_worker(tmp_path, fake, **kw):
    client = ExtensionHostClient("http://host", "t", transport=httpx.MockTransport(fake.handler))
    sleeps = []

    async def no_sleep(s):
        sleeps.append(s)

    worker = SourceDownloadWorker(client, str(tmp_path), sleep=no_sleep, **kw)
    worker._sleeps = sleeps
    return worker


async def new_series(db):
    series, _ = await add_series(db, SOURCE, MANGA)
    await db.commit()
    return series


async def test_enqueue_skips_chapters_already_queued(db, tmp_path):
    series = await new_series(db)
    worker = make_worker(tmp_path, FakeHost())
    chapters = [{"url": "/c/1", "name": "Chapter 1", "chapter_number": 1}]
    assert len(await worker.enqueue(db, series, SOURCE.module, chapters)) == 1
    await db.commit()
    assert await worker.enqueue(db, series, SOURCE.module, chapters) == []


async def test_chapter_downloads_as_cbz_with_pages_in_order(db, tmp_path):
    series = await new_series(db)
    worker = make_worker(tmp_path, FakeHost())
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/1", "name": "Chapter 1", "chapter_number": 1}])
    await db.commit()
    result = await worker.process(db)
    assert (result.downloaded, result.failed) == (1, 0)
    row = (await db.execute(select(SourceDownload))).scalar_one()
    assert row.status == "downloaded" and row.page_count == 3 and row.attempts == 1
    assert row.path.endswith("Chapter 1.cbz") and os.path.exists(row.path)
    with zipfile.ZipFile(row.path) as z:
        pages = [n for n in z.namelist() if n != "ComicInfo.xml"]
    assert pages == ["001.jpg", "002.png", "003.jpg"]
    assert not os.path.exists(row.path + ".tmp")


async def test_failing_page_is_retried_with_mihon_waits(db, tmp_path):
    series = await new_series(db)
    fake = FakeHost(fail_plan={0: 2})
    worker = make_worker(tmp_path, fake)
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/1", "name": "Chapter 1", "chapter_number": 1}])
    await db.commit()
    await worker.process(db)
    row = (await db.execute(select(SourceDownload))).scalar_one()
    assert row.status == "downloaded"
    assert worker._sleeps == [2.0, 4.0]  # two failures, two waits
    assert fake.image_calls[0] == 3


async def test_permanent_failure_is_error_then_retry_completes_without_refetching_pages(db, tmp_path):
    series = await new_series(db)
    fake = FakeHost(fail_plan={2: 99})  # page 2 fails every time
    worker = make_worker(tmp_path, fake)
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/1", "name": "Chapter 1", "chapter_number": 1}])
    await db.commit()
    await worker.process(db)
    row = (await db.execute(select(SourceDownload))).scalar_one()
    assert row.status == "error" and "upstream busy" in (row.last_error or "")
    assert row.path is None
    assert fake.page_list_calls == 1

    fake.fail_plan[2] = 0  # the source recovers
    row.status = "queued"
    await db.commit()
    await worker.process(db)
    await db.refresh(row)
    assert row.status == "downloaded" and row.attempts == 2
    assert fake.page_list_calls == 1  # the stored page list was reused
    assert fake.image_calls[0] == 1  # finished pages were not fetched again


async def test_restart_puts_downloading_rows_back_in_the_queue(db, tmp_path):
    series = await new_series(db)
    worker = make_worker(tmp_path, FakeHost())
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/1", "name": "Chapter 1", "chapter_number": 1}])
    await db.commit()
    row = (await db.execute(select(SourceDownload))).scalar_one()
    row.status = "downloading"
    await db.commit()
    assert await worker.recover(db) == 1
    await db.refresh(row)
    assert row.status == "queued"


async def test_already_committed_chapter_is_not_downloaded_again(db, tmp_path):
    series = await new_series(db)
    fake = FakeHost()
    worker = make_worker(tmp_path, fake)
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/1", "name": "Chapter 1", "chapter_number": 1}])
    await db.commit()
    await worker.process(db)
    row = (await db.execute(select(SourceDownload))).scalar_one()
    row.status = "queued"
    await db.commit()
    before = dict(fake.image_calls)
    await worker.process(db)
    assert fake.image_calls == before
    await db.refresh(row)
    assert row.status == "downloaded"


def test_image_extension_prefers_the_file_signature():
    assert image_extension(JPEG, "image/png") == "jpg"
    assert image_extension(PNG, None) == "png"
    assert image_extension(b"RIFF\x00\x00\x00\x00WEBPVP8 ", None) == "webp"
    assert image_extension(b"unknown", "image/avif") == "avif"
    assert image_extension(b"unknown", None) == "jpg"


async def test_startup_recovery_function_restores_interrupted_rows(db, tmp_path):
    from app.sources.download_worker import recover_queue
    series = await new_series(db)
    worker = make_worker(tmp_path, FakeHost())
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/9", "name": "Chapter 9", "chapter_number": 9}])
    await db.commit()
    row = (await db.execute(select(SourceDownload))).scalar_one()
    row.status = "downloading"
    await db.commit()
    assert await recover_queue(db) == 1
    await db.refresh(row)
    assert row.status == "queued"


async def test_cbz_includes_comicinfo_and_escapes_text(db, tmp_path):
    from app.sources.download_worker import comic_info_xml
    series = await new_series(db)
    worker = make_worker(tmp_path, FakeHost())
    await worker.enqueue(db, series, SOURCE.module, [{"url": "/c/1", "name": "Ch <1> & more", "chapter_number": 1}])
    await db.commit()
    await worker.process(db)
    row = (await db.execute(select(SourceDownload))).scalar_one()
    with zipfile.ZipFile(row.path) as z:
        names = z.namelist()
        xml = z.read("ComicInfo.xml").decode()
    assert sorted(names) == ["001.jpg", "002.png", "003.jpg", "ComicInfo.xml"]
    assert "<Series>Series X</Series>" in xml and "<Number>1</Number>" in xml
    assert "&lt;1&gt; &amp; more" in xml
