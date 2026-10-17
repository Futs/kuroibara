"""Admin: list users with their groups, and change a user's role. Superusers only."""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import groups
from app.core.deps import get_db
from app.models.access import UserGroup
from app.models.user import User
from app.sources.deps import require_superuser

router = APIRouter()


class RoleBody(BaseModel):
    role: str  # "admin" (admin and user) or "user"


async def _roles(db: AsyncSession, user_id) -> list[str]:
    names = []
    for name in groups.ROLES:
        if await groups.is_member(db, user_id, name):
            names.append(name)
    return names


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_superuser)) -> Any:
    users = (await db.execute(select(User).order_by(User.username))).scalars().all()
    return {"items": [{"id": str(u.id), "username": u.username, "email": u.email, "is_active": u.is_active,
                       "roles": await _roles(db, u.id)} for u in users]}


@router.put("/users/{user_id}/role")
async def set_role(
    user_id: UUID,
    body: RoleBody,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_superuser),
) -> Any:
    if body.role not in groups.ROLES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="role must be admin or user")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    try:
        await groups.set_role(db, user, body.role)
    except groups.GroupError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    await db.commit()
    return {"id": str(user.id), "username": user.username, "roles": await _roles(db, user.id)}
