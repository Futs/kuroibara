"""First-run setup. Open only until setup is complete, and each step needs the one-time token from the log."""
import functools
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import groups, setup as setup_state
from app.core.config import settings
from app.core.deps import get_db
from app.models.user import User

router = APIRouter()


class TokenBody(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


class AdminPasswordBody(TokenBody):
    password: str = Field(..., min_length=12, max_length=200)


class FirstUserBody(TokenBody):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=12, max_length=200)
    role: str = Field("user", pattern="^(admin|user)$")


class ProviderBody(TokenBody):
    # A module from the catalog (for example en/mangakatana), or null to add a provider later.
    module: Optional[str] = Field(None, pattern=r"^[a-z0-9]+/[a-z0-9_]+$")


class LibraryBody(TokenBody):
    name: str = Field(..., min_length=1, max_length=100)
    # Must be inside the server's storage root. Created if missing.
    path: str = Field(..., min_length=1, max_length=1000)


def _guard(fn):
    """Maps setup errors to HTTP: wrong token 403, wrong step 409. functools.wraps keeps FastAPI's signature."""
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        except (ValueError, groups.GroupError) as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return wrapper


async def _open_or_410(db: AsyncSession) -> None:
    if await setup_state.completed(db):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="setup is already complete")


@router.get("/status")
async def status_(db: AsyncSession = Depends(get_db)) -> Any:
    done = await setup_state.completed(db)
    return {
        "required": not done,
        "step": None if done else await setup_state.current_step(db),
        "steps": list(setup_state.STEPS),
    }


@router.post("/admin-password")
@_guard
async def admin_password(body: AdminPasswordBody, db: AsyncSession = Depends(get_db)) -> Any:
    await _open_or_410(db)
    await setup_state.check_token(db, body.token)
    await setup_state.expect_step(db, "admin_password")
    await setup_state.set_admin_password(db, body.password)
    await setup_state.advance(db, "first_user")
    await db.commit()
    return {"step": "first_user"}


@router.post("/first-user", status_code=status.HTTP_201_CREATED)
@_guard
async def first_user(body: FirstUserBody, db: AsyncSession = Depends(get_db)) -> Any:
    await _open_or_410(db)
    await setup_state.check_token(db, body.token)
    await setup_state.expect_step(db, "first_user")
    taken = (await db.execute(select(User).where(
        (User.username == body.username) | (User.email == body.email)))).scalars().first()
    if taken is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username or email already in use")
    from app.core.security import get_password_hash
    user = User(username=body.username, email=body.email, hashed_password=get_password_hash(body.password),
                is_active=True)
    db.add(user)
    await db.flush()
    await groups.set_role(db, user, body.role)
    await setup_state.advance(db, "provider")
    await db.commit()
    return {"id": str(user.id), "username": user.username,
            "roles": ["admin", "user"] if body.role == "admin" else ["user"]}


@router.post("/provider")
@_guard
async def provider(body: ProviderBody, db: AsyncSession = Depends(get_db)) -> Any:
    """Optional: installs one provider from the catalog. Needs the extension host to be configured."""
    await _open_or_410(db)
    await setup_state.check_token(db, body.token)
    await setup_state.expect_step(db, "provider")
    installed = None
    if body.module:
        if not settings.EXTENSION_HOST_TOKEN:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                detail="the extension host is not configured; skip this step and add a provider later")
        from app.sources.host_client import ExtensionHostClient, ExtensionHostError
        host = ExtensionHostClient(settings.EXTENSION_HOST_URL, settings.EXTENSION_HOST_TOKEN)
        try:
            installed = await host.install(body.module, source="upstream")
        except ExtensionHostError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message)
        finally:
            await host.aclose()
    await setup_state.advance(db, "library")
    await db.commit()
    return {"step": "library", "installed": installed}


@router.post("/library")
@_guard
async def library(body: LibraryBody, db: AsyncSession = Depends(get_db)) -> Any:
    """Names the first library and checks its folder is inside the storage root."""
    import os
    from app.models.access import AppSetting

    await _open_or_410(db)
    await setup_state.check_token(db, body.token)
    await setup_state.expect_step(db, "library")
    root = os.path.realpath(settings.STORAGE_PATH)
    target = os.path.realpath(os.path.join(root, body.path) if not os.path.isabs(body.path) else body.path)
    if os.path.commonpath([root, target]) != root or target == root:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"library folder must be inside {root}")
    try:
        os.makedirs(target, exist_ok=True)
    except OSError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"cannot create the library folder: {e.strerror or e}")
    row = await db.get(AppSetting, setup_state.LIBRARY_KEY)
    value = {"name": body.name, "path": target}
    if row is None:
        db.add(AppSetting(key=setup_state.LIBRARY_KEY, value=value))
    else:
        row.value = value
    await setup_state.advance(db, "finish")
    await db.commit()
    return {"step": "finish", "library": value}


@router.post("/finish")
@_guard
async def finish(body: TokenBody, db: AsyncSession = Depends(get_db)) -> Any:
    await _open_or_410(db)
    await setup_state.check_token(db, body.token)
    await setup_state.expect_step(db, "finish")
    await setup_state.complete(db)
    return {"required": False}
