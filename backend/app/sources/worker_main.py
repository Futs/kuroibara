"""Source download worker: a separate process, run from the same image as the API.

  python -m app.sources.worker_main

Only one instance should run (the compose service has one replica). Startup puts rows left "downloading" back
in the queue, because no other worker can own them. The API never does that.

Loop: claim up to SOURCE_WORKER_PARALLEL_SOURCES queued chapters (atomic, see SourceDownloadWorker.claim_next),
download them concurrently, each in its own database session. When nothing is queued it waits
SOURCE_WORKER_POLL_SECONDS. SIGTERM finishes the current batch and exits. A hard stop leaves claimed rows
"downloading"; the next start recovers them, and their finished pages are kept.
"""
from __future__ import annotations

import asyncio
import logging
import signal
import socket
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.extension_series import SourceDownload
from app.sources.download_worker import SourceDownloadWorker, recover_queue
from app.sources.host_client import ExtensionHostClient

logger = logging.getLogger("source_worker")


class Worker:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        host: ExtensionHostClient,
        root_dir: str,
        *,
        worker_id: Optional[str] = None,
        parallel_sources: int = 5,
        parallel_pages: int = 5,
        poll_seconds: float = 5.0,
        cbz: bool = True,
    ):
        self.session_factory = session_factory
        self.parallel_sources = parallel_sources
        self.poll_seconds = poll_seconds
        self.stopping = asyncio.Event()
        self.downloader = SourceDownloadWorker(
            host, root_dir, parallel_pages=parallel_pages, cbz=cbz,
            worker_id=worker_id or f"worker-{socket.gethostname()}",
        )

    async def startup(self) -> int:
        async with self.session_factory() as db:
            restored = await recover_queue(db)
        if restored:
            logger.info("%d interrupted chapter(s) back in the queue", restored)
        return restored

    async def claim(self) -> list[int]:
        """Claims a batch and returns the row ids. Commits the claim, so other workers skip these rows."""
        async with self.session_factory() as db:
            rows = await self.downloader.claim_next(db, limit=self.parallel_sources)
            ids = [r.id for r in rows]
            await db.commit()
        return ids

    async def download(self, row_id) -> bool:
        async with self.session_factory() as db:
            row = await db.get(SourceDownload, row_id)
            if row is None:
                return False
            return await self.downloader.download_one(db, row)

    async def run_once(self) -> int:
        """One claim and download round. Returns how many chapters were handled."""
        ids = await self.claim()
        if ids:
            await asyncio.gather(*(self.download(i) for i in ids))
        return len(ids)

    async def run(self) -> None:
        await self.startup()
        logger.info("worker %s running (batch %d, pages %d)", self.downloader.worker_id,
                    self.parallel_sources, self.downloader.parallel_pages)
        while not self.stopping.is_set():
            handled = await self.run_once()
            if handled == 0:
                try:
                    await asyncio.wait_for(self.stopping.wait(), timeout=self.poll_seconds)
                except asyncio.TimeoutError:
                    pass
        logger.info("worker stopped")

    def request_stop(self) -> None:
        self.stopping.set()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    from app.db.session import AsyncSessionLocal

    if not settings.EXTENSION_HOST_TOKEN:
        raise SystemExit("EXTENSION_HOST_TOKEN is not set; the worker needs the extension host")
    host = ExtensionHostClient(settings.EXTENSION_HOST_URL, settings.EXTENSION_HOST_TOKEN)
    worker = Worker(
        AsyncSessionLocal,
        host,
        settings.SOURCE_DOWNLOAD_DIR,
        parallel_sources=settings.SOURCE_WORKER_PARALLEL_SOURCES,
        parallel_pages=settings.SOURCE_WORKER_PARALLEL_PAGES,
        poll_seconds=settings.SOURCE_WORKER_POLL_SECONDS,
    )
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, worker.request_stop)
    try:
        await worker.run()
    finally:
        await host.aclose()


if __name__ == "__main__":
    asyncio.run(main())
