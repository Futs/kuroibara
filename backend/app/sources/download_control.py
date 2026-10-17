"""User controls for source chapter downloads: retry, cancel, remove, and re-download.

Rules:
- A chapter that is downloading cannot be changed here. The worker owns it until it finishes or fails.
- Only files under the configured download root are ever deleted. A stored path outside it is ignored.
- Remove and re-download delete the committed file (CBZ or folder) and any leftover temp folder.
"""
from __future__ import annotations

import os
import shutil
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extension_series import SourceDownload

QUEUED, DOWNLOADING, DOWNLOADED, ERROR, CANCELLED = "queued", "downloading", "downloaded", "error", "cancelled"


class DownloadControlError(Exception):
    """The action is not allowed in the chapter's current state."""


def _inside(root: str, path: str) -> bool:
    root_real = os.path.realpath(root)
    target = os.path.realpath(path)
    return target != root_real and os.path.commonpath([root_real, target]) == root_real


def _delete_files(root: str, row: SourceDownload) -> None:
    """Removes the committed file or folder, and any "<name>_tmp" folder or ".cbz.tmp" file beside it."""
    if not row.path:
        return
    candidates = [row.path, row.path + ".tmp"]
    base = row.path[:-4] if row.path.endswith(".cbz") else row.path
    candidates.append(base + "_tmp")
    for path in candidates:
        if not os.path.exists(path) or not _inside(root, path):
            continue
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.remove(path)


async def retry(db: AsyncSession, row: SourceDownload) -> SourceDownload:
    """Failed chapters go back to the queue. Finished pages are kept, so the retry does not refetch them."""
    if row.status != ERROR:
        raise DownloadControlError(f"only a failed chapter can be retried (it is {row.status})")
    row.status = QUEUED
    row.last_error = None
    await db.flush()
    return row


async def cancel(db: AsyncSession, row: SourceDownload) -> SourceDownload:
    """Stops a queued or failed chapter. A chapter that is downloading cannot be cancelled mid-flight."""
    if row.status == DOWNLOADING:
        raise DownloadControlError("this chapter is downloading; cancel is possible once it finishes or fails")
    if row.status not in (QUEUED, ERROR):
        raise DownloadControlError(f"nothing to cancel (it is {row.status})")
    row.status = CANCELLED
    await db.flush()
    return row


async def remove(db: AsyncSession, row: SourceDownload, root: str) -> None:
    """Deletes the chapter's files and its queue row. The chapter is then not downloaded."""
    if row.status == DOWNLOADING:
        raise DownloadControlError("this chapter is downloading; it cannot be removed until it finishes or fails")
    _delete_files(root, row)
    await db.delete(row)
    await db.flush()


async def redownload(db: AsyncSession, row: SourceDownload, root: str) -> SourceDownload:
    """Deletes the committed copy and queues the chapter again from a fresh page list."""
    if row.status == DOWNLOADING:
        raise DownloadControlError("this chapter is downloading; it cannot be re-downloaded until it finishes or fails")
    _delete_files(root, row)
    row.status = QUEUED
    row.path = None
    row.pages = None
    row.page_count = None
    row.last_error = None
    await db.flush()
    return row
