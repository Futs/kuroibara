"""Chapter writer: tmp files, resume, completeness, commit and CBZ packing. Filesystem only, no database."""
import asyncio
import os
import zipfile

import pytest

from app.sources.download_writer import (
    IncompleteChapterError,
    ChapterWriter,
    RETRY_DELAYS,
    safe_name,
    with_retries,
)


def test_pages_go_to_tmp_until_commit(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    w.write_page(1, "jpg", b"a")
    w.write_page(2, "jpg", b"b")
    assert not w.already_committed()
    assert os.path.isdir(w.paths.tmp_dir) and not os.path.exists(w.paths.final)
    assert w.pages_on_disk() == ["001.jpg", "002.jpg"]


def test_partial_page_is_not_a_finished_page(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    with open(w.partial_path(1, "jpg"), "wb") as f:
        f.write(b"half")
    assert w.pages_on_disk() == []
    assert w.partial_size(1) == 4
    assert not w.is_complete(1)


def test_resume_appends_to_partial_then_finishes(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    w.write_partial(1, "jpg", b"ab")
    assert w.pages_on_disk() == []  # not finished yet
    w.write_partial(1, "jpg", b"cd", append=True)  # HTTP 206 continues from the stored bytes
    assert w.partial_size(1) == 4
    w.finish_page(1, "jpg")
    assert open(os.path.join(w.paths.tmp_dir, "001.jpg"), "rb").read() == b"abcd"


def test_416_discards_partial(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    with open(w.partial_path(3, "png"), "wb") as f:
        f.write(b"stale")
    w.discard_partial(3)
    assert w.partial_size(3) == 0


def test_commit_refuses_an_incomplete_chapter(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    w.write_page(1, "jpg", b"a")
    with pytest.raises(IncompleteChapterError):
        w.commit(page_count=2)
    assert not os.path.exists(w.paths.final)


def test_commit_refuses_when_a_partial_is_left_behind(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    w.write_page(1, "jpg", b"a")
    with open(w.partial_path(2, "jpg"), "wb") as f:
        f.write(b"x")
    assert not w.is_complete(1)


def test_commit_as_folder_renames_tmp_into_place(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=False)
    w.write_page(1, "jpg", b"a")
    w.write_page(2, "png", b"b")
    final = w.commit(page_count=2)
    assert final == os.path.join(str(tmp_path), "Chapter 1")
    assert sorted(os.listdir(final)) == ["001.jpg", "002.png"]
    assert not os.path.exists(w.paths.tmp_dir)


def test_commit_as_cbz_packs_pages_and_removes_folder(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=True)
    w.write_page(1, "jpg", b"a")
    w.write_page(2, "jpg", b"b")
    final = w.commit(page_count=2)
    assert final.endswith("Chapter 1.cbz")
    with zipfile.ZipFile(final) as z:
        assert z.namelist() == ["001.jpg", "002.jpg"]
    assert not os.path.exists(final + ".tmp")
    assert not os.path.exists(w.paths.tmp_dir)


def test_already_committed_is_detected(tmp_path):
    w = ChapterWriter(str(tmp_path), "Chapter 1", cbz=True)
    w.write_page(1, "jpg", b"a")
    w.commit(page_count=1)
    again = ChapterWriter(str(tmp_path), "Chapter 1", cbz=True)
    assert again.already_committed()


def test_unsafe_names_are_sanitised(tmp_path):
    assert "/" not in safe_name("a/b:c?")
    assert safe_name("..") == "untitled"
    w = ChapterWriter(str(tmp_path), "Ch 1: part/2", cbz=False)
    assert os.path.dirname(w.paths.tmp_dir) == str(tmp_path)


def test_retry_waits_match_mihon_and_gives_up_after_three(tmp_path):
    assert RETRY_DELAYS == (2.0, 4.0, 8.0)
    waits = []
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        raise RuntimeError("boom")

    async def fake_sleep(s):
        waits.append(s)

    with pytest.raises(RuntimeError):
        asyncio.run(with_retries(flaky, sleep=fake_sleep))
    assert waits == [2.0, 4.0, 8.0]
    assert calls["n"] == 4  # one try plus three retries


def test_retry_succeeds_on_a_later_attempt():
    state = {"n": 0}

    async def second_time():
        state["n"] += 1
        if state["n"] < 2:
            raise RuntimeError("once")
        return "ok"

    async def no_sleep(_):
        return None

    assert asyncio.run(with_retries(second_time, sleep=no_sleep)) == "ok"
