"""The signed-in user's settings. Currently: the time zone used for "today", the week, the month and the year."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.timezones import effective_zone, parse_zone
from app.models.user import User

router = APIRouter()


class TimezoneBody(BaseModel):
    # IANA name such as Europe/Amsterdam. null clears the preference and uses the server's zone.
    timezone: Optional[str] = None


def _settings_json(stored: Optional[str]) -> dict[str, Any]:
    zone, source = effective_zone(stored)
    return {"timezone": stored, "effective_timezone": str(zone), "timezone_source": source}


@router.get("/settings")
async def get_settings(user: User = Depends(get_current_user)) -> Any:
    return _settings_json(getattr(user, "timezone", None))


@router.put("/settings/timezone")
async def set_timezone(
    body: TimezoneBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Any:
    if body.timezone is not None:
        try:
            zone = parse_zone(body.timezone)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
        stored = str(zone)
    else:
        stored = None
    row = await db.get(User, user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    row.timezone = stored
    await db.commit()
    return _settings_json(stored)
