"""Library entries from extension sources, their metadata, revert, and migration to another source.

Model (Mihon's): one `series` row per title per source. `series_metadata` holds the provider snapshot (`base`)
and the values shown (`current`, each with an origin). Migrating creates a second entry for the new source;
the old entry stays in the database with in_library = false, so nothing is lost.

MangaUpdates is applied later, field by field (Phase 2b). It never runs automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extension_series import Series, SeriesMetadata

# Fields the library shows, and where each comes from in the host's manga JSON.
PROVIDER_FIELDS = ("title", "description", "authors", "artists", "genres", "status", "cover_url")
# Origins a user chose on purpose; these are what a migration may carry over.
CHOSEN_ORIGINS = ("mangaupdates", "edited")


@dataclass(frozen=True)
class SourceRef:
    """Which extension a library entry comes from. `module` is the host install key."""

    module: str
    package: str
    name: str
    lang: str
    source_id: Optional[str]


def _split(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def provider_fields(manga: dict[str, Any]) -> dict[str, Any]:
    """Maps the host's manga JSON to the library fields. Missing values stay empty."""
    return {
        "title": manga.get("title") or "",
        "description": manga.get("description"),
        "authors": _split(manga.get("author")),
        "artists": _split(manga.get("artist")),
        "genres": _split(manga.get("genre")),
        "status": manga.get("status"),
        "cover_url": manga.get("thumbnail_url"),
    }


def tagged(fields: dict[str, Any], origin: str) -> dict[str, dict[str, Any]]:
    return {name: {"value": value, "origin": origin} for name, value in fields.items()}


def sync_listing(series: Series, record: SeriesMetadata) -> None:
    """Copies the shown title and cover onto the row, so lists and sorting need no join."""
    current = record.current or {}
    title = (current.get("title") or {}).get("value")
    if title:
        series.title = title
    series.cover_url = (current.get("cover_url") or {}).get("value")


async def find_existing(session: AsyncSession, module: str, series_url: str) -> Optional[Series]:
    return (await session.execute(
        select(Series).where(Series.module == module, Series.series_url == series_url)
    )).scalar_one_or_none()


async def add_series(
    session: AsyncSession,
    source: SourceRef,
    manga: dict[str, Any],
    *,
    content_warning: Optional[str] = None,
) -> tuple[Series, bool]:
    """Adds a title from a source's details result. Returns (series, created).

    An entry for the same source and URL is returned, not duplicated. If it was removed from the library, it is
    put back (Mihon does the same when you favourite a title again).
    """
    series_url = manga["url"]
    existing = await find_existing(session, source.module, series_url)
    if existing is not None:
        if not existing.in_library:
            existing.in_library = True
            await session.flush()
        return existing, False

    fields = provider_fields(manga)
    series = Series(
        module=source.module,
        package=source.package,
        source_name=source.name,
        source_lang=source.lang,
        source_id=source.source_id,
        series_url=series_url,
        title=fields["title"],
        cover_url=fields["cover_url"],
        is_nsfw=content_warning == "CONTENT_WARNING_NSFW",
        content_warning=content_warning,
        in_library=True,
    )
    series.metadata_record = SeriesMetadata(base=fields, current=tagged(fields, "provider"))
    session.add(series)
    await session.flush()
    return series, True


async def revert_to_provider(session: AsyncSession, series: Series) -> SeriesMetadata:
    """Resets the shown values to this entry's provider snapshot. Keeps the cached MangaUpdates entry."""
    record = series.metadata_record
    record.current = tagged(record.base, "provider")
    sync_listing(series, record)
    await session.flush()
    return record


async def migrate_to_source(
    session: AsyncSession,
    old: Series,
    target: SourceRef,
    manga: dict[str, Any],
    *,
    content_warning: Optional[str] = None,
    replace: bool = True,
    carry_metadata: bool = False,
) -> tuple[Series, bool]:
    """Mihon's migration. Creates (or reuses) the target entry, then:
    - carry_metadata: copies the values the user chose (MangaUpdates or edited) into the target.
      Origins are kept, so the target shows where each value came from. Its provider snapshot is unchanged.
    - replace: the old entry leaves the library (in_library = false). With replace=False it is a copy, and both stay.
    Downloads of the old entry are not touched. Returns (target, created).
    """
    if target.module == old.module and manga["url"] == old.series_url:
        raise ValueError("the title is already on this source")

    new, created = await add_series(session, target, manga, content_warning=content_warning)
    if carry_metadata and old.metadata_record is not None and new.metadata_record is not None:
        new_current = dict(new.metadata_record.current or {})
        for name, entry in (old.metadata_record.current or {}).items():
            if entry.get("origin") in CHOSEN_ORIGINS:
                new_current[name] = dict(entry)
        new.metadata_record.current = new_current
        new.metadata_record.mangaupdates = old.metadata_record.mangaupdates  # so the comparison still works offline
        sync_listing(new, new.metadata_record)
    if replace:
        old.in_library = False
    await session.flush()
    return new, created


async def apply_values(session: AsyncSession, series: Series, updates: dict[str, tuple[Any, str]]) -> SeriesMetadata:
    """Sets the shown value and origin for each field, then updates the listing copy. Nothing else changes."""
    record = series.metadata_record
    current = dict(record.current or {})
    for name, (value, origin) in updates.items():
        current[name] = {"value": value, "origin": origin}
    record.current = current
    sync_listing(series, record)
    await session.flush()
    return record
