"""Series from extension sources: add, duplicate handling, revert to provider. Needs the test database."""
import pytest
from sqlalchemy import select

from app.models.extension_series import Series, SeriesMetadata
from app.sources.series_service import (
    SourceRef,
    add_series,
    provider_fields,
    revert_to_provider,
)

SOURCE = SourceRef(
    module="en/mangakatana",
    package="eu.kanade.tachiyomi.extension.en.mangakatana",
    name="MangaKatana",
    lang="en",
    source_id="3170561626848540385",
)

MANGA = {
    "url": "/manga/one-piece.49",
    "title": "One Piece",
    "author": "Oda Eiichiro",
    "artist": "Oda Eiichiro, Someone Else",
    "genre": "Action, Adventure",
    "status": 1,
    "description": "Pirates.",
    "thumbnail_url": "https://example.test/cover.jpg",
}


def test_provider_fields_splits_lists_and_keeps_missing_as_empty():
    fields = provider_fields({"title": "T", "author": "A, B"})
    assert fields["authors"] == ["A", "B"]
    assert fields["genres"] == []
    assert fields["cover_url"] is None


async def test_add_series_stores_base_and_tagged_current(db):
    series, created = await add_series(db, SOURCE, MANGA)
    await db.commit()
    assert created is True

    meta = (await db.execute(select(SeriesMetadata).where(SeriesMetadata.series_id == series.id))).scalar_one()
    assert meta.base["title"] == "One Piece"
    assert meta.current["title"] == {"value": "One Piece", "origin": "provider"}
    assert meta.current["authors"] == {"value": ["Oda Eiichiro"], "origin": "provider"}
    assert meta.mangaupdates is None

    assert series.module == "en/mangakatana" and series.in_library is True
    assert series.series_url == "/manga/one-piece.49" and series.title == "One Piece"


async def test_same_extension_and_url_is_not_duplicated(db):
    first, _ = await add_series(db, SOURCE, MANGA)
    second, created = await add_series(db, SOURCE, MANGA)
    await db.commit()
    assert created is False
    assert second.id == first.id
    count = len((await db.execute(select(Series))).scalars().all())
    assert count == 1


async def test_same_title_from_another_extension_is_a_new_series_link(db):
    other = SourceRef(module="en/toonily", package="eu.kanade.tachiyomi.extension.en.toonily",
                      name="Toonily", lang="en", source_id=None)
    first, _ = await add_series(db, SOURCE, MANGA)
    second, created = await add_series(db, other, {**MANGA, "url": "/series/42"})
    await db.commit()
    assert created is True and second.id != first.id


async def test_nsfw_content_warning_sets_flag(db):
    series, _ = await add_series(db, SOURCE, {**MANGA, "url": "/x"}, content_warning="CONTENT_WARNING_NSFW")
    await db.commit()
    assert series.is_nsfw is True


async def test_revert_restores_provider_values_and_keeps_base(db):
    series, _ = await add_series(db, SOURCE, MANGA)
    meta = series.metadata_record
    meta.current = {**meta.current, "title": {"value": "Edited", "origin": "edited"}}
    await db.flush()

    await revert_to_provider(db, series)
    await db.commit()
    assert meta.current["title"] == {"value": "One Piece", "origin": "provider"}
    assert meta.base["title"] == "One Piece"


OTHER = SourceRef(module="en/toonily", package="eu.kanade.tachiyomi.extension.en.toonily",
                  name="Toonily", lang="en", source_id=None)


async def test_migrate_creates_a_new_entry_and_takes_the_old_one_out_of_the_library(db):
    from app.sources.series_service import migrate_to_source
    old, _ = await add_series(db, SOURCE, MANGA)
    new, created = await migrate_to_source(db, old, OTHER, {**MANGA, "url": "/series/42"})
    await db.commit()
    assert created is True and new.id != old.id
    assert old.in_library is False and new.in_library is True
    assert new.module == "en/toonily" and new.series_url == "/series/42"
    assert new.metadata_record.current["title"] == {"value": "One Piece", "origin": "provider"}


async def test_migrate_with_copy_keeps_the_old_entry_in_the_library(db):
    from app.sources.series_service import migrate_to_source
    old, _ = await add_series(db, SOURCE, MANGA)
    await migrate_to_source(db, old, OTHER, {**MANGA, "url": "/series/42"}, replace=False)
    await db.commit()
    assert old.in_library is True


async def test_migrate_carries_chosen_values_and_keeps_their_origin(db):
    from app.sources.series_service import migrate_to_source
    old, _ = await add_series(db, SOURCE, MANGA)
    meta = old.metadata_record
    meta.current = {**meta.current,
                    "title": {"value": "ONE PIECE (MU)", "origin": "mangaupdates"},
                    "description": {"value": "Edited blurb", "origin": "edited"}}
    meta.mangaupdates = {"id": 123, "title": "ONE PIECE (MU)"}
    await db.flush()
    new, _ = await migrate_to_source(db, old, OTHER, {**MANGA, "url": "/series/42", "description": "Provider blurb"},
                                     carry_metadata=True)
    await db.commit()
    cur = new.metadata_record.current
    assert cur["title"] == {"value": "ONE PIECE (MU)", "origin": "mangaupdates"}
    assert cur["description"] == {"value": "Edited blurb", "origin": "edited"}
    assert cur["genres"]["origin"] == "provider"  # not chosen on the old entry, so it stays the provider's
    assert new.title == "ONE PIECE (MU)"  # the listing copy follows the shown title
    assert new.metadata_record.base["title"] == "One Piece"  # the snapshot is still the target's own
    assert new.metadata_record.mangaupdates == {"id": 123, "title": "ONE PIECE (MU)"}


async def test_migrating_to_the_same_title_is_refused(db):
    from app.sources.series_service import migrate_to_source
    old, _ = await add_series(db, SOURCE, MANGA)
    with pytest.raises(ValueError):
        await migrate_to_source(db, old, SOURCE, MANGA)


async def test_readding_a_removed_title_puts_it_back(db):
    from app.sources.series_service import migrate_to_source
    old, _ = await add_series(db, SOURCE, MANGA)
    await migrate_to_source(db, old, OTHER, {**MANGA, "url": "/series/42"})
    again, created = await add_series(db, SOURCE, MANGA)
    await db.commit()
    assert created is False and again.id == old.id and again.in_library is True


async def test_revert_updates_the_listing_title(db):
    series, _ = await add_series(db, SOURCE, MANGA)
    meta = series.metadata_record
    meta.current = {**meta.current, "title": {"value": "Edited", "origin": "edited"}}
    series.title = "Edited"
    await db.flush()
    await revert_to_provider(db, series)
    await db.commit()
    assert series.title == "One Piece"
