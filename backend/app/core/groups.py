"""Group membership rules. `admin` and `user` are the only groups for now.

Membership is the record. users.is_superuser is kept equal to "is in admin", because the existing checks use it.
Two rules protect the server: a user always keeps the `user` group, and the last admin cannot be removed.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import Group, UserGroup
from app.models.user import User

ADMIN = "admin"
USER = "user"
ROLES = (ADMIN, USER)


class GroupError(Exception):
    pass


DEFAULT_GROUPS = {ADMIN: (1, "Full access, including server and user management"),
                  USER: (2, "Use the library and change own settings")}


async def _group_id(db: AsyncSession, name: str) -> int:
    gid = (await db.execute(select(Group.id).where(Group.name == name))).scalar_one_or_none()
    if gid is None and name in DEFAULT_GROUPS:
        # The migration seeds these. Databases built by create_all (tests, fresh dev setups) get them here.
        fixed_id, description = DEFAULT_GROUPS[name]
        db.add(Group(id=fixed_id, name=name, description=description))
        await db.flush()
        gid = fixed_id
    if gid is None:
        raise GroupError(f"unknown group: {name}")
    return gid


async def member_ids(db: AsyncSession, name: str) -> list:
    gid = await _group_id(db, name)
    return list((await db.execute(select(UserGroup.user_id).where(UserGroup.group_id == gid))).scalars().all())


async def is_member(db: AsyncSession, user_id, name: str) -> bool:
    gid = await _group_id(db, name)
    row = await db.get(UserGroup, (user_id, gid))
    return row is not None


async def admin_count(db: AsyncSession) -> int:
    gid = await _group_id(db, ADMIN)
    return int((await db.execute(
        select(func.count()).select_from(UserGroup).join(User, User.id == UserGroup.user_id)
        .where(UserGroup.group_id == gid, User.is_active.is_(True))
    )).scalar_one())


async def add(db: AsyncSession, user: User, name: str) -> None:
    gid = await _group_id(db, name)
    if await db.get(UserGroup, (user.id, gid)) is None:
        db.add(UserGroup(user_id=user.id, group_id=gid))
    if name == ADMIN:
        user.is_superuser = True
    await db.flush()


async def remove(db: AsyncSession, user: User, name: str) -> None:
    if name == USER:
        raise GroupError("every user stays in the user group")
    gid = await _group_id(db, name)
    if name == ADMIN and await is_member(db, user.id, ADMIN) and await admin_count(db) <= 1:
        raise GroupError("the last admin cannot be removed from the admin group")
    row = await db.get(UserGroup, (user.id, gid))
    if row is not None:
        await db.delete(row)
    if name == ADMIN:
        user.is_superuser = False
    await db.flush()


async def set_role(db: AsyncSession, user: User, role: str) -> None:
    """role is "admin" (admin and user) or "user" (user only)."""
    if role not in ROLES:
        raise GroupError(f"unknown role: {role}")
    await add(db, user, USER)
    if role == ADMIN:
        await add(db, user, ADMIN)
    else:
        await remove(db, user, ADMIN)


async def join_default(db: AsyncSession, user: User) -> None:
    """Every new account joins `user`. Used by registration and the first-run wizard."""
    await add(db, user, USER)
