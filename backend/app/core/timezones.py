"""Time zones: a user's own zone, else the server's TZ, else UTC.

Events are stored in UTC. The local day is computed when an event is written, with the zone in force at that moment,
and stored with it. Changing a user's zone later does not move past days; the events keep their UTC time, so the
rollup can be rebuilt if needed.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = ZoneInfo("UTC")


def parse_zone(name: str) -> ZoneInfo:
    """IANA name to ZoneInfo. Raises ValueError for anything that is not a known zone."""
    if not name or not name.strip():
        raise ValueError("time zone name is empty")
    try:
        return ZoneInfo(name.strip())
    except (ZoneInfoNotFoundError, ValueError, OSError) as e:
        raise ValueError(f"unknown time zone: {name}") from e


def server_zone() -> ZoneInfo:
    """The zone from the TZ environment variable (set in docker-compose). UTC if unset or unknown."""
    name = os.environ.get("TZ")
    if name:
        try:
            return parse_zone(name)
        except ValueError:
            pass
    return UTC


def effective_zone(user_timezone: Optional[str]) -> tuple[ZoneInfo, str]:
    """(zone, source). source is 'user', 'server' or 'utc'."""
    if user_timezone:
        try:
            return parse_zone(user_timezone), "user"
        except ValueError:
            pass  # a stored name that is no longer valid falls back, rather than failing the request
    zone = server_zone()
    return zone, ("utc" if zone is UTC else "server")


def local_day(at: datetime, zone: ZoneInfo) -> date:
    """The calendar day of `at` in `zone`. Naive datetimes are taken as UTC."""
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    return at.astimezone(zone).date()
