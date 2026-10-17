"""Source chapter downloads, Mihon's method (see download_writer.py for the file handling).

Queue: rows in `source_downloads`. A row is `queued`, `downloading`, `downloaded` or `error`.
- recover() puts rows left in `downloading` back to `queued` after a restart.
- process() takes queued rows and downloads them. Pages within a chapter run in parallel, up to
  `parallel_pages` (Mihon default 5). A chapter is `downloaded` only when every page is in and the commit succeeds.
- A failed chapter is `error` with the message. Its finished pages stay, so a retry does not refetch them.
"""
from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from xml.sax.saxutils import escape

from app.models.extension_series import Series, SeriesMetadata, SourceDownload
from app.sources.download_writer import (
    RETRY_DELAYS,
    ChapterWriter,
    IncompleteChapterError,
    safe_name,
    with_retries,
)
from app.sources.host_client import ExtensionHostClient, ExtensionHostError

QUEUED, DOWNLOADING, DOWNLOADED, ERROR = "queued", "downloading", "downloaded", "error"

_SIGNATURES = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF8", "gif"),
)
_MIME = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif",
         "image/avif": "avif"}


def image_extension(body: bytes, content_type: Optional[str]) -> str:
    """Extension from the file's own bytes first, then the content type, then jpg (as Mihon falls back)."""
    for sig, ext in _SIGNATURES:
        if body.startswith(sig):
            return ext
    if len(body) >= 12 and body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return "webp"
    if content_type:
        ext = _MIME.get(content_type.split(";")[0].strip().lower())
        if ext:
            return ext
    return "jpg"


def _values(current: Optional[dict[str, Any]], name: str) -> Any:
    entry = (current or {}).get(name) or {}
    return entry.get("value")


def comic_info_xml(series: Series, row: SourceDownload, meta: Optional[SeriesMetadata]) -> str:
    """ComicInfo.xml, the fields Mihon writes for a chapter: series, number, writer, genre, summary, web link."""
    current = meta.current if meta else {}
    authors = _values(current, "authors") or []
    genres = _values(current, "genres") or []
    summary = _values(current, "description") or ""
    fields = {
        "Series": series.title,
        "Title": row.chapter_name or "",
        "Number": f"{row.chapter_number:g}" if row.chapter_number is not None else "",
        "Writer": ", ".join(authors),
        "Genre": ", ".join(genres),
        "Summary": summary,
        "Web": row.chapter_url,
        "LanguageISO": "",
    }
    body = "".join(f"  <{k}>{escape(v)}</{k}>\n" for k, v in fields.items() if v)
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n' + body + "</ComicInfo>\n")


def series_folder(series: Series) -> str:
    """Readable and unique: "<title> [<first 8 hex of the series id>]". Stable across renames and migrations,
    because the series id does not change when its source changes."""
    return f"{safe_name(series.title, 'series')} [{series.id.hex[:8]}]"


def chapter_dirname(row: SourceDownload) -> str:
    if row.chapter_name:
        return safe_name(row.chapter_name, "chapter")
    if row.chapter_number is not None:
        return f"Chapter {row.chapter_number:g}"
    return "chapter"


async def recover_queue(db: AsyncSession) -> int:
    """Startup recovery for the single worker: rows left downloading go back to queued. Returns how many.
    Only the worker calls this at its startup. The API must not, or it would reset a running worker's rows."""
    result = await db.execute(
        update(SourceDownload).where(SourceDownload.status == DOWNLOADING)
        .values(status=QUEUED, claimed_by=None, claimed_at=None)
    )
    await db.commit()
    return result.rowcount or 0


@dataclass
class QueueResult:
    attempted: int
    downloaded: int
    failed: int


class SourceDownloadWorker:
    def __init__(
        self,
        host: ExtensionHostClient,
        root_dir: str,
        *,
        parallel_pages: int = 5,
        cbz: bool = True,
        delays: tuple[float, ...] = RETRY_DELAYS,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        worker_id: str = "api",
    ):
        self.worker_id = worker_id
        self.host = host
        self.root_dir = root_dir
        self.parallel_pages = parallel_pages
        self.cbz = cbz
        self.delays = delays
        self.sleep = sleep

    # ---- queue -------------------------------------------------------------

    async def enqueue(self, db: AsyncSession, series: Series, module: str,
                      chapters: list[dict[str, Any]]) -> list[SourceDownload]:
        """Adds chapters to the queue. A chapter already queued or downloaded for this series is skipped."""
        existing = set((await db.execute(
            select(SourceDownload.chapter_url).where(
                SourceDownload.series_id == series.id, SourceDownload.module == module)
        )).scalars().all())
        added = []
        for ch in chapters:
            url = ch["url"]
            if url in existing:
                continue
            existing.add(url)
            row = SourceDownload(
                series_id=series.id,
                module=module,
                chapter_url=url,
                chapter_name=ch.get("name") or "",
                chapter_number=ch.get("chapter_number"),
                status=QUEUED,
                attempts=0,
            )
            db.add(row)
            added.append(row)
        await db.flush()
        return added

    async def recover(self, db: AsyncSession) -> int:
        """Same as recover_queue(). Their finished pages are kept. Only for startup: never call it while another worker runs."""
        return await recover_queue(db)

    async def claim_next(self, db: AsyncSession, *, limit: int) -> list[SourceDownload]:
        """Takes up to `limit` queued rows for this worker. Safe with several workers and API calls at once:
        SELECT ... FOR UPDATE SKIP LOCKED means a row locked by one transaction is skipped by the others.
        The caller must commit; the status change and the lock are released together on commit."""
        rows = (await db.execute(
            select(SourceDownload).where(SourceDownload.status == QUEUED)
            .order_by(SourceDownload.created_at).limit(limit)
            .with_for_update(skip_locked=True)
        )).scalars().all()
        now = datetime.now(timezone.utc)
        for row in rows:
            row.status = DOWNLOADING
            row.attempts = (row.attempts or 0) + 1
            row.claimed_by = self.worker_id
            row.claimed_at = now
            row.last_error = None
        return rows

    async def process(self, db: AsyncSession, *, limit: int = 5) -> QueueResult:
        """Claims and downloads up to `limit` chapters in this session. Used by the manual API call."""
        rows = await self.claim_next(db, limit=limit)
        await db.commit()
        downloaded = failed = 0
        for row in rows:
            ok = await self.download_one(db, row)
            downloaded += ok
            failed += not ok
        return QueueResult(attempted=len(rows), downloaded=downloaded, failed=failed)

    # ---- one chapter -------------------------------------------------------

    async def download_one(self, db: AsyncSession, row: SourceDownload) -> bool:
        series = await db.get(Series, row.series_id)
        # Folder = readable title plus a short id, so two series with the same title never share files.
        series_dir = os.path.join(self.root_dir, safe_name(row.module, "source"), series_folder(series))
        writer = ChapterWriter(series_dir, chapter_dirname(row), cbz=self.cbz)
        try:
            if writer.already_committed():
                return await self._mark(db, row, DOWNLOADED, path=writer.paths.final)

            if row.pages is None:
                pages = (await self.host.pages(row.module, row.chapter_url))["pages"]
                if not pages:
                    raise ExtensionHostError(None, "page list is empty")
                row.pages = [{"index": p["index"], "url": p.get("url", ""), "image_url": p.get("image_url")}
                             for p in pages]
                row.page_count = len(pages)
                await db.commit()

            sem = asyncio.Semaphore(self.parallel_pages)

            async def guarded(page: dict[str, Any]) -> None:
                async with sem:
                    await self._download_page(row, writer, page)

            await asyncio.gather(*(guarded(p) for p in row.pages))

            writer.write_comic_info(comic_info_xml(series, row, await db.get(SeriesMetadata, series.id)))
            path = writer.commit(page_count=row.page_count)
            return await self._mark(db, row, DOWNLOADED, path=path)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # any failure leaves the chapter in error, with its finished pages kept
            return await self._mark(db, row, ERROR, error=f"{type(e).__name__}: {e}"[:500])

    async def _download_page(self, row: SourceDownload, writer: ChapterWriter, page: dict[str, Any]) -> None:
        # The host's page index is 0-based; files are numbered from 001, as in Mihon.
        index = page["index"]
        number = index + 1
        if self._finished(writer, number):
            return

        async def attempt() -> None:
            offset = writer.partial_size(number)
            try:
                img = await self.host.image(row.module, image_url=page.get("image_url"),
                                            url=page.get("url", ""), index=index, offset=offset)
            except ExtensionHostError as e:
                if e.status == 416:
                    writer.discard_partial(number)
                raise
            resumed = offset > 0 and img.status == 206
            if offset > 0 and not resumed:
                writer.discard_partial(number)  # the extension sent the whole image; start over, as Mihon does
            ext = image_extension(img.body, img.content_type)
            writer.write_partial(number, ext, img.body, append=resumed)
            writer.finish_page(number, ext)

        await with_retries(attempt, delays=self.delays, sleep=self.sleep)

    @staticmethod
    def _finished(writer: ChapterWriter, number: int) -> bool:
        return any(re.match(rf"^{number:03d}\.[a-z0-9]+$", n) for n in writer.pages_on_disk())

    async def _mark(self, db: AsyncSession, row: SourceDownload, status: str, *, path: Optional[str] = None,
                    error: Optional[str] = None) -> bool:
        row.status = status
        row.path = path if path else row.path
        row.last_error = error
        await db.commit()
        return status == DOWNLOADED
