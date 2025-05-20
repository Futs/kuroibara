from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.models.manga import MangaType, MangaStatus


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
    extra: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Search response schema."""
    
    results: List[SearchResult]
    total: int
    page: int
    limit: int
    has_next: bool
