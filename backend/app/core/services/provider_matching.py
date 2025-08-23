"""
Provider matching service for finding chapters across multiple providers.
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.registry import provider_registry
from app.models.manga import Chapter, Manga

logger = logging.getLogger(__name__)


class ChapterAlternative:
    """Represents an alternative source for a chapter."""

    def __init__(
        self,
        provider_name: str,
        external_manga_id: str,
        external_chapter_id: str,
        confidence: float,
        chapter_title: str = None,
        chapter_number: str = None,
    ):
        self.provider_name = provider_name
        self.external_manga_id = external_manga_id
        self.external_chapter_id = external_chapter_id
        self.confidence = confidence
        self.chapter_title = chapter_title
        self.chapter_number = chapter_number


class ProviderMatchingService:
    """Service to find the same chapter across multiple providers."""

    def __init__(self):
        self.min_confidence = 0.7  # Minimum confidence for a match
        self.title_similarity_weight = 0.6
        self.chapter_number_weight = 0.4

    def normalize_title(self, title: str) -> str:
        """Normalize manga title for comparison."""
        if not title:
            return ""

        # Convert to lowercase
        title = title.lower()

        # Remove common prefixes/suffixes
        title = re.sub(r"\b(manga|manhwa|manhua|comic)\b", "", title)

        # Remove special characters and extra spaces
        title = re.sub(r"[^\w\s]", " ", title)
        title = re.sub(r"\s+", " ", title).strip()

        return title

    def normalize_chapter_number(self, chapter_number: str) -> str:
        """Normalize chapter number for comparison."""
        if not chapter_number:
            return ""

        # Extract numeric part
        match = re.search(r"(\d+(?:\.\d+)?)", str(chapter_number))
        if match:
            return match.group(1)

        return str(chapter_number).lower().strip()

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two manga titles."""
        norm_title1 = self.normalize_title(title1)
        norm_title2 = self.normalize_title(title2)

        if not norm_title1 or not norm_title2:
            return 0.0

        return SequenceMatcher(None, norm_title1, norm_title2).ratio()

    def calculate_chapter_similarity(self, chapter1: str, chapter2: str) -> float:
        """Calculate similarity between two chapter numbers."""
        norm_chapter1 = self.normalize_chapter_number(chapter1)
        norm_chapter2 = self.normalize_chapter_number(chapter2)

        if not norm_chapter1 or not norm_chapter2:
            return 0.0

        # Exact match gets full score
        if norm_chapter1 == norm_chapter2:
            return 1.0

        # Partial match for similar numbers
        return SequenceMatcher(None, norm_chapter1, norm_chapter2).ratio()

    async def find_chapter_alternatives(
        self,
        manga_title: str,
        chapter_number: str,
        original_provider: str,
        exclude_providers: List[str] = None,
        max_alternatives: int = 5,
        timeout_per_provider: int = 10,
        max_providers_to_search: int = 8,
    ) -> List[ChapterAlternative]:
        """
        Find alternative sources for a chapter across multiple providers.

        Args:
            manga_title: Title of the manga
            chapter_number: Chapter number to find
            original_provider: Provider to exclude from search
            exclude_providers: Additional providers to exclude
            max_alternatives: Maximum number of alternatives to return
            timeout_per_provider: Timeout in seconds per provider
            max_providers_to_search: Maximum number of providers to search

        Returns:
            List of chapter alternatives sorted by confidence
        """
        import asyncio

        if exclude_providers is None:
            exclude_providers = []

        exclude_providers.append(original_provider)
        alternatives = []

        # Get priority providers first (most reliable ones)
        priority_providers = [
            "MangaPill",
            "MangaSee",
            "MangaKakalot",
            "MangaBat",
            "MangaLife",
            "ReadM",
        ]

        # Get all available providers
        all_providers = provider_registry.get_all_providers()

        # Sort providers: priority first, then others
        sorted_providers = []
        remaining_providers = []

        for provider in all_providers:
            if provider.name.lower() in [p.lower() for p in exclude_providers]:
                continue

            if provider.name in priority_providers:
                sorted_providers.append(provider)
            else:
                remaining_providers.append(provider)

        # Add remaining providers up to the limit
        sorted_providers.extend(remaining_providers)

        # Limit the number of providers to search
        providers_to_search = sorted_providers[:max_providers_to_search]

        logger.info(
            f"Searching {len(providers_to_search)} providers for alternatives to '{manga_title}' chapter {chapter_number}"
        )

        for i, provider in enumerate(providers_to_search):
            logger.info(
                f"Searching provider {i + 1}/{len(providers_to_search)}: {provider.name}"
            )

            try:
                # Search for manga on this provider with timeout
                search_results, _, _ = await asyncio.wait_for(
                    provider.search(
                        manga_title, page=1, limit=5
                    ),  # Reduced limit for speed
                    timeout=timeout_per_provider,
                )

                for manga_result in search_results:
                    # Handle both dict and SearchResult object formats
                    if hasattr(manga_result, "title"):
                        # SearchResult object
                        manga_title_result = manga_result.title
                        manga_id_result = manga_result.id
                    else:
                        # Dictionary format
                        manga_title_result = manga_result.get("title", "")
                        manga_id_result = manga_result.get("id", "")

                    # Calculate title similarity
                    title_sim = self.calculate_title_similarity(
                        manga_title, manga_title_result
                    )

                    if title_sim < 0.5:  # Skip if title similarity is too low
                        continue

                    try:
                        # Get chapters for this manga with timeout
                        chapters, _, _ = await asyncio.wait_for(
                            provider.get_chapters(manga_id_result),
                            timeout=timeout_per_provider,
                        )

                        for chapter_data in chapters:
                            # Handle both dict and object formats for chapters
                            if hasattr(chapter_data, "number"):
                                chapter_number_result = chapter_data.number
                                chapter_id_result = chapter_data.id
                                chapter_title_result = getattr(
                                    chapter_data, "title", None
                                )
                            else:
                                chapter_number_result = chapter_data.get("number", "")
                                chapter_id_result = chapter_data.get("id", "")
                                chapter_title_result = chapter_data.get("title")

                            # Calculate chapter similarity
                            chapter_sim = self.calculate_chapter_similarity(
                                chapter_number, chapter_number_result
                            )

                            if (
                                chapter_sim < 0.8
                            ):  # Skip if chapter similarity is too low
                                continue

                            # Calculate overall confidence
                            confidence = (
                                title_sim * self.title_similarity_weight
                                + chapter_sim * self.chapter_number_weight
                            )

                            if confidence >= self.min_confidence:
                                alternative = ChapterAlternative(
                                    provider_name=provider.name,
                                    external_manga_id=manga_id_result,
                                    external_chapter_id=chapter_id_result,
                                    confidence=confidence,
                                    chapter_title=chapter_title_result,
                                    chapter_number=chapter_number_result,
                                )
                                alternatives.append(alternative)

                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout getting chapters from {provider.name}")
                        continue
                    except Exception as e:
                        logger.warning(
                            f"Error getting chapters from {provider.name}: {e}"
                        )
                        continue

            except asyncio.TimeoutError:
                logger.warning(f"Timeout searching on {provider.name}")
                continue
            except Exception as e:
                logger.warning(f"Error searching on {provider.name}: {e}")
                continue

            # Early exit if we have enough alternatives
            if len(alternatives) >= max_alternatives:
                logger.info(f"Found {len(alternatives)} alternatives, stopping search")
                break

        # Sort by confidence and return top alternatives
        alternatives.sort(key=lambda x: x.confidence, reverse=True)
        return alternatives[:max_alternatives]

    async def get_fallback_providers_for_manga(
        self, manga: Manga, exclude_providers: List[str] = None
    ) -> List[str]:
        """
        Get recommended fallback providers for a manga based on content type and preferences.

        Args:
            manga: The manga object
            exclude_providers: Providers to exclude

        Returns:
            List of provider names in priority order
        """
        if exclude_providers is None:
            exclude_providers = []

        # Get all providers
        all_providers = provider_registry.get_all_providers()

        # Filter out excluded providers
        available_providers = [
            p
            for p in all_providers
            if p.name.lower() not in [ep.lower() for ep in exclude_providers]
        ]

        # Sort by priority and NSFW support
        fallback_providers = []

        for provider in available_providers:
            # Skip if manga is NSFW but provider doesn't support it
            if manga.is_nsfw and not getattr(provider, "supports_nsfw", False):
                continue

            fallback_providers.append(provider.name)

        # Prioritize based on manga type and provider reliability
        priority_providers = ["MangaPill", "MangaSee", "MangaKakalot", "MangaBat"]

        # Sort: priority providers first, then others
        sorted_providers = []
        for priority_provider in priority_providers:
            if priority_provider in fallback_providers:
                sorted_providers.append(priority_provider)
                fallback_providers.remove(priority_provider)

        # Add remaining providers
        sorted_providers.extend(fallback_providers)

        return sorted_providers[:5]  # Return top 5 fallback providers


# Global instance
provider_matching_service = ProviderMatchingService()
