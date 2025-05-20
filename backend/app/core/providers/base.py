from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.models.manga import MangaType, MangaStatus
from app.schemas.search import SearchResult, SearchFilter


class BaseProvider(ABC):
    """Base class for manga providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the provider."""
        pass
    
    @property
    @abstractmethod
    def url(self) -> str:
        """Get the URL of the provider."""
        pass
    
    @property
    @abstractmethod
    def supports_nsfw(self) -> bool:
        """Check if the provider supports NSFW content."""
        pass
    
    @abstractmethod
    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> tuple[List[SearchResult], int, bool]:
        """
        Search for manga.
        
        Args:
            query: The search query
            page: The page number
            limit: The number of results per page
            
        Returns:
            A tuple containing:
            - List of search results
            - Total number of results
            - Whether there are more results
        """
        pass
    
    @abstractmethod
    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """
        Get details for a manga.
        
        Args:
            manga_id: The ID of the manga
            
        Returns:
            A dictionary containing manga details
        """
        pass
    
    @abstractmethod
    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """
        Get chapters for a manga.
        
        Args:
            manga_id: The ID of the manga
            page: The page number
            limit: The number of results per page
            
        Returns:
            A tuple containing:
            - List of chapters
            - Total number of chapters
            - Whether there are more chapters
        """
        pass
    
    @abstractmethod
    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """
        Get pages for a chapter.
        
        Args:
            manga_id: The ID of the manga
            chapter_id: The ID of the chapter
            
        Returns:
            A list of page URLs
        """
        pass
    
    @abstractmethod
    async def download_page(self, page_url: str) -> bytes:
        """
        Download a page.
        
        Args:
            page_url: The URL of the page
            
        Returns:
            The page content as bytes
        """
        pass
    
    @abstractmethod
    async def download_cover(self, manga_id: str) -> bytes:
        """
        Download a manga cover.
        
        Args:
            manga_id: The ID of the manga
            
        Returns:
            The cover content as bytes
        """
        pass
