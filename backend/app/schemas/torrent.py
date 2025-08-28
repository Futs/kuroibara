"""
Pydantic schemas for torrent-related operations.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field


class TorrentResultSchema(BaseModel):
    """Schema for a single torrent search result."""
    
    title: str = Field(..., description="Torrent title")
    magnet_link: str = Field(..., description="Magnet link")
    torrent_url: Optional[str] = Field(None, description="Direct torrent download URL")
    size: str = Field(..., description="File size (human readable)")
    size_bytes: int = Field(..., description="File size in bytes")
    seeders: int = Field(..., description="Number of seeders")
    leechers: int = Field(..., description="Number of leechers")
    upload_date: datetime = Field(..., description="Upload date")
    category: str = Field(..., description="Torrent category")
    indexer: str = Field(..., description="Source indexer")
    info_hash: Optional[str] = Field(None, description="Torrent info hash")
    description: Optional[str] = Field(None, description="Torrent description")
    uploader: Optional[str] = Field(None, description="Uploader name")
    
    class Config:
        from_attributes = True


class TorrentSearchRequest(BaseModel):
    """Schema for torrent search request."""
    
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="Torrent category")
    indexer: Optional[str] = Field(None, description="Specific indexer to search")
    limit: int = Field(50, ge=1, le=100, description="Maximum results per indexer")


class TorrentSearchResponse(BaseModel):
    """Schema for torrent search response."""
    
    query: str = Field(..., description="Original search query")
    category: Optional[str] = Field(None, description="Search category")
    total_results: int = Field(..., description="Total number of results")
    indexer_results: Dict[str, List[TorrentResultSchema]] = Field(
        ..., description="Results grouped by indexer"
    )


class TorrentDownloadRequest(BaseModel):
    """Schema for torrent download request."""
    
    title: str = Field(..., description="Torrent title")
    manga_id: Optional[UUID] = Field(None, description="Associated manga ID")
    client_id: UUID = Field(..., description="Download client ID")
    magnet_link: Optional[str] = Field(None, description="Magnet link")
    torrent_url: Optional[str] = Field(None, description="Torrent file URL")
    indexer: str = Field(..., description="Source indexer")
    info_hash: Optional[str] = Field(None, description="Torrent info hash")
    size: str = Field(..., description="File size")
    seeders: int = Field(0, description="Number of seeders")
    leechers: int = Field(0, description="Number of leechers")
    category: Optional[str] = Field(None, description="Torrent category")


class TorrentDownloadResponse(BaseModel):
    """Schema for torrent download response."""
    
    download_id: UUID = Field(..., description="Download record ID")
    external_id: str = Field(..., description="External download client ID")
    status: str = Field(..., description="Download status")
    message: str = Field(..., description="Status message")


class IndexerHealthResponse(BaseModel):
    """Schema for indexer health check response."""
    
    status: str = Field(..., description="Overall health status")
    healthy_count: int = Field(..., description="Number of healthy indexers")
    total_count: int = Field(..., description="Total number of indexers")
    indexers: Dict[str, Tuple[bool, str]] = Field(
        ..., description="Individual indexer health status"
    )


class TorrentStatsSchema(BaseModel):
    """Schema for torrent statistics."""
    
    total_downloads: int = Field(..., description="Total torrent downloads")
    active_downloads: int = Field(..., description="Currently active downloads")
    completed_downloads: int = Field(..., description="Completed downloads")
    failed_downloads: int = Field(..., description="Failed downloads")
    total_size_downloaded: int = Field(..., description="Total bytes downloaded")
    average_download_speed: float = Field(..., description="Average download speed (bytes/sec)")


class TorrentQualityFilter(BaseModel):
    """Schema for torrent quality filtering preferences."""
    
    min_seeders: int = Field(1, ge=0, description="Minimum number of seeders")
    max_size_gb: Optional[float] = Field(None, ge=0, description="Maximum size in GB")
    min_size_mb: Optional[float] = Field(None, ge=0, description="Minimum size in MB")
    preferred_formats: List[str] = Field(
        default_factory=lambda: ["cbz", "cbr", "zip", "rar"],
        description="Preferred file formats"
    )
    exclude_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to exclude from results"
    )
    include_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that must be present"
    )


class TorrentSearchFilters(BaseModel):
    """Schema for advanced torrent search filters."""
    
    quality: Optional[TorrentQualityFilter] = Field(None, description="Quality filters")
    sort_by: str = Field("seeders", description="Sort field (seeders, size, date)")
    sort_order: str = Field("desc", description="Sort order (asc, desc)")
    include_dead: bool = Field(False, description="Include torrents with 0 seeders")


class EnhancedTorrentSearchRequest(TorrentSearchRequest):
    """Enhanced torrent search request with filters."""
    
    filters: Optional[TorrentSearchFilters] = Field(None, description="Search filters")
    auto_select_best: bool = Field(False, description="Automatically select best torrent")


class TorrentMatchResult(BaseModel):
    """Schema for manga-torrent matching result."""
    
    manga_title: str = Field(..., description="Manga title")
    manga_id: Optional[UUID] = Field(None, description="Manga ID if in library")
    matched_torrents: List[TorrentResultSchema] = Field(
        ..., description="Matched torrent results"
    )
    confidence_score: float = Field(..., ge=0, le=1, description="Match confidence")
    match_reasons: List[str] = Field(..., description="Reasons for the match")


class BulkTorrentDownloadRequest(BaseModel):
    """Schema for bulk torrent download request."""
    
    downloads: List[TorrentDownloadRequest] = Field(
        ..., description="List of torrents to download"
    )
    client_id: UUID = Field(..., description="Download client ID")
    start_paused: bool = Field(False, description="Start downloads in paused state")
    category: Optional[str] = Field(None, description="Category for all downloads")


class BulkTorrentDownloadResponse(BaseModel):
    """Schema for bulk torrent download response."""
    
    total_requested: int = Field(..., description="Total downloads requested")
    successful: int = Field(..., description="Successfully started downloads")
    failed: int = Field(..., description="Failed downloads")
    download_ids: List[UUID] = Field(..., description="Created download record IDs")
    errors: List[str] = Field(..., description="Error messages for failed downloads")


class TorrentClientStats(BaseModel):
    """Schema for torrent client statistics."""
    
    client_name: str = Field(..., description="Download client name")
    total_torrents: int = Field(..., description="Total torrents in client")
    downloading: int = Field(..., description="Currently downloading")
    seeding: int = Field(..., description="Currently seeding")
    paused: int = Field(..., description="Paused torrents")
    completed: int = Field(..., description="Completed torrents")
    total_download_speed: int = Field(..., description="Total download speed (bytes/sec)")
    total_upload_speed: int = Field(..., description="Total upload speed (bytes/sec)")
    free_space: int = Field(..., description="Free disk space (bytes)")


class TorrentHealthCheck(BaseModel):
    """Schema for individual torrent health check."""
    
    info_hash: str = Field(..., description="Torrent info hash")
    title: str = Field(..., description="Torrent title")
    seeders: int = Field(..., description="Current seeders")
    leechers: int = Field(..., description="Current leechers")
    last_checked: datetime = Field(..., description="Last health check time")
    is_healthy: bool = Field(..., description="Whether torrent is healthy")
    health_score: float = Field(..., ge=0, le=1, description="Health score (0-1)")


class TorrentRecommendation(BaseModel):
    """Schema for torrent recommendation."""
    
    torrent: TorrentResultSchema = Field(..., description="Recommended torrent")
    score: float = Field(..., ge=0, le=1, description="Recommendation score")
    reasons: List[str] = Field(..., description="Recommendation reasons")
    manga_match: Optional[str] = Field(None, description="Matched manga title")
    quality_rating: str = Field(..., description="Quality rating (excellent, good, fair, poor)")
