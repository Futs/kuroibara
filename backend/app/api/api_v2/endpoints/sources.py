"""Extension sources: catalog, install state, health, and browse (search, details, pages).

Thin proxy to the extension host. The host is the source of truth for installs and health (D6).
Module names contain a slash (en/mangakatana), so the module is a path parameter with `:path`.
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.user import User
from app.sources.deps import get_host_client, host_error
from app.sources.host_client import ExtensionHostClient, ExtensionHostError

router = APIRouter()


class UrlBody(BaseModel):
    url: str


async def _call(coro):
    try:
        return await coro
    except ExtensionHostError as e:
        raise host_error(e)


@router.get("/catalog")
async def catalog(
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    """Upstream catalog with local and installed flags. 404 until the upstream index has been fetched."""
    return await _call(host.upstream())


@router.get("/installed")
async def installed(
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.installed())


@router.post("/{module:path}/install")
async def install(
    module: str,
    source: str = Query("upstream", pattern="^(upstream|local)$"),
    version_code: Optional[int] = None,
    hash: Optional[str] = None,
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.install(module, source=source, version_code=version_code, hash=hash))


@router.delete("/{module:path}")
async def uninstall(
    module: str,
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.uninstall(module))


@router.post("/{module:path}/enable")
async def enable(
    module: str,
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.enable(module))


@router.post("/{module:path}/disable")
async def disable(
    module: str,
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.disable(module))


@router.post("/{module:path}/test")
async def test(
    module: str,
    q: str = Query("one", min_length=1, max_length=200),
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    """Runs the four-step probe. A failing source is reported in the health record, not hidden."""
    return await _call(host.test(module, query=q))


@router.post("/{module:path}/search")
async def search(
    module: str,
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1, le=100),
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.search(module, q, page))


@router.post("/{module:path}/details")
async def details(
    module: str,
    body: UrlBody,
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.details(module, body.url))


@router.post("/{module:path}/pages")
async def pages(
    module: str,
    body: UrlBody,
    host: ExtensionHostClient = Depends(get_host_client),
    _user: User = Depends(get_current_user),
) -> Any:
    return await _call(host.pages(module, body.url))
