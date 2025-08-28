"""
Torrent indexer services for manga downloads.

This module provides integration with various torrent indexers like Nyaa.si
to search for and download manga torrents with metadata matching.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, quote

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class TorrentResult:
    """Represents a torrent search result."""
    
    title: str
    magnet_link: str
    torrent_url: Optional[str]
    size: str
    seeders: int
    leechers: int
    upload_date: datetime
    category: str
    indexer: str
    info_hash: Optional[str] = None
    description: Optional[str] = None
    uploader: Optional[str] = None
    
    @property
    def size_bytes(self) -> int:
        """Convert size string to bytes."""
        if not self.size:
            return 0
            
        size_str = self.size.upper()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }
        
        for unit, multiplier in multipliers.items():
            if unit in size_str:
                try:
                    number = float(size_str.replace(unit, '').strip())
                    return int(number * multiplier)
                except ValueError:
                    pass
        return 0


class BaseTorrentIndexer(ABC):
    """Base class for torrent indexers."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Indexer name."""
        pass
    
    @abstractmethod
    async def search(self, query: str, category: Optional[str] = None, limit: int = 50) -> List[TorrentResult]:
        """Search for torrents."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Tuple[bool, str]:
        """Test connection to the indexer."""
        pass


class NyaaIndexer(BaseTorrentIndexer):
    """Nyaa.si torrent indexer for anime/manga content."""
    
    def __init__(self, base_url: str = "https://nyaa.si", timeout: int = 30):
        super().__init__(base_url, timeout)
        self.search_url = f"{self.base_url}/"
        
        # Nyaa categories
        self.categories = {
            'anime': '1_0',
            'manga': '3_0',  # Literature category for manga
            'all': '0_0'
        }
    
    @property
    def name(self) -> str:
        return "Nyaa"
    
    async def search(self, query: str, category: Optional[str] = None, limit: int = 50) -> List[TorrentResult]:
        """Search Nyaa for torrents."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            # Prepare search parameters
            params = {
                'q': query,
                'c': self.categories.get(category, self.categories['manga']),
                's': 'seeders',  # Sort by seeders
                'o': 'desc'      # Descending order
            }
            
            logger.info(f"Searching Nyaa for: {query} (category: {category})")
            
            async with self.session.get(self.search_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Nyaa search failed: HTTP {response.status}")
                    return []
                
                html = await response.text()
                return self._parse_search_results(html, limit)
                
        except Exception as e:
            logger.error(f"Error searching Nyaa: {e}")
            return []
    
    def _parse_search_results(self, html: str, limit: int) -> List[TorrentResult]:
        """Parse Nyaa search results from HTML."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find torrent rows
        rows = soup.select('tbody tr')
        
        for row in rows[:limit]:
            try:
                result = self._parse_torrent_row(row)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing Nyaa row: {e}")
                continue
        
        logger.info(f"Found {len(results)} torrents on Nyaa")
        return results
    
    def _parse_torrent_row(self, row) -> Optional[TorrentResult]:
        """Parse a single torrent row."""
        try:
            # Get category
            category_cell = row.select_one('td:first-child')
            category = category_cell.get('title', 'Unknown') if category_cell else 'Unknown'
            
            # Get title and links
            title_cell = row.select_one('td:nth-child(2)')
            if not title_cell:
                return None
            
            title_link = title_cell.select_one('a[href*="/view/"]')
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            
            # Get magnet and torrent links
            magnet_link = None
            torrent_url = None
            
            magnet_elem = title_cell.select_one('a[href^="magnet:"]')
            if magnet_elem:
                magnet_link = magnet_elem.get('href')
            
            torrent_elem = title_cell.select_one('a[href*="/download/"]')
            if torrent_elem:
                torrent_url = urljoin(self.base_url, torrent_elem.get('href'))
            
            if not magnet_link and not torrent_url:
                return None
            
            # Get size
            size_cell = row.select_one('td:nth-child(4)')
            size = size_cell.get_text(strip=True) if size_cell else '0 B'
            
            # Get seeders and leechers
            seeders_cell = row.select_one('td:nth-child(6)')
            leechers_cell = row.select_one('td:nth-child(7)')
            
            seeders = int(seeders_cell.get_text(strip=True)) if seeders_cell else 0
            leechers = int(leechers_cell.get_text(strip=True)) if leechers_cell else 0
            
            # Get upload date
            date_cell = row.select_one('td:nth-child(5)')
            upload_date = self._parse_date(date_cell.get_text(strip=True)) if date_cell else datetime.now()
            
            # Extract info hash from magnet link
            info_hash = None
            if magnet_link:
                hash_match = re.search(r'btih:([a-fA-F0-9]{40})', magnet_link)
                if hash_match:
                    info_hash = hash_match.group(1).upper()
            
            return TorrentResult(
                title=title,
                magnet_link=magnet_link or '',
                torrent_url=torrent_url,
                size=size,
                seeders=seeders,
                leechers=leechers,
                upload_date=upload_date,
                category=category,
                indexer=self.name,
                info_hash=info_hash
            )
            
        except Exception as e:
            logger.warning(f"Error parsing Nyaa torrent row: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse Nyaa date string."""
        try:
            # Nyaa uses format like "2023-12-25 15:30"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback to current time
            return datetime.now()
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test connection to Nyaa."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    return True, f"Connected to Nyaa.si (HTTP {response.status})"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, str(e)


class TorrentIndexerService:
    """Service for managing multiple torrent indexers."""
    
    def __init__(self):
        self.indexers: Dict[str, BaseTorrentIndexer] = {}
        self._register_default_indexers()
    
    def _register_default_indexers(self):
        """Register default torrent indexers."""
        self.indexers['nyaa'] = NyaaIndexer()
    
    def register_indexer(self, name: str, indexer: BaseTorrentIndexer):
        """Register a new indexer."""
        self.indexers[name] = indexer
    
    def get_indexer(self, name: str) -> Optional[BaseTorrentIndexer]:
        """Get indexer by name."""
        return self.indexers.get(name)
    
    def list_indexers(self) -> List[str]:
        """List available indexers."""
        return list(self.indexers.keys())
    
    async def search_all(self, query: str, category: Optional[str] = None, limit: int = 50) -> Dict[str, List[TorrentResult]]:
        """Search all indexers."""
        results = {}
        
        tasks = []
        for name, indexer in self.indexers.items():
            async with indexer:
                task = asyncio.create_task(
                    self._search_indexer(name, indexer, query, category, limit)
                )
                tasks.append(task)
        
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(completed_results):
            indexer_name = list(self.indexers.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Error searching {indexer_name}: {result}")
                results[indexer_name] = []
            else:
                results[indexer_name] = result
        
        return results
    
    async def _search_indexer(self, name: str, indexer: BaseTorrentIndexer, query: str, category: Optional[str], limit: int) -> List[TorrentResult]:
        """Search a single indexer."""
        try:
            return await indexer.search(query, category, limit)
        except Exception as e:
            logger.error(f"Error searching {name}: {e}")
            return []
    
    async def test_all_indexers(self) -> Dict[str, Tuple[bool, str]]:
        """Test connection to all indexers."""
        results = {}
        
        for name, indexer in self.indexers.items():
            async with indexer:
                results[name] = await indexer.test_connection()
        
        return results


# Global service instance
torrent_indexer_service = TorrentIndexerService()
