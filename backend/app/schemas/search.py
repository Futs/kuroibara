from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.manga import MangaStatus, MangaType


class ProviderInfo(BaseModel):
    """Provider information schema with health status."""

    id: str
    name: str
    url: str
    supports_nsfw: bool
    status: str = "unknown"
    is_enabled: bool = True
    last_check: Optional[datetime] = None
    response_time: Optional[int] = None
    uptime_percentage: int = 100
    consecutive_failures: int = 0
    is_healthy: bool = True


class SearchQuery(BaseModel):
    """Search query schema."""

    query: str
    provider: Optional[str] = None
    page: int = 1
    limit: int = 20


class SearchFilter(BaseModel):
    """Search filter schema."""

    title: Optional[str] = None
    type: Optional[MangaType] = None
    status: Optional[MangaStatus] = None
    genres: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    include_nsfw: bool = False


class SearchResult(BaseModel):
    """Search result schema."""

    id: str
    title: str
    alternative_titles: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    type: MangaType = MangaType.UNKNOWN
    status: MangaStatus = MangaStatus.UNKNOWN
    year: Optional[int] = None
    is_nsfw: bool = False
    genres: List[str] = []
    authors: List[str] = []
    provider: str
    url: str
    in_library: bool = False
    source_indexer: Optional[str] = None  # Source indexer (e.g., "mangaupdates")
    source_id: Optional[str] = None  # Source-specific ID
    extra: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response schema."""

    results: List[SearchResult]
    total: int
    page: int
    limit: int
    has_next: bool
