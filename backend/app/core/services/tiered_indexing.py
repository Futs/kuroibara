"""Tiered indexing system with MangaUpdates, MadaraDex, and MangaDex."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IndexerTier(Enum):
    """Indexer tier levels."""
    PRIMARY = 1    # MangaUpdates - Most comprehensive metadata
    SECONDARY = 2  # MadaraDex - Good coverage, especially for NSFW
    TERTIARY = 3   # MangaDex - Excellent for mainstream manga


@dataclass
class UniversalMetadata:
    """Universal metadata schema that accommodates all indexers."""
    
    # Core identification
    title: str
    alternative_titles: Dict[str, str]  # {"english": "...", "japanese": "...", etc}
    description: Optional[str] = None
    
    # Visual
    cover_image_url: Optional[str] = None
    
    # Classification
    type: Optional[str] = None  # manga, manhwa, manhua, novel
    status: Optional[str] = None  # ongoing, completed, hiatus, cancelled
    year: Optional[int] = None
    completed_year: Optional[int] = None
    
    # Content information
    is_nsfw: bool = False
    content_rating: Optional[str] = None  # safe, suggestive, erotica, pornographic
    demographic: Optional[str] = None  # shounen, seinen, shoujo, josei
    
    # Metadata
    genres: List[str] = None
    tags: List[str] = None  # More specific than genres
    themes: List[str] = None  # Thematic elements
    
    # People
    authors: List[Dict[str, str]] = None  # [{"name": "...", "role": "story"}, ...]
    artists: List[Dict[str, str]] = None  # [{"name": "...", "role": "art"}, ...]
    
    # Statistics
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    popularity_rank: Optional[int] = None
    follows: Optional[int] = None
    
    # Chapter information
    latest_chapter: Optional[str] = None
    total_chapters: Optional[int] = None
    
    # Source information
    source_indexer: str = None  # Which indexer provided this data
    source_id: str = None  # ID in the source indexer
    source_url: Optional[str] = None
    confidence_score: float = 1.0  # How confident we are in this data
    
    # Raw data for debugging/future use
    raw_data: Dict[str, Any] = None


class BaseIndexer(ABC):
    """Base class for all indexers."""
    
    def __init__(self, name: str, tier: IndexerTier, base_url: str):
        self.name = name
        self.tier = tier
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=8),  # 8 seconds per indexer
            headers=self._get_headers()
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "User-Agent": "Kuroibara/1.0 (https://github.com/Futs/kuroibara)"
        }
    
    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[UniversalMetadata]:
        """Search for manga using the indexer."""
        pass
    
    @abstractmethod
    async def get_details(self, source_id: str) -> Optional[UniversalMetadata]:
        """Get detailed information about a specific manga."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test if the indexer is accessible."""
        pass


class MangaUpdatesIndexer(BaseIndexer):
    """MangaUpdates indexer - Primary tier with proper rate limiting and caching."""

    def __init__(self):
        super().__init__(
            name="MangaUpdates",
            tier=IndexerTier.PRIMARY,
            base_url="https://api.mangaupdates.com/v1"
        )
        self.last_update_time = 0
        self.update_interval = 5.0  # 5 seconds between UPDATE operations only
        self.cache = {}  # Simple in-memory cache for efficiency
        self.cache_ttl = 300  # 5 minutes cache TTL

    async def _rate_limit_updates(self):
        """Rate limit UPDATE operations only (5 seconds between updates)."""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_update_time

        if time_since_last < self.update_interval:
            sleep_time = self.update_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_update_time = time.time()

    def _get_cache_key(self, query: str, limit: int) -> str:
        """Generate cache key for request."""
        return f"search:{query}:{limit}"

    def _is_cache_valid(self, cache_entry) -> bool:
        """Check if cache entry is still valid."""
        import time
        return (time.time() - cache_entry['timestamp']) < self.cache_ttl

    async def search(self, query: str, limit: int = 20) -> List[UniversalMetadata]:
        """Search MangaUpdates with caching and rate limiting."""
        if not self.session:
            raise RuntimeError("Indexer must be used as async context manager")

        # Check cache first (as per Acceptable Use Policy)
        cache_key = self._get_cache_key(query, limit)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            return self.cache[cache_key]['data']

        # No rate limiting needed for search operations per MangaUpdates admin
        # Only UPDATE operations are rate limited (5 seconds)

        url = f"{self.base_url}/series/search"
        # Use POST request with JSON body as per OpenAPI spec
        payload = {
            "search": query,
            "page": 1,
            "perpage": min(limit, 100),
            "stype": "title"  # Search by title
        }
        
        try:
            # Use POST request as per OpenAPI specification
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Kuroibara/1.0 (Manga Library Manager; https://github.com/Futs/kuroibara)'
            }

            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []

                    # MangaUpdates API is working correctly

                    for item in data.get("results", []):
                        metadata = self._convert_search_result(item)
                        if metadata:
                            results.append(metadata)

                    # Cache the results (as per Acceptable Use Policy)
                    import time
                    self.cache[cache_key] = {
                        'data': results,
                        'timestamp': time.time()
                    }

                    return results
                elif response.status == 429:
                    logger.warning("MangaUpdates DDOS protection triggered (429). Backing off...")
                    # This indicates DDOS protection, not normal rate limiting
                    return []
                else:
                    error_text = await response.text()
                    logger.error(f"MangaUpdates search failed: {response.status} - {error_text[:200]}")
                    return []
        except Exception as e:
            logger.error(f"Error searching MangaUpdates: {e}")
            return []
    
    async def get_details(self, source_id: str) -> Optional[UniversalMetadata]:
        """Get detailed MangaUpdates information."""
        if not self.session:
            raise RuntimeError("Indexer must be used as async context manager")
        
        url = f"{self.base_url}/series/{source_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._convert_details(data)
                else:
                    logger.error(f"Failed to get MangaUpdates details {source_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting MangaUpdates details: {e}")
            return None
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MangaUpdates connection with proper rate limiting."""
        try:
            # No rate limiting needed for connection tests (read-only operation)

            url = f"{self.base_url}/series/search"
            payload = {
                "search": "test",
                "perpage": 1,
                "stype": "title"
            }
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Kuroibara/1.0 (Manga Library Manager; https://github.com/Futs/kuroibara)'
            }

            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return True, "Connected to MangaUpdates API"
                elif response.status == 429:
                    return False, "DDOS protection triggered (429) - this is normal protection, not rate limiting"
                else:
                    error_text = await response.text()
                    return False, f"HTTP {response.status}: {error_text[:100]}"
        except Exception as e:
            return False, str(e)
    
    def _convert_search_result(self, item: Dict) -> Optional[UniversalMetadata]:
        """Convert MangaUpdates search result to universal metadata."""
        try:
            # Handle case where item might not be a dictionary
            if not isinstance(item, dict):
                logger.warning(f"Expected dict but got {type(item)}: {item}")
                return None

            record = item.get("record", {})
            
            return UniversalMetadata(
                title=record.get("title", ""),
                alternative_titles=self._extract_alt_titles(record),
                description=record.get("description", ""),
                cover_image_url=self._extract_cover_url(record),
                type=record.get("type"),  # It's a string, not nested object
                status=record.get("status"),  # It's a string, not nested object
                year=self._extract_year(record),
                is_nsfw=self._is_nsfw(record),
                genres=self._extract_genres(record),
                authors=self._extract_authors(record),
                rating=record.get("bayesian_rating"),  # Use bayesian_rating instead
                rating_count=record.get("rating_votes", 0),  # Use rating_votes
                source_indexer="mangaupdates",
                source_id=str(record.get("series_id")),
                source_url=record.get("url"),
                confidence_score=1.0,
                raw_data=item
            )
        except Exception as e:
            logger.error(f"Error converting MangaUpdates result: {e}")
            return None
    
    def _convert_details(self, data: Dict) -> Optional[UniversalMetadata]:
        """Convert MangaUpdates details to universal metadata."""
        # Similar to _convert_search_result but with more detailed data
        return self._convert_search_result({"record": data})
    
    def _extract_alt_titles(self, record: Dict) -> Dict[str, str]:
        """Extract alternative titles."""
        titles = {}
        for assoc in record.get("associated", []):
            if assoc.get("title"):
                lang = assoc.get("type", "unknown")
                titles[lang] = assoc["title"]
        return titles
    
    def _extract_cover_url(self, record: Dict) -> Optional[str]:
        """Extract cover image URL."""
        image = record.get("image", {})
        if isinstance(image, dict):
            return image.get("url", {}).get("original")
        return None
    
    def _extract_year(self, record: Dict) -> Optional[int]:
        """Extract publication year."""
        year_data = record.get("year")
        if isinstance(year_data, dict):
            return year_data.get("year")
        elif isinstance(year_data, int):
            return year_data
        return None
    
    def _is_nsfw(self, record: Dict) -> bool:
        """Determine if content is NSFW."""
        genres = [g.get("genre", "").lower() for g in record.get("genres", [])]
        categories = [c.get("category", "").lower() for c in record.get("categories", [])]
        
        nsfw_indicators = ["adult", "mature", "ecchi", "hentai", "smut", "pornographic"]
        
        for indicator in nsfw_indicators:
            if any(indicator in g for g in genres) or any(indicator in c for c in categories):
                return True
        
        return False
    
    def _extract_genres(self, record: Dict) -> List[str]:
        """Extract genres list."""
        genres = []
        for genre_data in record.get("genres", []):
            if genre_data.get("genre"):
                genres.append(genre_data["genre"])
        return genres
    
    def _extract_authors(self, record: Dict) -> List[Dict[str, str]]:
        """Extract authors list."""
        authors = []
        for author_data in record.get("authors", []):
            if author_data.get("name"):
                authors.append({
                    "name": author_data["name"],
                    "role": author_data.get("type", "author")
                })
        return authors


class MadaraDexIndexer(BaseIndexer):
    """MadaraDex indexer - Secondary tier."""
    
    def __init__(self):
        super().__init__(
            name="MadaraDex",
            tier=IndexerTier.SECONDARY,
            base_url="https://madaradex.org"
        )
    
    async def search(self, query: str, limit: int = 20) -> List[UniversalMetadata]:
        """Search MadaraDex using WordPress manga search."""
        if not self.session:
            raise RuntimeError("Indexer must be used as async context manager")

        # MadaraDex uses WordPress manga search with specific post_type
        url = f"{self.base_url}/"
        params = {
            "s": query,
            "post_type": "wp-manga"  # Search specifically for manga posts
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self._parse_search_results(html_content, limit)
                else:
                    logger.error(f"MadaraDex search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching MadaraDex: {e}")
            return []
    
    async def get_details(self, source_id: str) -> Optional[UniversalMetadata]:
        """Get detailed MadaraDex information."""
        if not self.session:
            raise RuntimeError("Indexer must be used as async context manager")
        
        # source_id should be the manga URL path
        url = f"{self.base_url}/{source_id.lstrip('/')}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self._parse_manga_details(html_content, url)
                else:
                    logger.error(f"Failed to get MadaraDex details {source_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting MadaraDex details: {e}")
            return None
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MadaraDex connection."""
        try:
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    return True, "Connected to MadaraDex"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, str(e)
    
    def _parse_search_results(self, html_content: str, limit: int) -> List[UniversalMetadata]:
        """Parse MadaraDex search results from HTML."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'lxml')
            results = []

            # Find manga items in search results
            # MadaraDex uses .c-tabs-item for manga items in search results
            manga_items = soup.find_all('div', class_='c-tabs-item')

            for item in manga_items[:limit]:
                try:
                    metadata = self._parse_manga_item(item)
                    if metadata:
                        results.append(metadata)
                except Exception as e:
                    logger.error(f"Error parsing MadaraDex manga item: {e}")
                    continue

            logger.info(f"Parsed {len(results)} manga from MadaraDex search results")
            return results

        except ImportError:
            logger.error("BeautifulSoup not available for HTML parsing")
            return []
        except Exception as e:
            logger.error(f"Error parsing MadaraDex search results: {e}")
            return []
    
    def _parse_manga_details(self, html_content: str, url: str) -> Optional[UniversalMetadata]:
        """Parse MadaraDex manga details from HTML."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'lxml')

            # Extract basic information
            title = self._extract_title(soup)
            if not title:
                logger.warning("Could not extract title from MadaraDex page")
                return None

            # Extract URL path as source_id
            source_id = url.replace(self.base_url, "").strip("/")

            metadata = UniversalMetadata(
                title=title,
                alternative_titles=self._extract_alternative_titles(soup),
                description=self._extract_description(soup),
                cover_image_url=self._extract_cover_image(soup),
                type=self._extract_type(soup),
                status=self._extract_status(soup),
                year=self._extract_year(soup),
                is_nsfw=self._extract_nsfw_status(soup),
                content_rating=self._extract_content_rating(soup),
                genres=self._extract_genres(soup),
                tags=self._extract_tags(soup),
                authors=self._extract_authors(soup),
                artists=self._extract_artists(soup),
                rating=self._extract_rating(soup),
                latest_chapter=self._extract_latest_chapter(soup),
                source_indexer="madaradex",
                source_id=source_id,
                source_url=url,
                confidence_score=0.8,  # Medium confidence for HTML parsing
                raw_data={"url": url, "title": title}
            )

            return metadata

        except ImportError:
            logger.error("BeautifulSoup not available for HTML parsing")
            return None
        except Exception as e:
            logger.error(f"Error parsing MadaraDex manga details: {e}")
            return None

    def _parse_manga_item(self, item_soup) -> Optional[UniversalMetadata]:
        """Parse individual manga item from search results."""
        try:
            # Extract title and URL - MadaraDex uses h3 for titles
            title_elem = item_soup.find('h3')
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            # Find the main manga link
            title_link = item_soup.find('a', href=lambda x: x and '/title/' in x)
            if not title_link:
                title_link = item_soup.find('a')

            if not title_link:
                return None

            manga_url = title_link.get('href', '')

            if not title or not manga_url:
                return None

            # Make URL absolute
            if manga_url.startswith('/'):
                manga_url = self.base_url + manga_url

            # Extract source_id from URL
            source_id = manga_url.replace(self.base_url, "").strip("/")

            # Extract cover image
            cover_img = item_soup.find('img')
            cover_url = None
            if cover_img:
                cover_url = cover_img.get('src') or cover_img.get('data-src')
                if cover_url and cover_url.startswith('/'):
                    cover_url = self.base_url + cover_url

            # Extract genres from the item
            genres = []

            # First try the .mg_genres element (comma-separated genres)
            mg_genres = item_soup.find(class_='mg_genres')
            if mg_genres:
                genre_text = mg_genres.get_text(strip=True)
                if genre_text and genre_text.startswith('Genres'):
                    # Remove "Genres" prefix and split by comma
                    genre_text = genre_text.replace('Genres', '', 1)
                    genres = [g.strip() for g in genre_text.split(',') if g.strip()]

            # If no genres found, try genre links
            if not genres:
                genre_links = item_soup.find_all('a', href=lambda x: x and '/genre/' in x)
                for genre_link in genre_links:
                    genre_text = genre_link.get_text(strip=True)
                    if genre_text:
                        genres.append(genre_text)

            # Extract latest chapter from meta-item
            latest_chapter = None
            meta_items = item_soup.find_all(class_='meta-item')
            for meta_item in meta_items:
                text = meta_item.get_text(strip=True)
                if 'Latest chapter' in text:
                    # Extract chapter number from "Latest chapterChapter 109"
                    latest_chapter = text.replace('Latest chapter', '').strip()
                    break

            # Extract rating
            rating = None
            rating_elem = item_soup.find(class_='rating') or item_soup.find(class_='score')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except (ValueError, TypeError):
                    pass

            # Check for NSFW indicators
            is_nsfw = self._check_nsfw_indicators(item_soup, title, genres)

            return UniversalMetadata(
                title=title,
                alternative_titles={},
                description=None,  # Not available in search results
                cover_image_url=cover_url,
                type="manhwa",  # MadaraDex is primarily manhwa
                status=None,  # Not available in search results
                year=None,  # Not available in search results
                is_nsfw=is_nsfw,
                genres=genres,
                latest_chapter=latest_chapter,
                rating=rating,
                source_indexer="madaradex",
                source_id=source_id,
                source_url=manga_url,
                confidence_score=0.8,  # Improved confidence with better parsing
                raw_data={"search_item": True, "genres_raw": genres}
            )

        except Exception as e:
            logger.error(f"Error parsing MadaraDex manga item: {e}")
            return None

    def _extract_title(self, soup) -> Optional[str]:
        """Extract manga title from details page."""
        # Try multiple selectors for title
        selectors = [
            'h1.post-title',
            '.post-title h1',
            'h1',
            '.manga-title',
            '.entry-title'
        ]

        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)

        return None

    def _extract_alternative_titles(self, soup) -> Dict[str, str]:
        """Extract alternative titles."""
        alt_titles = {}

        # Look for alternative titles in summary content
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            text = item.get_text(strip=True)
            if 'alternative' in text.lower() or 'other name' in text.lower():
                # Extract titles after the label
                titles_text = text.split(':', 1)
                if len(titles_text) > 1:
                    titles = [t.strip() for t in titles_text[1].split(',')]
                    for i, title in enumerate(titles):
                        if title:
                            alt_titles[f"alt_{i}"] = title

        return alt_titles

    def _extract_description(self, soup) -> Optional[str]:
        """Extract manga description."""
        # Try multiple selectors for description
        selectors = [
            '.summary__content p',
            '.description-summary p',
            '.manga-excerpt p',
            '.summary-content p'
        ]

        for selector in selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                return desc_elem.get_text(strip=True)

        return None

    def _extract_cover_image(self, soup) -> Optional[str]:
        """Extract cover image URL."""
        # Try multiple selectors for cover image
        selectors = [
            '.summary_image img',
            '.manga-cover img',
            '.post-thumbnail img',
            '.item-thumb img'
        ]

        for selector in selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                img_url = img_elem.get('src') or img_elem.get('data-src')
                if img_url:
                    if img_url.startswith('/'):
                        img_url = self.base_url + img_url
                    return img_url

        return None

    def _extract_type(self, soup) -> Optional[str]:
        """Extract manga type (manga, manhwa, manhua)."""
        # Look for type in summary content
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            text = item.get_text(strip=True).lower()
            if 'manhwa' in text:
                return 'manhwa'
            elif 'manhua' in text:
                return 'manhua'
            elif 'manga' in text:
                return 'manga'

        # Default to manhwa for MadaraDex
        return 'manhwa'

    def _extract_status(self, soup) -> Optional[str]:
        """Extract manga status."""
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            text = item.get_text(strip=True).lower()
            if 'ongoing' in text:
                return 'ongoing'
            elif 'completed' in text:
                return 'completed'
            elif 'hiatus' in text:
                return 'hiatus'
            elif 'cancelled' in text:
                return 'cancelled'

        return None

    def _extract_year(self, soup) -> Optional[int]:
        """Extract publication year."""
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            text = item.get_text(strip=True)
            # Look for year patterns
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                return int(year_match.group())

        return None

    def _extract_nsfw_status(self, soup) -> bool:
        """Extract NSFW status."""
        # Check for adult content indicators
        text_content = soup.get_text().lower()
        nsfw_indicators = [
            'mature', 'adult', 'ecchi', 'smut', 'hentai',
            '18+', 'nsfw', 'explicit', 'sexual'
        ]

        for indicator in nsfw_indicators:
            if indicator in text_content:
                return True

        # Check genres for NSFW indicators
        genres = self._extract_genres(soup)
        nsfw_genres = ['mature', 'adult', 'ecchi', 'smut']
        for genre in genres:
            if genre.lower() in nsfw_genres:
                return True

        return False

    def _extract_content_rating(self, soup) -> Optional[str]:
        """Extract content rating."""
        if self._extract_nsfw_status(soup):
            return 'erotica'
        return 'safe'

    def _extract_genres(self, soup) -> List[str]:
        """Extract genres list."""
        genres = []

        # Look for genre links
        genre_links = soup.find_all('a', href=lambda x: x and '/genres/' in x)
        for link in genre_links:
            genre_text = link.get_text(strip=True)
            if genre_text and genre_text not in genres:
                genres.append(genre_text)

        # Also check for genres in summary content
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            parent = item.find_parent()
            if parent and 'genre' in parent.get_text().lower():
                genre_text = item.get_text(strip=True)
                genre_list = [g.strip() for g in genre_text.split(',')]
                for genre in genre_list:
                    if genre and genre not in genres:
                        genres.append(genre)

        return genres

    def _extract_tags(self, soup) -> List[str]:
        """Extract tags (similar to genres but more specific)."""
        # For MadaraDex, tags are often the same as genres
        return self._extract_genres(soup)

    def _extract_authors(self, soup) -> List[Dict[str, str]]:
        """Extract authors list."""
        authors = []

        # Look for author information in summary
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            parent = item.find_parent()
            if parent and 'author' in parent.get_text().lower():
                author_text = item.get_text(strip=True)
                author_names = [a.strip() for a in author_text.split(',')]
                for name in author_names:
                    if name:
                        authors.append({"name": name, "role": "author"})

        return authors

    def _extract_artists(self, soup) -> List[Dict[str, str]]:
        """Extract artists list."""
        artists = []

        # Look for artist information in summary
        summary_items = soup.find_all('div', class_='summary-content')
        for item in summary_items:
            parent = item.find_parent()
            if parent and 'artist' in parent.get_text().lower():
                artist_text = item.get_text(strip=True)
                artist_names = [a.strip() for a in artist_text.split(',')]
                for name in artist_names:
                    if name:
                        artists.append({"name": name, "role": "artist"})

        return artists

    def _extract_rating(self, soup) -> Optional[float]:
        """Extract rating if available."""
        # Look for rating elements
        rating_selectors = [
            '.rating-pmd',
            '.post-rating',
            '.manga-rating',
            '[data-rating]'
        ]

        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_data = rating_elem.get('data-rating')

                if rating_data:
                    try:
                        return float(rating_data)
                    except ValueError:
                        pass

                # Try to extract rating from text
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        return float(rating_match.group(1))
                    except ValueError:
                        pass

        return None

    def _extract_latest_chapter(self, soup) -> Optional[str]:
        """Extract latest chapter information."""
        # Look for latest chapter in various places
        chapter_selectors = [
            '.wp-manga-chapter:first-child a',
            '.chapter-item:first-child a',
            '.latest-chapter a'
        ]

        for selector in chapter_selectors:
            chapter_elem = soup.select_one(selector)
            if chapter_elem:
                chapter_text = chapter_elem.get_text(strip=True)
                # Extract chapter number
                import re
                chapter_match = re.search(r'chapter\s*(\d+(?:\.\d+)?)', chapter_text.lower())
                if chapter_match:
                    return chapter_match.group(1)
                return chapter_text

        return None

    def _check_nsfw_indicators(self, soup, title: str, genres: List[str]) -> bool:
        """Check for NSFW indicators in search results."""
        # Check title
        nsfw_keywords = ['mature', 'adult', 'ecchi', 'smut', '18+']
        title_lower = title.lower()

        for keyword in nsfw_keywords:
            if keyword in title_lower:
                return True

        # Check genres
        nsfw_genres = ['mature', 'adult', 'ecchi', 'smut', 'harem']
        for genre in genres:
            if genre.lower() in nsfw_genres:
                return True

        # Check for 18+ badge or indicator in the item
        nsfw_indicators = soup.find_all(text=lambda x: x and '18+' in x)
        if nsfw_indicators:
            return True

        return False


class MangaDexIndexer(BaseIndexer):
    """MangaDex indexer - Tertiary tier."""

    def __init__(self):
        super().__init__(
            name="MangaDex",
            tier=IndexerTier.TERTIARY,
            base_url="https://api.mangadex.org"
        )
    
    async def search(self, query: str, limit: int = 20) -> List[UniversalMetadata]:
        """Search MangaDex."""
        if not self.session:
            raise RuntimeError("Indexer must be used as async context manager")
        
        url = f"{self.base_url}/manga"
        params = {
            "title": query,
            "limit": min(limit, 100),
            "includes[]": ["cover_art", "author", "artist"],
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get("data", []):
                        metadata = self._convert_search_result(item)
                        if metadata:
                            results.append(metadata)
                    
                    return results
                else:
                    logger.error(f"MangaDex search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching MangaDex: {e}")
            return []
    
    async def get_details(self, source_id: str) -> Optional[UniversalMetadata]:
        """Get detailed MangaDex information."""
        if not self.session:
            raise RuntimeError("Indexer must be used as async context manager")
        
        url = f"{self.base_url}/manga/{source_id}"
        params = {
            "includes[]": ["cover_art", "author", "artist", "tag"]
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._convert_details(data.get("data", {}))
                else:
                    logger.error(f"Failed to get MangaDex details {source_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting MangaDex details: {e}")
            return None
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test MangaDex connection."""
        try:
            url = f"{self.base_url}/manga"
            params = {"title": "test", "limit": 1}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return True, "Connected to MangaDex API"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, str(e)
    
    def _convert_search_result(self, item: Dict) -> Optional[UniversalMetadata]:
        """Convert MangaDex search result to universal metadata."""
        try:
            attributes = item.get("attributes", {})
            
            return UniversalMetadata(
                title=self._get_title(attributes),
                alternative_titles=attributes.get("altTitles", []),
                description=self._get_description(attributes),
                cover_image_url=self._get_cover_url(item),
                type="manga",  # MangaDex is primarily manga
                status=attributes.get("status"),
                year=attributes.get("year"),
                is_nsfw=attributes.get("contentRating") in ["erotica", "pornographic"],
                content_rating=attributes.get("contentRating"),
                demographic=attributes.get("publicationDemographic"),
                tags=self._extract_tags(item),
                authors=self._extract_people(item, "author"),
                artists=self._extract_people(item, "artist"),
                source_indexer="mangadex",
                source_id=item.get("id"),
                source_url=f"https://mangadex.org/title/{item.get('id')}",
                confidence_score=0.9,  # Slightly lower than MangaUpdates
                raw_data=item
            )
        except Exception as e:
            logger.error(f"Error converting MangaDex result: {e}")
            return None
    
    def _convert_details(self, data: Dict) -> Optional[UniversalMetadata]:
        """Convert MangaDex details to universal metadata."""
        return self._convert_search_result(data)
    
    def _get_title(self, attributes: Dict) -> str:
        """Get the best title from MangaDex attributes."""
        title_obj = attributes.get("title", {})
        
        # Prefer English, then romanized, then any available
        for lang in ["en", "ja-ro", "ja"]:
            if lang in title_obj:
                return title_obj[lang]
        
        # Return first available title
        if title_obj:
            return list(title_obj.values())[0]
        
        return "Unknown Title"
    
    def _get_description(self, attributes: Dict) -> Optional[str]:
        """Get description from MangaDex attributes."""
        desc_obj = attributes.get("description", {})
        
        # Prefer English description
        for lang in ["en", "ja"]:
            if lang in desc_obj:
                return desc_obj[lang]
        
        return None
    
    def _get_cover_url(self, item: Dict) -> Optional[str]:
        """Extract cover URL from MangaDex relationships."""
        relationships = item.get("relationships", [])
        
        for rel in relationships:
            if rel.get("type") == "cover_art":
                cover_id = rel.get("id")
                filename = rel.get("attributes", {}).get("fileName")
                if cover_id and filename:
                    return f"https://uploads.mangadex.org/covers/{item.get('id')}/{filename}"
        
        return None
    
    def _extract_tags(self, item: Dict) -> List[str]:
        """Extract tags from MangaDex relationships."""
        tags = []
        relationships = item.get("relationships", [])
        
        for rel in relationships:
            if rel.get("type") == "tag":
                tag_name = rel.get("attributes", {}).get("name", {}).get("en")
                if tag_name:
                    tags.append(tag_name)
        
        return tags
    
    def _extract_people(self, item: Dict, person_type: str) -> List[Dict[str, str]]:
        """Extract authors/artists from MangaDex relationships."""
        people = []
        relationships = item.get("relationships", [])
        
        for rel in relationships:
            if rel.get("type") == person_type:
                name = rel.get("attributes", {}).get("name")
                if name:
                    people.append({
                        "name": name,
                        "role": person_type
                    })
        
        return people


class TieredSearchService:
    """Service that orchestrates searches across multiple indexers."""

    def __init__(self):
        self.indexers = [
            MangaUpdatesIndexer(),  # Primary
            MadaraDexIndexer(),     # Secondary
            MangaDexIndexer(),      # Tertiary
        ]

    async def search(
        self,
        query: str,
        limit: int = 20,
        use_fallback: bool = True,
        min_results: int = 5
    ) -> List[UniversalMetadata]:
        """
        Search across all indexers with intelligent fallback.

        Args:
            query: Search query
            limit: Maximum results to return
            use_fallback: Whether to try secondary/tertiary if primary fails
            min_results: Minimum results before trying next tier
        """
        all_results = []

        for indexer in self.indexers:
            try:
                async with indexer as idx:
                    logger.info(f"Searching {indexer.name} for: {query}")
                    results = await idx.search(query, limit)

                    if results:
                        logger.info(f"Found {len(results)} results from {indexer.name}")
                        all_results.extend(results)

                        # If we have enough results from higher tier, stop
                        if len(all_results) >= min_results and not use_fallback:
                            break

                        # If primary tier gave good results, we might not need others
                        if indexer.tier == IndexerTier.PRIMARY and len(results) >= min_results:
                            if not use_fallback:
                                break
                    else:
                        logger.warning(f"No results from {indexer.name}")

                # Add delay between indexers to be respectful
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error searching {indexer.name}: {e}")
                continue

        # Remove duplicates and sort by confidence/tier
        unique_results = self._deduplicate_results(all_results)
        sorted_results = self._sort_results(unique_results)

        return sorted_results[:limit]

    async def get_details(
        self,
        source_indexer: str,
        source_id: str
    ) -> Optional[UniversalMetadata]:
        """Get detailed information from specific indexer."""
        indexer = self._get_indexer_by_name(source_indexer)
        if not indexer:
            logger.error(f"Unknown indexer: {source_indexer}")
            return None

        try:
            async with indexer as idx:
                return await idx.get_details(source_id)
        except Exception as e:
            logger.error(f"Error getting details from {source_indexer}: {e}")
            return None

    async def test_all_indexers(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Test connectivity to all indexers."""
        results = {}

        for indexer in self.indexers:
            try:
                async with indexer as idx:
                    success, message = await idx.test_connection()
                    results[indexer.name] = (success, message)
            except Exception as e:
                results[indexer.name] = (False, str(e))

        return results

    def _get_indexer_by_name(self, name: str) -> Optional[BaseIndexer]:
        """Get indexer instance by name."""
        for indexer in self.indexers:
            if indexer.name.lower() == name.lower():
                return indexer
        return None

    def _deduplicate_results(self, results: List[UniversalMetadata]) -> List[UniversalMetadata]:
        """Remove duplicate results based on title similarity."""
        if not results:
            return []

        unique_results = []
        seen_titles = set()

        for result in results:
            # Create a normalized title for comparison
            normalized_title = self._normalize_title(result.title)

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_results.append(result)
            else:
                # If we have a duplicate, keep the one with higher confidence
                for i, existing in enumerate(unique_results):
                    if self._normalize_title(existing.title) == normalized_title:
                        if result.confidence_score > existing.confidence_score:
                            unique_results[i] = result
                        break

        return unique_results

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        import re

        # Remove common punctuation and normalize spacing
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _sort_results(self, results: List[UniversalMetadata]) -> List[UniversalMetadata]:
        """Sort results by tier priority and confidence score."""
        tier_priority = {
            "mangaupdates": 1,
            "madaradx": 2,
            "mangadex": 3
        }

        return sorted(
            results,
            key=lambda x: (
                tier_priority.get(x.source_indexer, 999),  # Tier priority
                -x.confidence_score,  # Higher confidence first
                -len(x.description or ""),  # More detailed descriptions first
                x.title.lower()  # Alphabetical as final tiebreaker
            )
        )

    async def cross_reference_manga(
        self,
        primary_result: UniversalMetadata,
        search_other_indexers: bool = True
    ) -> Dict[str, UniversalMetadata]:
        """
        Cross-reference a manga across all indexers to get comprehensive data.

        Args:
            primary_result: The primary result to cross-reference
            search_other_indexers: Whether to search other indexers

        Returns:
            Dict mapping indexer names to their results
        """
        cross_references = {primary_result.source_indexer: primary_result}

        if not search_other_indexers:
            return cross_references

        # Search other indexers for the same manga
        search_terms = [primary_result.title]

        # Add alternative titles as search terms
        if primary_result.alternative_titles:
            if isinstance(primary_result.alternative_titles, dict):
                search_terms.extend(primary_result.alternative_titles.values())
            elif isinstance(primary_result.alternative_titles, list):
                search_terms.extend(primary_result.alternative_titles)

        for indexer in self.indexers:
            if indexer.name.lower() == primary_result.source_indexer.lower():
                continue  # Skip the source indexer

            try:
                async with indexer as idx:
                    # Try each search term
                    for term in search_terms[:3]:  # Limit to avoid rate limiting
                        results = await idx.search(term, limit=5)

                        # Find the best match
                        best_match = self._find_best_match(primary_result, results)
                        if best_match and best_match.confidence_score >= 0.7:
                            cross_references[indexer.name.lower()] = best_match
                            break

                        await asyncio.sleep(0.3)  # Small delay between searches

            except Exception as e:
                logger.error(f"Error cross-referencing with {indexer.name}: {e}")

        return cross_references

    def _find_best_match(
        self,
        target: UniversalMetadata,
        candidates: List[UniversalMetadata]
    ) -> Optional[UniversalMetadata]:
        """Find the best matching candidate for the target manga."""
        if not candidates:
            return None

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            score = self._calculate_similarity_score(target, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match:
            best_match.confidence_score = best_score

        return best_match

    def _calculate_similarity_score(
        self,
        target: UniversalMetadata,
        candidate: UniversalMetadata
    ) -> float:
        """Calculate similarity score between two manga entries."""
        from difflib import SequenceMatcher

        score = 0.0

        # Title similarity (50% weight)
        title_sim = SequenceMatcher(
            None,
            self._normalize_title(target.title),
            self._normalize_title(candidate.title)
        ).ratio()
        score += title_sim * 0.5

        # Alternative title similarity (20% weight)
        if target.alternative_titles and candidate.alternative_titles:
            alt_similarities = []
            for target_alt in target.alternative_titles.values():
                for candidate_alt in candidate.alternative_titles.values():
                    alt_sim = SequenceMatcher(
                        None,
                        self._normalize_title(target_alt),
                        self._normalize_title(candidate_alt)
                    ).ratio()
                    alt_similarities.append(alt_sim)

            if alt_similarities:
                score += max(alt_similarities) * 0.2

        # Year similarity (10% weight)
        if target.year and candidate.year:
            year_diff = abs(target.year - candidate.year)
            if year_diff <= 1:
                score += 0.1
            elif year_diff <= 2:
                score += 0.05

        # Type similarity (10% weight)
        if target.type and candidate.type:
            if target.type.lower() == candidate.type.lower():
                score += 0.1

        # Genre overlap (10% weight)
        if target.genres and candidate.genres:
            target_genres = set(g.lower() for g in target.genres)
            candidate_genres = set(g.lower() for g in candidate.genres)

            if target_genres and candidate_genres:
                overlap = len(target_genres & candidate_genres)
                total = len(target_genres | candidate_genres)
                genre_sim = overlap / total if total > 0 else 0
                score += genre_sim * 0.1

        return min(score, 1.0)


# Global service instance
tiered_search_service = TieredSearchService()
