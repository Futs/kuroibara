"""Chapter download writer, following Mihon's method (app/.../data/download/Downloader.kt).

Pages are written into `<chapter>_tmp/`. A page is written to `NNN.<ext>.tmp` and renamed when complete, so an
interrupted page never looks finished. The chapter is committed only when every page is present; then it is
either renamed to `<chapter>/` or packed into `<chapter>.cbz` (written as `.cbz.tmp`, then renamed).
Nothing is shown as downloaded until commit().

Retries and rate limits are separate things:
- `RETRY_DELAYS` is error backoff for a failed page (3 retries, 2s, 4s, 8s), as in Mihon.
- Rate limits are the extension's own rules (keiyoushi `rateLimit`) applied in its HTTP client. They are not here.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import zipfile
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

TMP_SUFFIX = "_tmp"
COMIC_INFO = "ComicInfo.xml"
PARTIAL_SUFFIX = ".tmp"
RETRY_DELAYS = (2.0, 4.0, 8.0)

T = TypeVar("T")

_UNSAFE = re.compile(r'[\\/:*?"<>|\x00-\x1f]+')


class IncompleteChapterError(Exception):
    """Raised by commit() when some pages are missing. The chapter stays uncommitted."""


def safe_name(name: str, fallback: str = "untitled") -> str:
    """Filesystem-safe folder or file name, the way Mihon's DiskUtil does it roughly: no separators or control chars."""
    cleaned = _UNSAFE.sub("_", name).strip().strip(".")
    return cleaned[:200] or fallback


async def with_retries(
    fn: Callable[[], Awaitable[T]],
    *,
    delays: tuple[float, ...] = RETRY_DELAYS,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Runs fn, retrying after each delay on failure. Re-raises the last error."""
    attempt = 0
    while True:
        try:
            return await fn()
        except asyncio.CancelledError:
            raise
        except Exception:
            if attempt >= len(delays):
                raise
            await sleep(delays[attempt])
            attempt += 1


@dataclass(frozen=True)
class ChapterPaths:
    tmp_dir: str
    final: str  # the .cbz file or the chapter folder
    cbz: bool


class ChapterWriter:
    """Writes one chapter. Create one per download attempt; it resumes from what is already on disk."""

    def __init__(self, series_dir: str, chapter_dirname: str, *, cbz: bool = True):
        dirname = safe_name(chapter_dirname)
        self.paths = ChapterPaths(
            tmp_dir=os.path.join(series_dir, dirname + TMP_SUFFIX),
            final=os.path.join(series_dir, dirname + (".cbz" if cbz else "")),
            cbz=cbz,
        )
        os.makedirs(self.paths.tmp_dir, exist_ok=True)

    # Final file names are NNN.<ext>; NNN is the 1-based page number, zero-padded to 3 digits.
    @staticmethod
    def page_name(index: int, ext: str) -> str:
        return f"{index:03d}.{ext.lstrip('.').lower()}"

    def already_committed(self) -> bool:
        """True if the chapter is already in place (the guard against a second copy after a crash)."""
        return os.path.exists(self.paths.final)

    def partial_size(self, index: int) -> int:
        """Bytes already written for a page that was interrupted. 0 if none. Used to resume with HTTP Range."""
        candidates = [
            os.path.join(self.paths.tmp_dir, f"{index:03d}.{ext}{PARTIAL_SUFFIX}")
            for ext in ("jpg", "jpeg", "png", "webp", "gif", "avif")
        ]
        for path in candidates:
            if os.path.exists(path):
                return os.path.getsize(path)
        return 0

    def partial_path(self, index: int, ext: str) -> str:
        return os.path.join(self.paths.tmp_dir, self.page_name(index, ext) + PARTIAL_SUFFIX)

    def write_comic_info(self, xml: str) -> str:
        """Writes ComicInfo.xml into the temp folder. It goes into the CBZ or folder on commit (Mihon does the same)."""
        path = os.path.join(self.paths.tmp_dir, COMIC_INFO)
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return path

    def write_partial(self, index: int, ext: str, data: bytes, *, append: bool = False) -> None:
        """Writes bytes of a page into its .tmp file. append=True continues it (HTTP 206 after an interruption)."""
        with open(self.partial_path(index, ext), "ab" if append else "wb") as f:
            f.write(data)

    def finish_page(self, index: int, ext: str) -> str:
        """Renames a completely written page into place. Only now does it count as downloaded."""
        final = os.path.join(self.paths.tmp_dir, self.page_name(index, ext))
        os.replace(self.partial_path(index, ext), final)
        return final

    def write_page(self, index: int, ext: str, data: bytes) -> str:
        """Writes a whole page in one go: partial, then finish."""
        self.write_partial(index, ext, data)
        return self.finish_page(index, ext)

    def discard_partial(self, index: int) -> None:
        """Deletes a partial page after a 416 (the stored range is no longer valid)."""
        for ext in ("jpg", "jpeg", "png", "webp", "gif", "avif"):
            path = os.path.join(self.paths.tmp_dir, f"{index:03d}.{ext}{PARTIAL_SUFFIX}")
            if os.path.exists(path):
                os.remove(path)

    def pages_on_disk(self) -> list[str]:
        """Finished page files (no .tmp), sorted by page number. ComicInfo.xml is not a page."""
        names = [
            n for n in os.listdir(self.paths.tmp_dir)
            if not n.endswith(PARTIAL_SUFFIX) and re.match(r"^\d{3}\.[a-z0-9]+$", n)
        ]
        return sorted(names)

    def is_complete(self, page_count: int) -> bool:
        """Mihon's completeness check: the right number of finished pages, and no partial files left."""
        if page_count <= 0:
            return False
        leftovers = [n for n in os.listdir(self.paths.tmp_dir) if n.endswith(PARTIAL_SUFFIX)]
        return not leftovers and len(self.pages_on_disk()) == page_count

    def commit(self, page_count: int) -> str:
        """Moves the finished chapter into place. Raises IncompleteChapterError if any page is missing."""
        if not self.is_complete(page_count):
            raise IncompleteChapterError(
                f"{len(self.pages_on_disk())} of {page_count} pages on disk for {os.path.basename(self.paths.final)}"
            )
        if self.paths.cbz:
            self._archive()
        else:
            if os.path.exists(self.paths.final):
                shutil.rmtree(self.paths.final)
            os.replace(self.paths.tmp_dir, self.paths.final)
        return self.paths.final

    def _archive(self) -> None:
        """Packs the pages into <chapter>.cbz via <chapter>.cbz.tmp, then renames, then removes the folder."""
        zip_tmp = self.paths.final + PARTIAL_SUFFIX
        names = self.pages_on_disk()
        if os.path.exists(os.path.join(self.paths.tmp_dir, COMIC_INFO)):
            names = [COMIC_INFO] + names
        with zipfile.ZipFile(zip_tmp, "w", zipfile.ZIP_STORED) as z:
            for name in names:
                z.write(os.path.join(self.paths.tmp_dir, name), arcname=name)
        os.replace(zip_tmp, self.paths.final)
        shutil.rmtree(self.paths.tmp_dir, ignore_errors=True)

    def abandon(self) -> None:
        """Removes the temp folder. Only for a chapter that will not be retried."""
        shutil.rmtree(self.paths.tmp_dir, ignore_errors=True)
