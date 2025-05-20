from typing import List, Dict, Any, Optional, Tuple
import httpx
import re
import json
from urllib.parse import urlencode

from app.core.providers.base import BaseProvider
from app.models.manga import MangaType, MangaStatus
from app.schemas.search import SearchResult


class MangaSeeProvider(BaseProvider):
    """MangaSee provider."""
    
    @property
    def name(self) -> str:
        return "MangaSee"
    
    @property
    def url(self) -> str:
        return "https://mangasee123.com"
    
    @property
    def supports_nsfw(self) -> bool:
        return True
    
    async def _get_all_manga(self) -> List[Dict[str, Any]]:
        """Get all manga from MangaSee."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/search/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            
            # Check if request was successful
            response.raise_for_status()
            html = response.text
            
            # Extract manga list from JavaScript
            match = re.search(r'vm.Directory = (.*?);', html)
            if match:
                manga_list = json.loads(match.group(1))
                return manga_list
            
            return []
    
    async def search(
        self, query: str, page: int = 1, limit: int = 20
    ) -> Tuple[List[SearchResult], int, bool]:
        """Search for manga on MangaSee."""
        # Get all manga
        manga_list = await self._get_all_manga()
        
        # Filter manga by query
        filtered_manga = []
        for manga in manga_list:
            if query.lower() in manga.get("s", "").lower():
                filtered_manga.append(manga)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Apply pagination
        total = len(filtered_manga)
        paginated_manga = filtered_manga[offset:offset + limit]
        has_next = (offset + limit) < total
        
        # Parse results
        results = []
        for manga in paginated_manga:
            # Get manga ID (slug)
            manga_id = manga.get("i", "")
            
            # Get title
            title = manga.get("s", "")
            
            # Get alternative titles
            alternative_titles = {}
            if "al" in manga and manga["al"]:
                alternative_titles["alternative"] = manga["al"]
            
            # Determine manga type
            manga_type = MangaType.MANGA
            if "t" in manga:
                manga_type_str = manga["t"].lower()
                if "manhwa" in manga_type_str:
                    manga_type = MangaType.MANHWA
                elif "manhua" in manga_type_str:
                    manga_type = MangaType.MANHUA
            
            # Determine manga status
            manga_status = MangaStatus.UNKNOWN
            if "ss" in manga:
                status_str = manga["ss"].lower()
                if "ongoing" in status_str:
                    manga_status = MangaStatus.ONGOING
                elif "complete" in status_str:
                    manga_status = MangaStatus.COMPLETED
                elif "hiatus" in status_str:
                    manga_status = MangaStatus.HIATUS
                elif "cancelled" in status_str or "dropped" in status_str:
                    manga_status = MangaStatus.CANCELLED
            
            # Get genres
            genres = manga.get("g", [])
            
            # Determine if manga is NSFW
            is_nsfw = "Adult" in genres or "Mature" in genres or "Smut" in genres
            
            # Get cover URL
            cover_url = f"https://temp.compsci88.com/cover/{manga_id}.jpg"
            
            # Create search result
            result = SearchResult(
                id=manga_id,
                title=title,
                alternative_titles=alternative_titles,
                description="",  # We need to fetch the manga details to get the description
                cover_image=cover_url,
                type=manga_type,
                status=manga_status,
                year=None,
                is_nsfw=is_nsfw,
                genres=genres,
                authors=[],  # We need to fetch the manga details to get the authors
                provider=self.name,
                url=f"{self.url}/manga/{manga_id}",
            )
            
            results.append(result)
        
        return results, total, has_next
    
    async def get_manga_details(self, manga_id: str) -> Dict[str, Any]:
        """Get details for a manga on MangaSee."""
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/manga/{manga_id}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            
            # Check if request was successful
            response.raise_for_status()
            html = response.text
            
            # Extract manga details from JavaScript
            match = re.search(r'vm.SeriesJSON = (.*?);', html)
            if not match:
                return {}
            
            manga_details_json = json.loads(match.group(1))
            
            # Get title
            title = manga_details_json.get("SeriesName", "")
            
            # Get alternative titles
            alternative_titles = {}
            if "AlternativeNames" in manga_details_json and manga_details_json["AlternativeNames"]:
                alternative_titles["alternative"] = manga_details_json["AlternativeNames"]
            
            # Get description
            description = manga_details_json.get("Description", "")
            
            # Get authors
            authors = []
            if "Author" in manga_details_json and manga_details_json["Author"]:
                authors = manga_details_json["Author"].split(",")
            
            # Get genres
            genres = manga_details_json.get("Genres", [])
            
            # Determine manga type
            manga_type = MangaType.MANGA
            if "Type" in manga_details_json:
                manga_type_str = manga_details_json["Type"].lower()
                if "manhwa" in manga_type_str:
                    manga_type = MangaType.MANHWA
                elif "manhua" in manga_type_str:
                    manga_type = MangaType.MANHUA
            
            # Determine manga status
            manga_status = MangaStatus.UNKNOWN
            if "Status" in manga_details_json:
                status_str = manga_details_json["Status"].lower()
                if "ongoing" in status_str:
                    manga_status = MangaStatus.ONGOING
                elif "complete" in status_str:
                    manga_status = MangaStatus.COMPLETED
                elif "hiatus" in status_str:
                    manga_status = MangaStatus.HIATUS
                elif "cancelled" in status_str or "dropped" in status_str:
                    manga_status = MangaStatus.CANCELLED
            
            # Get year
            year = None
            if "YearOfRelease" in manga_details_json:
                try:
                    year = int(manga_details_json["YearOfRelease"])
                except (ValueError, TypeError):
                    pass
            
            # Determine if manga is NSFW
            is_nsfw = "Adult" in genres or "Mature" in genres or "Smut" in genres
            
            # Get cover URL
            cover_url = f"https://temp.compsci88.com/cover/{manga_id}.jpg"
            
            # Return manga details
            return {
                "id": manga_id,
                "title": title,
                "alternative_titles": alternative_titles,
                "description": description,
                "cover_image": cover_url,
                "type": manga_type,
                "status": manga_status,
                "year": year,
                "is_nsfw": is_nsfw,
                "genres": genres,
                "authors": authors,
                "provider": self.name,
                "url": f"{self.url}/manga/{manga_id}",
            }
    
    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Get chapters for a manga on MangaSee."""
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/manga/{manga_id}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            
            # Check if request was successful
            response.raise_for_status()
            html = response.text
            
            # Extract chapters from JavaScript
            match = re.search(r'vm.Chapters = (.*?);', html)
            if not match:
                return [], 0, False
            
            chapters_json = json.loads(match.group(1))
            
            # Parse chapters
            chapters = []
            for chapter in chapters_json:
                # Get chapter ID
                chapter_id = chapter.get("Chapter", "")
                
                # Get chapter number
                chapter_number = ""
                if chapter_id:
                    # MangaSee uses a specific format for chapter numbers
                    # The first digit is the season, the next 4 digits are the chapter number
                    # For example, "10100" means season 1, chapter 100
                    # "0" means chapter 0, "100" means chapter 100, etc.
                    if len(chapter_id) >= 1:
                        chapter_number = str(int(chapter_id[-3:]))
                        if chapter_id[-3:] == "000":
                            chapter_number = str(int(chapter_id[1:-3]))
                
                # Get chapter title
                chapter_title = chapter.get("ChapterName", "")
                
                # Get chapter date
                chapter_date = chapter.get("Date", "")
                
                # Create chapter
                chapters.append({
                    "id": chapter_id,
                    "title": chapter_title,
                    "number": chapter_number,
                    "volume": None,
                    "language": "en",
                    "pages_count": 0,  # We don't know the page count yet
                    "manga_id": manga_id,
                    "date": chapter_date,
                })
            
            # Sort chapters by number (descending)
            chapters.sort(key=lambda x: float(x["number"]) if x["number"] else 0, reverse=True)
            
            # Calculate offset
            offset = (page - 1) * limit
            
            # Apply pagination
            total = len(chapters)
            paginated_chapters = chapters[offset:offset + limit]
            has_next = (offset + limit) < total
            
            return paginated_chapters, total, has_next
    
    async def get_pages(self, manga_id: str, chapter_id: str) -> List[str]:
        """Get pages for a chapter on MangaSee."""
        # Make request
        async with httpx.AsyncClient() as client:
            # Convert chapter ID to URL format
            # The first digit is the season, the next 4 digits are the chapter number
            # For example, "10100" means season 1, chapter 100
            # URL format: /read-online/{manga_id}-chapter-{chapter_number}-index-{page}
            season = chapter_id[0]
            chapter_number = str(int(chapter_id[1:-3]))
            chapter_decimal = chapter_id[-3:]
            
            if chapter_decimal != "000":
                chapter_number += "." + str(int(chapter_decimal))
            
            response = await client.get(
                f"{self.url}/read-online/{manga_id}-chapter-{chapter_number}-page-1.html",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            
            # Check if request was successful
            response.raise_for_status()
            html = response.text
            
            # Extract chapter data from JavaScript
            match = re.search(r'vm.CurChapter = (.*?);', html)
            if not match:
                return []
            
            chapter_data = json.loads(match.group(1))
            
            # Get directory and path
            match = re.search(r'vm.CurPathName = "(.*?)";', html)
            if not match:
                return []
            
            path_name = match.group(1)
            
            # Get number of pages
            pages_count = int(chapter_data.get("Page", "0"))
            
            # Generate page URLs
            page_urls = []
            for page in range(1, pages_count + 1):
                # MangaSee uses a specific format for page URLs
                # https://official-ongoing-1.ivalice.us/manga/{manga_id}/{chapter_directory}/{page}.png
                page_str = f"{page:03d}"
                page_url = f"https://{path_name}/manga/{manga_id}/{chapter_data['Directory']}/{page_str}.png"
                page_urls.append(page_url)
            
            return page_urls
    
    async def download_page(self, page_url: str) -> bytes:
        """Download a page from MangaSee."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                page_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": self.url
                }
            )
            response.raise_for_status()
            return response.content
    
    async def download_cover(self, manga_id: str) -> bytes:
        """Download a manga cover from MangaSee."""
        # Get cover URL
        cover_url = f"https://temp.compsci88.com/cover/{manga_id}.jpg"
        
        # Download cover
        async with httpx.AsyncClient() as client:
            response = await client.get(
                cover_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": self.url
                }
            )
            response.raise_for_status()
            return response.content
