"""
ManhwaToon provider implementation.

ManhwaToon (https://www.manhwatoon.me) is a WordPress/Madara-based manga site.
Unlike most Madara sites in this codebase, its chapter list is not rendered
inline in the manga page HTML - it's loaded via an AJAX POST to
`{manga_url}/ajax/chapters/` using the post ID found in the hidden
`.rating-post-id` input. This subclass adds that extra step; everything else
(search, manga details, pages) uses the standard EnhancedGenericProvider flow.
"""

import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.core.providers.enhanced_generic import EnhancedGenericProvider

logger = logging.getLogger(__name__)


class ManhwaToonProvider(EnhancedGenericProvider):
    """ManhwaToon provider with AJAX-based chapter list support."""

    def _extract_genres(self, soup: BeautifulSoup) -> List[str]:
        # Manga detail pages list genres as a plain comma-separated string next
        # to the "Genre(s)" heading, not as <a> tags (unlike search results).
        genres = super()._extract_genres(soup)
        if genres:
            return genres
        block = soup.select_one(
            ".summary-heading:-soup-contains('Genre') + .summary-content"
        )
        if not block:
            return []
        return [g.strip() for g in block.get_text(strip=True).split(",") if g.strip()]

    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        # Same comma-separated (no <a>) format as genres on the detail page.
        authors = super()._extract_authors(soup)
        if authors:
            return authors
        block = soup.select_one(
            ".summary-heading:-soup-contains('Author') + .summary-content"
        )
        if not block:
            return []
        return [a.strip() for a in block.get_text(strip=True).split(",") if a.strip()]

    async def get_chapters(
        self, manga_id: str, page: int = 1, limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        manga_url = self._manga_url_pattern.format(manga_id=manga_id)
        html = await self._make_request(manga_url)
        if not html:
            return [], 0, False

        soup = BeautifulSoup(html, "html.parser")
        post_id_el = soup.select_one(".rating-post-id")
        post_id = post_id_el.get("value") if post_id_el else None
        if not post_id:
            logger.warning(
                f"No post ID found for {manga_id} on {self.name}, "
                "falling back to inline chapter scraping"
            )
            return await super().get_chapters(manga_id, page, limit)

        ajax_url = f"{manga_url.rstrip('/')}/ajax/chapters/"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    ajax_url,
                    data={"manga_id": post_id},
                    headers=self._headers,
                )
                response.raise_for_status()
                chapter_html = response.text
        except Exception as e:
            logger.error(f"Error fetching AJAX chapter list for {manga_id}: {e}")
            return await super().get_chapters(manga_id, page, limit)

        chapter_soup = BeautifulSoup(chapter_html, "html.parser")
        # Each <li> also holds a second, textless <a> inside
        # `.chapter-release-date` - take only the first (main) link per <li>.
        chapter_elements = [
            a
            for a in (
                li.find("a") for li in chapter_soup.select("li.wp-manga-chapter")
            )
            if a is not None
        ]
        if not chapter_elements:
            logger.warning(f"AJAX chapter list empty for {manga_id} on {self.name}")
            return await super().get_chapters(manga_id, page, limit)

        chapters = []
        for element in chapter_elements:
            chapter_url = element.get("href", "")
            if not chapter_url or chapter_url.startswith("#"):
                continue
            if chapter_url.startswith("/"):
                chapter_url = urljoin(self._base_url, chapter_url)

            chapter_id = chapter_url.rstrip("/").split("/")[-1]
            if not chapter_id:
                continue

            chapter_title = element.get_text(strip=True)
            chapter_number = self._extract_chapter_number(chapter_title, chapter_url)

            chapters.append(
                {
                    "id": chapter_id,
                    "title": chapter_title,
                    "number": chapter_number,
                    "volume": None,
                    "language": "en",
                    "pages_count": 0,
                    "manga_id": manga_id,
                    "publish_at": None,
                    "readable_at": None,
                    "source": self.name,
                    "url": chapter_url,
                }
            )

        total = len(chapters)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_chapters = chapters[start_idx:end_idx]
        has_next = end_idx < total

        return paginated_chapters, total, has_next
