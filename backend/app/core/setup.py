"""First-run setup: the one-time token, the steps, and the switch that holds the API closed until setup is done.

Steps, in order: admin_password -> first_user -> provider -> library -> finish.
The token is random, shown once in the server log, stored only as a SHA-256 hash, and rotated on each start
until setup completes. Setup is complete when the setup_completed key exists in app_settings.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import groups
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.access import AppSetting
from app.models.user import User

logger = logging.getLogger("setup")

COMPLETED_KEY = "setup_completed"
STEP_KEY = "setup_step"
TOKEN_KEY = "setup_token_hash"
LIBRARY_KEY = "library"
STEPS = ("admin_password", "first_user", "provider", "library", "finish")
ADMIN_USERNAME = "admin"
UNUSABLE_PASSWORD = "!setup-pending"  # not a valid hash, so the admin cannot log in until the password is set

# Read by the API guard. Refreshed at startup and when setup completes.
_required = False


def required() -> bool:
    return _required


async def _setting(db: AsyncSession, key: str):
    row = await db.get(AppSetting, key)
    return None if row is None else row.value


async def _put(db: AsyncSession, key: str, value) -> None:
    row = await db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=value))
    else:
        row.value = value
    await db.flush()


async def completed(db: AsyncSession) -> bool:
    return (await _setting(db, COMPLETED_KEY)) is not None


async def current_step(db: AsyncSession) -> Optional[str]:
    value = await _setting(db, STEP_KEY)
    return value.get("step") if isinstance(value, dict) else None


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def refresh(db: AsyncSession) -> None:
    global _required
    _required = settings.SETUP_ENABLED and not await completed(db)


async def bootstrap(db: AsyncSession) -> Optional[str]:
    """Called at startup. If setup is not complete: makes sure an admin account exists, rotates the token,
    and returns the new token to show once. Returns None when setup is already complete."""
    await refresh(db)
    if not _required:
        return None
    admin = (await db.execute(select(User).where(User.username == ADMIN_USERNAME))).scalar_one_or_none()
    if admin is None:
        admin = User(username=ADMIN_USERNAME, email="admin@setup.invalid",
                     hashed_password=UNUSABLE_PASSWORD, is_active=True)
        db.add(admin)
        await db.flush()
        await groups.add(db, admin, groups.ADMIN)
        await groups.add(db, admin, groups.USER)
    token = secrets.token_urlsafe(32)
    await _put(db, TOKEN_KEY, {"hash": _hash(token)})
    await _put(db, STEP_KEY, {"step": current_step_or_first(await current_step(db))})
    await db.commit()
    return token


def current_step_or_first(step: Optional[str]) -> str:
    return step if step in STEPS else STEPS[0]


async def check_token(db: AsyncSession, token: str) -> None:
    """Raises PermissionError unless the token matches the stored hash. Constant-time comparison."""
    stored = await _setting(db, TOKEN_KEY)
    if not stored or not token or not hmac.compare_digest(stored.get("hash", ""), _hash(token)):
        raise PermissionError("invalid setup token")


async def expect_step(db: AsyncSession, step: str) -> None:
    current = await current_step(db)
    if current != step:
        raise ValueError(f"setup is at step '{current}', not '{step}'")


async def advance(db: AsyncSession, to: str) -> None:
    await _put(db, STEP_KEY, {"step": to})


async def set_admin_password(db: AsyncSession, password: str) -> None:
    admin = (await db.execute(select(User).where(User.username == ADMIN_USERNAME))).scalar_one()
    admin.hashed_password = get_password_hash(password)
    await db.flush()


async def complete(db: AsyncSession) -> None:
    """Marks setup done and removes the token. After this the API is open to everyone with an account."""
    global _required
    await _put(db, COMPLETED_KEY, {"completed": True})
    await db.execute(AppSetting.__table__.delete().where(AppSetting.key.in_([TOKEN_KEY, STEP_KEY])))
    await db.commit()
    _required = False


def announce(token: str, port_hint: str = "/setup") -> None:
    """Prints the token once, in a box, so it is easy to find in the log."""
    line = "=" * 72
    logger.warning(
        "\n%s\nFIRST-RUN SETUP REQUIRED\nOpen %s and use this one-time token:\n\n    %s\n\n"
        "It is shown once. A new token is issued on each start until setup completes.\n%s",
        line, port_hint, token, line,
    )
