"""Async client for the extension host HTTP API (extension-host/, see docs/TODO_TACHIYOMI_EXTENSIONS.md).

The host is the source of truth for what is installed, enabled and healthy. Kuroibara asks it;
it does not keep its own copy of installs. Health is shown to the user, never used to hide a source (D6).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import quote

import httpx


class ExtensionHostError(Exception):
    """The host answered with an error status, or could not be reached."""

    def __init__(self, status: Optional[int], message: str):
        super().__init__(f"extension host: {status or 'unreachable'}: {message}")
        self.status = status
        self.message = message


@dataclass(frozen=True)
class ImageFetch:
    status: int  # the extension's status for the image: 200, or 206 when a range was honoured
    content_type: Optional[str]
    body: bytes


class ExtensionHostClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 130.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        if not token:
            raise ExtensionHostError(None, "EXTENSION_HOST_TOKEN is not set")
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "ExtensionHostClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            resp = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise ExtensionHostError(None, str(e)) from e
        if resp.status_code >= 400:
            try:
                message = resp.json().get("error", resp.text)
            except ValueError:
                message = resp.text
            raise ExtensionHostError(resp.status_code, message)
        return resp.json()

    @staticmethod
    def _module_path(module: str) -> str:
        # Modules contain a slash (en/mangakatana); the host reads the action from the last path segment.
        return "/".join(quote(part, safe="") for part in module.split("/"))

    async def health(self) -> bool:
        try:
            return (await self._request("GET", "/health")).get("ok") is True
        except ExtensionHostError:
            return False

    async def catalog(self) -> dict[str, Any]:
        """Local build index: modules with versions and sources."""
        return await self._request("GET", "/catalog")

    async def upstream(self) -> dict[str, Any]:
        """Upstream Keiyoushi catalog with local/installed flags. 404 if not fetched yet."""
        return await self._request("GET", "/upstream")

    async def installed(self) -> dict[str, Any]:
        """{"extensions": {module: {...}}}"""
        return await self._request("GET", "/extensions")

    async def install(self, module: str, *, source: str = "upstream", version_code: Optional[int] = None,
                      hash: Optional[str] = None) -> dict[str, Any]:
        params: dict[str, Any] = {"source": source}
        if version_code is not None:
            params["version_code"] = version_code
        if hash is not None:
            params["hash"] = hash
        return await self._request("POST", f"/extensions/{self._module_path(module)}/install", params=params)

    async def uninstall(self, module: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/extensions/{self._module_path(module)}")

    async def enable(self, module: str) -> dict[str, Any]:
        return await self._request("POST", f"/extensions/{self._module_path(module)}/enable")

    async def disable(self, module: str) -> dict[str, Any]:
        return await self._request("POST", f"/extensions/{self._module_path(module)}/disable")

    async def test(self, module: str, query: str = "one") -> dict[str, Any]:
        """Runs the four-step probe on the host and returns the updated install (with health)."""
        return await self._request("POST", f"/extensions/{self._module_path(module)}/test", params={"q": query})

    async def search(self, module: str, query: str, page: int = 1) -> dict[str, Any]:
        """Search one installed, enabled source. Returns {source, lang, has_next, mangas: [...]}."""
        return await self._request("POST", f"/extensions/{self._module_path(module)}/search",
                                   params={"q": query, "page": page})

    async def details(self, module: str, url: str) -> dict[str, Any]:
        """Details and chapters for a title URL from search. Returns {manga, chapters: [...]}."""
        return await self._request("POST", f"/extensions/{self._module_path(module)}/details", json={"url": url})

    async def pages(self, module: str, chapter_url: str) -> dict[str, Any]:
        return await self._request("POST", f"/extensions/{self._module_path(module)}/pages",
                                   json={"url": chapter_url})

    async def image(self, module: str, *, image_url: Optional[str], url: str = "", index: int = 0,
                    offset: int = 0) -> ImageFetch:
        """One page image as the extension fetches it. offset > 0 asks for the rest (HTTP Range)."""
        payload = {"url": url, "index": index, "offset": offset}
        if image_url:
            payload["image_url"] = image_url
        try:
            resp = await self._client.post(f"/extensions/{self._module_path(module)}/image", json=payload)
        except httpx.HTTPError as e:
            raise ExtensionHostError(None, str(e)) from e
        if resp.status_code >= 400:
            try:
                message = resp.json().get("error", resp.text)
            except ValueError:
                message = resp.text
            raise ExtensionHostError(resp.status_code, message)
        upstream = int(resp.headers.get("X-Upstream-Status", resp.status_code))
        return ImageFetch(status=upstream, content_type=resp.headers.get("Content-Type"), body=resp.content)

    async def catalog_settings(self) -> dict[str, Any]:
        return await self._request("GET", "/catalog/settings")

    async def set_catalog_settings(self, url: Optional[str]) -> dict[str, Any]:
        """url None restores the built-in catalog."""
        return await self._request("PUT", "/catalog/settings", json={"url": url})

    async def refresh_catalog(self) -> dict[str, Any]:
        return await self._request("POST", "/catalog/refresh")

    async def import_jar(self, module: str, data: bytes) -> dict[str, Any]:
        """Uploads a Keiyoushi-compatible JAR for a module. The host checks it before keeping it."""
        try:
            resp = await self._client.post(f"/extensions/{self._module_path(module)}/import", content=data,
                                           headers={"Content-Type": "application/octet-stream"})
        except httpx.HTTPError as e:
            raise ExtensionHostError(None, str(e)) from e
        if resp.status_code >= 400:
            try:
                message = resp.json().get("error", resp.text)
            except ValueError:
                message = resp.text
            raise ExtensionHostError(resp.status_code, message)
        return resp.json()

    async def health_of(self, module: str) -> dict[str, Any]:
        return await self._request("GET", f"/extensions/{self._module_path(module)}/health")
