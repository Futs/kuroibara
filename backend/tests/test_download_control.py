"""Download controls: retry, cancel, remove and re-download, with the files they touch. Test database + temp dir."""
import os

import pytest
from sqlalchemy import select

from app.models.extension_series import SourceDownload
from app.sources import download_control as ctl
from app.sources.series_service import SourceRef, add_series
from app.sources.download_control import DownloadControlError

SRC = SourceRef(module="en/mangakatana", package="eu.kanade.tachiyomi.extension.en.mangakatana",
                name="MangaKatana", lang="en", source_id=None)


async def row_with(db, status, path=None, url="/c/1"):
    s, _ = await add_series(db, SRC, {"url": f"/m/{url}", "title": "T"})
    r = SourceDownload(series_id=s.id, module=SRC.module, chapter_url=url, chapter_name="Chapter 1",
                       chapter_number=1.0, status=status, path=path, pages=[{"index": 0, "url": "", "image_url": "x"}],
                       page_count=1)
    db.add(r)
    await db.commit()
    return r


async def test_retry_only_from_error_and_keeps_pages(db):
    r = await row_with(db, "error")
    r.last_error = "boom"
    await db.commit()
    await ctl.retry(db, r)
    assert r.status == "queued" and r.last_error is None and r.pages is not None


async def test_retry_refused_for_other_states(db):
    r = await row_with(db, "downloaded", url="/c/2")
    with pytest.raises(DownloadControlError):
        await ctl.retry(db, r)


async def test_cancel_queued_or_failed_but_not_downloading(db):
    q = await row_with(db, "queued", url="/c/3")
    await ctl.cancel(db, q)
    assert q.status == "cancelled"
    d = await row_with(db, "downloading", url="/c/4")
    with pytest.raises(DownloadControlError):
        await ctl.cancel(db, d)


async def test_remove_deletes_the_cbz_and_the_row(db, tmp_path):
    cbz = tmp_path / "T [abc]" / "Chapter 1.cbz"
    cbz.parent.mkdir(parents=True)
    cbz.write_bytes(b"zip")
    r = await row_with(db, "downloaded", path=str(cbz), url="/c/5")
    await ctl.remove(db, r, str(tmp_path))
    await db.commit()
    assert not cbz.exists()
    assert (await db.execute(select(SourceDownload).where(SourceDownload.id == r.id))).scalar_one_or_none() is None


async def test_paths_outside_the_download_root_are_never_deleted(db, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "keep.cbz"
    outside.write_bytes(b"keep")
    r = await row_with(db, "downloaded", path=str(outside), url="/c/6")
    await ctl.remove(db, r, str(root))
    assert outside.exists()


async def test_redownload_deletes_the_copy_and_resets_the_page_list(db, tmp_path):
    folder = tmp_path / "T [abc]" / "Chapter 1"
    folder.mkdir(parents=True)
    (folder / "001.jpg").write_bytes(b"x")
    r = await row_with(db, "downloaded", path=str(folder), url="/c/7")
    await ctl.redownload(db, r, str(tmp_path))
    assert not folder.exists()
    assert r.status == "queued" and r.pages is None and r.path is None and r.page_count is None


async def test_downloading_chapters_are_left_alone(db, tmp_path):
    r = await row_with(db, "downloading", url="/c/8")
    for fn in (lambda: ctl.remove(db, r, str(tmp_path)), lambda: ctl.redownload(db, r, str(tmp_path))):
        with pytest.raises(DownloadControlError):
            await fn()
