"""FastAPI dependencies for the extension host."""
from typing import AsyncGenerator

from fastapi import HTTPException, status

from fastapi import Depends

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.sources.host_client import ExtensionHostClient, ExtensionHostError


async def get_host_client() -> AsyncGenerator[ExtensionHostClient, None]:
    if not settings.EXTENSION_HOST_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Extension host is not configured (EXTENSION_HOST_TOKEN)",
        )
    try:
        client = ExtensionHostClient(settings.EXTENSION_HOST_URL, settings.EXTENSION_HOST_TOKEN)
    except ExtensionHostError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    try:
        yield client
    finally:
        await client.aclose()


async def require_superuser(user: User = Depends(get_current_user)) -> User:
    """Source management changes things for every user (installs, catalog, imports), so it is for superusers."""
    if not getattr(user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="superuser required")
    return user


def make_download_worker(host: ExtensionHostClient, **kwargs):
    """A download worker bound to the configured storage directory."""
    from app.sources.download_worker import SourceDownloadWorker

    return SourceDownloadWorker(host, settings.SOURCE_DOWNLOAD_DIR, **kwargs)


def host_error(e: ExtensionHostError) -> HTTPException:
    """Maps a host failure to an HTTP status. Unreachable host is 503; host statuses pass through."""
    if e.status is None:
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    mapped = e.status if e.status in (400, 401, 404, 405, 409, 413, 422, 502, 503, 504) else 502
    return HTTPException(status_code=mapped, detail=e.message)
