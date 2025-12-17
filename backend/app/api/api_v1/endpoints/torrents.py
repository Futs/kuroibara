"""
Torrent search and download endpoints.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.services.download_clients import DownloadClientService
from app.core.services.torrent_indexers import torrent_indexer_service
from app.models.mangaupdates import Download, DownloadClient
from app.models.user import User
from app.schemas.torrent import (
    IndexerHealthResponse,
    TorrentDownloadRequest,
    TorrentDownloadResponse,
    TorrentSearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=TorrentSearchResponse)
async def search_torrents(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(
        None, description="Torrent category (manga, anime, all)"
    ),
    indexer: Optional[str] = Query(None, description="Specific indexer to search"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results per indexer"),
    current_user: User = Depends(get_current_user),
):
    """
    Search for torrents across configured indexers.

    This endpoint searches torrent indexers like Nyaa.si for manga content
    and returns results with metadata for download consideration.
    """
    try:
        if indexer:
            # Search specific indexer
            indexer_obj = torrent_indexer_service.get_indexer(indexer)
            if not indexer_obj:
                raise HTTPException(
                    status_code=404, detail=f"Indexer '{indexer}' not found"
                )

            async with indexer_obj:
                results = await indexer_obj.search(query, category, limit)
                indexer_results = {indexer: results}
        else:
            # Search all indexers
            indexer_results = await torrent_indexer_service.search_all(
                query, category, limit
            )

        # Calculate totals
        total_results = sum(len(results) for results in indexer_results.values())

        logger.info(f"Torrent search for '{query}' returned {total_results} results")

        return TorrentSearchResponse(
            query=query,
            category=category,
            total_results=total_results,
            indexer_results=indexer_results,
        )

    except Exception as e:
        logger.error(f"Error searching torrents: {e}")
        raise HTTPException(status_code=500, detail=f"Torrent search failed: {str(e)}")


@router.post("/download", response_model=TorrentDownloadResponse)
async def download_torrent(
    request: TorrentDownloadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Download a torrent using configured download client.

    This endpoint adds a torrent to the configured download client
    (qBittorrent, Deluge, etc.) and tracks the download in the database.
    """
    try:
        # Get download client
        download_client = await db.get(DownloadClient, request.client_id)
        if not download_client:
            raise HTTPException(status_code=404, detail="Download client not found")

        if not download_client.is_enabled:
            raise HTTPException(status_code=400, detail="Download client is disabled")

        # Create download record
        download = Download(
            title=request.title,
            manga_id=request.manga_id,
            user_id=current_user.id,
            client_id=download_client.id,
            download_type="torrent",
            status="pending",
            external_url=request.magnet_link or request.torrent_url,
            metadata={
                "indexer": request.indexer,
                "info_hash": request.info_hash,
                "size": request.size,
                "seeders": request.seeders,
                "leechers": request.leechers,
                "category": request.category,
            },
        )

        db.add(download)
        await db.flush()  # Get the ID

        # Initialize download client service
        client_service = DownloadClientService()
        client = await client_service.get_client(download_client)

        # Add torrent to client
        if request.magnet_link:
            # Use magnet link
            external_id = await client.add_magnet(request.magnet_link, download)
        elif request.torrent_url:
            # Download torrent file and add
            async with client.session.get(request.torrent_url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to download torrent file: HTTP {response.status}",
                    )
                torrent_data = await response.read()
                external_id = await client.add_torrent(torrent_data, download)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either magnet_link or torrent_url must be provided",
            )

        # Update download with external ID
        download.external_id = external_id
        download.status = "downloading"

        await db.commit()

        logger.info(f"Started torrent download: {request.title} (ID: {download.id})")

        return TorrentDownloadResponse(
            download_id=download.id,
            external_id=external_id,
            status="downloading",
            message="Torrent added to download client successfully",
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error downloading torrent: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start torrent download: {str(e)}"
        )


@router.get("/indexers", response_model=List[str])
async def list_indexers(
    current_user: User = Depends(get_current_user),
):
    """
    List available torrent indexers.
    """
    return torrent_indexer_service.list_indexers()


@router.get("/indexers/health", response_model=IndexerHealthResponse)
async def check_indexer_health(
    current_user: User = Depends(get_current_user),
):
    """
    Check health status of all torrent indexers.
    """
    try:
        health_results = await torrent_indexer_service.test_all_indexers()

        healthy_count = sum(
            1 for is_healthy, _ in health_results.values() if is_healthy
        )
        total_count = len(health_results)

        overall_status = (
            "healthy"
            if healthy_count == total_count
            else ("degraded" if healthy_count > 0 else "unhealthy")
        )

        return IndexerHealthResponse(
            status=overall_status,
            healthy_count=healthy_count,
            total_count=total_count,
            indexers=health_results,
        )

    except Exception as e:
        logger.error(f"Error checking indexer health: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check indexer health: {str(e)}"
        )


@router.post("/indexers/{indexer_name}/test")
async def test_indexer(
    indexer_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Test connection to a specific torrent indexer.
    """
    indexer = torrent_indexer_service.get_indexer(indexer_name)
    if not indexer:
        raise HTTPException(
            status_code=404, detail=f"Indexer '{indexer_name}' not found"
        )

    try:
        async with indexer:
            is_healthy, message = await indexer.test_connection()

        return {"indexer": indexer_name, "healthy": is_healthy, "message": message}

    except Exception as e:
        logger.error(f"Error testing indexer {indexer_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test indexer: {str(e)}")
