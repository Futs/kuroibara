"""MangaUpdates for a library entry: search, link, compare, and apply per field (Phase 2b).

Reuses the existing MangaUpdates client and field extraction (app/core/services/mangaupdates.py).
Nothing is applied automatically: the user links a match, looks at the comparison, and picks each field.

Stored on series_metadata.mangaupdates: {"series_id", "fetched_at", "fields": {field: value}}. The comparison
works from that cache, so it still works offline after the first fetch. Refreshing is an explicit action.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.core.services.mangaupdates import MangaUpdatesAPI, MangaUpdatesService
from app.models.extension_series import SeriesMetadata

# Library status values (Mihon's SManga constants) for MangaUpdates' status words.
STATUS_CODES = {"ongoing": 1, "completed": 2, "hiatus": 6, "cancelled": 5}

# The fields the comparison covers, in display order.
COMPARE_FIELDS = ("title", "description", "authors", "artists", "genres", "status", "cover_url")
CHOICES = ("provider", "mangaupdates", "edited")


def _names(items: Any) -> list[str]:
    return [i["name"] for i in (items or []) if isinstance(i, dict) and i.get("name")]


def search_candidates(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Trims a MangaUpdates search response to what the user needs to pick a match."""
    out = []
    for item in raw.get("results", []) or []:
        rec = item.get("record", item) if isinstance(item, dict) else {}
        series_id = rec.get("series_id")
        if series_id is None:
            continue
        image = (rec.get("image") or {}).get("url") or {}
        out.append({
            "mu_series_id": int(series_id),
            "title": rec.get("title") or "",
            "year": rec.get("year"),
            "cover_url": image.get("thumb") or image.get("original"),
        })
    return out


def mu_fields(entry: dict[str, Any]) -> dict[str, Any]:
    """Maps MangaUpdates' extracted entry to the library's field names and value shapes."""
    status_word = entry.get("status")
    return {
        "title": entry.get("title") or None,
        "description": entry.get("description") or None,
        "authors": _names(entry.get("authors")),
        "artists": _names(entry.get("artists")),
        "genres": [g for g in (entry.get("genres") or []) if g],
        "status": STATUS_CODES.get(status_word) if status_word else None,
        "cover_url": entry.get("cover_image_url") or None,
    }


async def fetch_entry(mu_series_id: int, api: MangaUpdatesAPI) -> Optional[dict[str, Any]]:
    """Gets one MangaUpdates series and maps it. Returns None if the API has nothing usable."""
    raw = await api.get_series_details(mu_series_id)
    if not isinstance(raw, dict) or "title" not in raw:
        return None
    svc = MangaUpdatesService()
    fields = mu_fields(svc._extract_entry_data(raw))
    fields["artists"] = _names(svc._extract_artists(raw))  # not in the extracted entry, so read from the raw response
    return fields


def store_snapshot(record: SeriesMetadata, mu_series_id: int, fields: dict[str, Any]) -> None:
    record.mangaupdates = {
        "series_id": mu_series_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fields": fields,
    }


def compare(record: SeriesMetadata) -> dict[str, Any]:
    """Per field: the provider's value, MangaUpdates' value, and the value shown now with its origin."""
    base = record.base or {}
    current = record.current or {}
    mu = (record.mangaupdates or {}).get("fields") or {}
    rows = {}
    for name in COMPARE_FIELDS:
        shown = current.get(name) or {}
        rows[name] = {
            "provider": base.get(name),
            "mangaupdates": mu.get(name) if record.mangaupdates else None,
            "shown": shown.get("value"),
            "origin": shown.get("origin"),
        }
    return {
        "mangaupdates_series_id": (record.mangaupdates or {}).get("series_id"),
        "fetched_at": (record.mangaupdates or {}).get("fetched_at"),
        "fields": rows,
    }


def plan_choices(choices: dict[str, Any], record: SeriesMetadata) -> dict[str, tuple[Any, str]]:
    """Turns the user's picks into (value, origin) per field. Unknown fields and values are rejected by the caller."""
    base = record.base or {}
    mu = (record.mangaupdates or {}).get("fields") or {}
    out: dict[str, tuple[Any, str]] = {}
    for name, pick in choices.items():
        if name not in COMPARE_FIELDS:
            raise ValueError(f"unknown field: {name}")
        if pick == "provider":
            out[name] = (base.get(name), "provider")
        elif pick == "mangaupdates":
            if not record.mangaupdates:
                raise ValueError("no MangaUpdates entry is linked")
            out[name] = (mu.get(name), "mangaupdates")
        elif isinstance(pick, dict) and pick.get("origin") == "edited":
            out[name] = (pick.get("value"), "edited")
        else:
            raise ValueError(f"{name}: choose provider, mangaupdates, or edited with a value")
    return out
