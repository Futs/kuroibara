"""Download client management service."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mangaupdates import Download, DownloadClient

logger = logging.getLogger(__name__)


class BaseDownloadClient(ABC):
    """Base class for download clients."""

    def __init__(self, config: DownloadClient):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    @property
    def base_url(self) -> str:
        """Get base URL for the client."""
        protocol = "https" if self.config.use_ssl else "http"
        return f"{protocol}://{self.config.host}:{self.config.port}"

    @abstractmethod
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to the download client."""
        pass

    @abstractmethod
    async def add_torrent(self, torrent_data: bytes, download: Download) -> str:
        """Add torrent to client. Returns external download ID."""
        pass

    @abstractmethod
    async def add_magnet(self, magnet_link: str, download: Download) -> str:
        """Add magnet link to client. Returns external download ID."""
        pass

    @abstractmethod
    async def get_download_status(self, external_id: str) -> Dict[str, Any]:
        """Get download status from client."""
        pass

    @abstractmethod
    async def remove_download(
        self, external_id: str, delete_data: bool = False
    ) -> bool:
        """Remove download from client."""
        pass


class QBittorrentClient(BaseDownloadClient):
    """qBittorrent download client."""

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to qBittorrent."""
        try:
            # Login first
            login_success = await self._login()
            if not login_success:
                return False, "Authentication failed"

            # Test API version endpoint
            url = urljoin(self.base_url, "/api/v2/app/version")
            async with self.session.get(url) as response:
                if response.status == 200:
                    version = await response.text()
                    return True, f"Connected to qBittorrent {version}"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, str(e)

    async def _login(self) -> bool:
        """Login to qBittorrent."""
        if not self.config.username or not self.config.password:
            return False

        url = urljoin(self.base_url, "/api/v2/auth/login")
        data = {"username": self.config.username, "password": self.config.password}

        try:
            async with self.session.post(url, data=data) as response:
                return response.status == 200 and await response.text() == "Ok."
        except Exception:
            return False

    async def add_torrent(self, torrent_data: bytes, download: Download) -> str:
        """Add torrent file to qBittorrent."""
        await self._login()

        url = urljoin(self.base_url, "/api/v2/torrents/add")

        # Prepare form data
        data = aiohttp.FormData()
        data.add_field("torrents", torrent_data, filename=f"{download.title}.torrent")

        if self.config.default_category:
            data.add_field("category", self.config.default_category)

        if self.config.download_path:
            data.add_field("savepath", self.config.download_path)

        # Add any additional settings
        settings = self.config.settings or {}
        for key, value in settings.items():
            data.add_field(key, str(value))

        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                # qBittorrent doesn't return the hash directly, we need to calculate it
                # For now, return a placeholder - in practice, we'd calculate the torrent hash
                return download.torrent_hash or "unknown"
            else:
                raise Exception(f"Failed to add torrent: HTTP {response.status}")

    async def add_magnet(self, magnet_link: str, download: Download) -> str:
        """Add magnet link to qBittorrent."""
        await self._login()

        url = urljoin(self.base_url, "/api/v2/torrents/add")

        data = {"urls": magnet_link}

        if self.config.default_category:
            data["category"] = self.config.default_category

        if self.config.download_path:
            data["savepath"] = self.config.download_path

        # Add any additional settings
        settings = self.config.settings or {}
        data.update(settings)

        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                return download.torrent_hash or "unknown"
            else:
                raise Exception(f"Failed to add magnet: HTTP {response.status}")

    async def get_download_status(self, external_id: str) -> Dict[str, Any]:
        """Get download status from qBittorrent."""
        await self._login()

        url = urljoin(self.base_url, "/api/v2/torrents/info")
        params = {"hashes": external_id}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                torrents = await response.json()
                if torrents:
                    torrent = torrents[0]
                    return {
                        "status": self._map_qbt_status(torrent.get("state", "")),
                        "progress": torrent.get("progress", 0) * 100,
                        "total_size": torrent.get("size", 0),
                        "downloaded_size": torrent.get("downloaded", 0),
                        "download_speed": torrent.get("dlspeed", 0),
                        "eta": torrent.get("eta", 0),
                        "name": torrent.get("name", ""),
                    }

            return {"status": "unknown"}

    def _map_qbt_status(self, qbt_status: str) -> str:
        """Map qBittorrent status to our status."""
        status_map = {
            "downloading": "downloading",
            "uploading": "completed",
            "pausedDL": "paused",
            "pausedUP": "completed",
            "queuedDL": "queued",
            "queuedUP": "completed",
            "stalledDL": "downloading",
            "stalledUP": "completed",
            "checkingDL": "downloading",
            "checkingUP": "completed",
            "error": "failed",
        }
        return status_map.get(qbt_status, "unknown")

    async def remove_download(
        self, external_id: str, delete_data: bool = False
    ) -> bool:
        """Remove download from qBittorrent."""
        await self._login()

        endpoint = (
            "/api/v2/torrents/delete" if delete_data else "/api/v2/torrents/remove"
        )
        url = urljoin(self.base_url, endpoint)

        data = {
            "hashes": external_id,
            "deleteFiles": "true" if delete_data else "false",
        }

        async with self.session.post(url, data=data) as response:
            return response.status == 200


class DelugeClient(BaseDownloadClient):
    """Deluge download client."""

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to Deluge."""
        # Deluge uses JSON-RPC, implementation would be different
        # This is a placeholder implementation
        return False, "Deluge client not implemented yet"

    async def add_torrent(self, torrent_data: bytes, download: Download) -> str:
        """Add torrent to Deluge."""
        raise NotImplementedError("Deluge client not implemented yet")

    async def add_magnet(self, magnet_link: str, download: Download) -> str:
        """Add magnet to Deluge."""
        raise NotImplementedError("Deluge client not implemented yet")

    async def get_download_status(self, external_id: str) -> Dict[str, Any]:
        """Get download status from Deluge."""
        raise NotImplementedError("Deluge client not implemented yet")

    async def remove_download(
        self, external_id: str, delete_data: bool = False
    ) -> bool:
        """Remove download from Deluge."""
        raise NotImplementedError("Deluge client not implemented yet")


class TransmissionClient(BaseDownloadClient):
    """Transmission download client."""

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to Transmission."""
        # Transmission uses JSON-RPC, implementation would be different
        # This is a placeholder implementation
        return False, "Transmission client not implemented yet"

    async def add_torrent(self, torrent_data: bytes, download: Download) -> str:
        """Add torrent to Transmission."""
        raise NotImplementedError("Transmission client not implemented yet")

    async def add_magnet(self, magnet_link: str, download: Download) -> str:
        """Add magnet to Transmission."""
        raise NotImplementedError("Transmission client not implemented yet")

    async def get_download_status(self, external_id: str) -> Dict[str, Any]:
        """Get download status from Transmission."""
        raise NotImplementedError("Transmission client not implemented yet")

    async def remove_download(
        self, external_id: str, delete_data: bool = False
    ) -> bool:
        """Remove download from Transmission."""
        raise NotImplementedError("Transmission client not implemented yet")


class SABnzbdClient(BaseDownloadClient):
    """SABnzbd NZB download client."""

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test connection to SABnzbd."""
        try:
            url = urljoin(self.base_url, "/api")
            params = {
                "mode": "version",
                "apikey": self.config.api_key,
                "output": "json",
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    version = data.get("version", "unknown")
                    return True, f"Connected to SABnzbd {version}"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, str(e)

    async def add_torrent(self, torrent_data: bytes, download: Download) -> str:
        """SABnzbd doesn't support torrents."""
        raise NotImplementedError("SABnzbd doesn't support torrent files")

    async def add_magnet(self, magnet_link: str, download: Download) -> str:
        """SABnzbd doesn't support magnets."""
        raise NotImplementedError("SABnzbd doesn't support magnet links")

    async def add_nzb(self, nzb_data: bytes, download: Download) -> str:
        """Add NZB to SABnzbd."""
        url = urljoin(self.base_url, "/api")

        # Prepare form data
        data = aiohttp.FormData()
        data.add_field("mode", "addfile")
        data.add_field("apikey", self.config.api_key)
        data.add_field("output", "json")
        data.add_field("nzbfile", nzb_data, filename=f"{download.title}.nzb")

        if self.config.default_category:
            data.add_field("cat", self.config.default_category)

        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                result = await response.json()
                if result.get("status"):
                    return result.get("nzo_id", "unknown")
                else:
                    raise Exception(
                        f"SABnzbd error: {result.get('error', 'Unknown error')}"
                    )
            else:
                raise Exception(f"Failed to add NZB: HTTP {response.status}")

    async def get_download_status(self, external_id: str) -> Dict[str, Any]:
        """Get download status from SABnzbd."""
        url = urljoin(self.base_url, "/api")
        params = {"mode": "queue", "apikey": self.config.api_key, "output": "json"}

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                queue = data.get("queue", {})

                # Look for our download in the queue
                for slot in queue.get("slots", []):
                    if slot.get("nzo_id") == external_id:
                        return {
                            "status": self._map_sab_status(slot.get("status", "")),
                            "progress": float(slot.get("percentage", 0)),
                            "total_size": self._parse_size(slot.get("size", "0")),
                            "downloaded_size": self._parse_size(
                                slot.get("sizeleft", "0")
                            ),
                            "download_speed": self._parse_speed(
                                slot.get("kbpersec", "0")
                            ),
                            "eta": slot.get("timeleft", "0:00:00"),
                            "name": slot.get("filename", ""),
                        }

                # If not in queue, check history
                return await self._check_history(external_id)

            return {"status": "unknown"}

    def _map_sab_status(self, sab_status: str) -> str:
        """Map SABnzbd status to our status."""
        status_map = {
            "Downloading": "downloading",
            "Queued": "queued",
            "Paused": "paused",
            "Completed": "completed",
            "Failed": "failed",
            "Verifying": "downloading",
            "Repairing": "downloading",
            "Extracting": "downloading",
        }
        return status_map.get(sab_status, "unknown")

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        # SABnzbd returns sizes like "1.2 GB", "500 MB", etc.
        # This is a simplified parser
        try:
            parts = size_str.strip().split()
            if len(parts) == 2:
                value = float(parts[0])
                unit = parts[1].upper()

                multipliers = {
                    "B": 1,
                    "KB": 1024,
                    "MB": 1024**2,
                    "GB": 1024**3,
                    "TB": 1024**4,
                }

                return int(value * multipliers.get(unit, 1))
        except (ValueError, KeyError):
            pass

        return 0

    def _parse_speed(self, speed_str: str) -> int:
        """Parse speed string to bytes per second."""
        try:
            # SABnzbd returns speed in KB/s
            return int(float(speed_str) * 1024)
        except (ValueError, TypeError):
            return 0

    async def _check_history(self, external_id: str) -> Dict[str, Any]:
        """Check download history for completed/failed downloads."""
        url = urljoin(self.base_url, "/api")
        params = {
            "mode": "history",
            "apikey": self.config.api_key,
            "output": "json",
            "limit": 100,
        }

        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                history = data.get("history", {})

                for slot in history.get("slots", []):
                    if slot.get("nzo_id") == external_id:
                        return {
                            "status": self._map_sab_status(slot.get("status", "")),
                            "progress": (
                                100.0 if slot.get("status") == "Completed" else 0.0
                            ),
                            "total_size": self._parse_size(slot.get("size", "0")),
                            "downloaded_size": self._parse_size(slot.get("size", "0")),
                            "name": slot.get("name", ""),
                        }

        return {"status": "unknown"}

    async def remove_download(
        self, external_id: str, delete_data: bool = False
    ) -> bool:
        """Remove download from SABnzbd."""
        url = urljoin(self.base_url, "/api")
        params = {
            "mode": "queue",
            "name": "delete",
            "value": external_id,
            "apikey": self.config.api_key,
            "output": "json",
        }

        if delete_data:
            params["del_files"] = "1"

        async with self.session.get(url, params=params) as response:
            return response.status == 200


class DownloadClientService:
    """Service for managing download clients."""

    CLIENT_IMPLEMENTATIONS = {
        "qbittorrent": QBittorrentClient,
        "deluge": DelugeClient,
        "transmission": TransmissionClient,
        "sabnzbd": SABnzbdClient,
    }

    async def get_client(self, client_config: DownloadClient) -> BaseDownloadClient:
        """Get download client instance."""
        implementation = self.CLIENT_IMPLEMENTATIONS.get(
            client_config.implementation.lower()
        )
        if not implementation:
            raise ValueError(
                f"Unsupported download client: {client_config.implementation}"
            )

        return implementation(client_config)

    async def test_all_clients(
        self, db: AsyncSession
    ) -> Dict[str, tuple[bool, Optional[str]]]:
        """Test all configured download clients."""
        result = await db.execute(
            select(DownloadClient).where(DownloadClient.is_enabled.is_(True))
        )
        clients = result.scalars().all()

        results = {}
        for client_config in clients:
            try:
                async with await self.get_client(client_config) as client:
                    success, message = await client.test_connection()
                    results[client_config.name] = (success, message)

                    # Update health status
                    client_config.is_healthy = success
                    client_config.error_message = message if not success else None
                    client_config.last_test = datetime.utcnow()
            except Exception as e:
                results[client_config.name] = (False, str(e))
                client_config.is_healthy = False
                client_config.error_message = str(e)
                client_config.last_test = datetime.utcnow()

        await db.commit()
        return results

    async def get_best_client(
        self, db: AsyncSession, client_type: str
    ) -> Optional[DownloadClient]:
        """Get the best available client for the given type."""
        result = await db.execute(
            select(DownloadClient)
            .where(
                (DownloadClient.client_type == client_type)
                & (DownloadClient.is_enabled.is_(True))
                & (DownloadClient.is_healthy.is_(True))
            )
            .order_by(DownloadClient.priority.asc())
        )

        return result.scalars().first()


# Global service instance
download_client_service = DownloadClientService()
