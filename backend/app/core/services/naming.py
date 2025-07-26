"""
Naming format engine for manga and chapter organization.

This module provides a flexible template system for naming manga folders and chapter files
following the *arr suite conventions (Sonarr, Radarr, etc.).
"""

import logging
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manga import Chapter, Manga

logger = logging.getLogger(__name__)


class VolumeDetectionResult:
    """Result of volume detection analysis for a manga."""

    def __init__(self):
        self.has_volumes = False
        self.volume_count = 0
        self.chapter_count = 0
        self.chapters_with_volumes = 0
        self.chapters_without_volumes = 0
        self.confidence_score = 0.0
        self.recommended_pattern = "volume_based"  # or "chapter_based"
        self.unique_volumes = set()

    def __str__(self):
        return (f"VolumeDetectionResult(has_volumes={self.has_volumes}, "
                f"confidence={self.confidence_score:.2f}, "
                f"pattern={self.recommended_pattern})")


class NamingFormatEngine:
    """
    Engine for processing naming format templates and generating standardized names.

    Supports template variables like:
    - {Manga Title} - Sanitized manga title
    - {Volume} - Volume number with fallback handling
    - {Chapter Number} - Chapter number (supports decimals)
    - {Chapter Name} - Chapter title
    - {Language} - Language code
    - {Year} - Publication year
    - {Source} - Source provider
    """

    # Default templates
    DEFAULT_MANGA_FORMAT = (
        "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
    )
    DEFAULT_CHAPTER_FORMAT = "{Chapter Number} - {Chapter Name}"

    # Alternative templates for different organization patterns
    CHAPTER_BASED_MANGA_FORMAT = "{Manga Title}/ch.{Chapter Number}"
    SIMPLE_MANGA_FORMAT = "{Manga Title}"
    VOLUME_ONLY_FORMAT = "{Manga Title}/Volume {Volume}"

    # Predefined template options for users
    TEMPLATE_PRESETS = {
        "volume_based": "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
        "chapter_based": "{Manga Title}/ch.{Chapter Number}",
        "simple": "{Manga Title}/{Chapter Number} - {Chapter Name}",
        "year_based": "{Manga Title} ({Year})/Volume {Volume}/{Chapter Number} - {Chapter Name}",
        "source_based": "{Source}/{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
    }

    # Template variable patterns
    VARIABLE_PATTERN = re.compile(r"\{([^}]+)\}")

    # Characters to remove or replace for filesystem safety
    UNSAFE_CHARS = r'[<>:"/\\|?*]'
    REPLACEMENT_CHAR = "_"

    def __init__(self):
        """Initialize the naming format engine."""
        pass

    async def analyze_manga_volume_usage(
        self, manga: Manga, db: AsyncSession
    ) -> VolumeDetectionResult:
        """
        Analyze a manga's chapters to determine volume usage patterns.

        Args:
            manga: The manga to analyze
            db: Database session

        Returns:
            VolumeDetectionResult with analysis details
        """
        result = VolumeDetectionResult()

        # Get all chapters for this manga
        chapters_query = select(Chapter).where(Chapter.manga_id == manga.id)
        chapters_result = await db.execute(chapters_query)
        chapters = chapters_result.scalars().all()

        if not chapters:
            return result

        result.chapter_count = len(chapters)

        # Analyze volume information
        for chapter in chapters:
            volume = getattr(chapter, 'volume', None)
            if volume and str(volume).strip() and str(volume) != "1":
                result.chapters_with_volumes += 1
                result.unique_volumes.add(str(volume))
            else:
                result.chapters_without_volumes += 1

        result.volume_count = len(result.unique_volumes)

        # Calculate confidence score and recommendation
        if result.chapter_count == 0:
            result.confidence_score = 0.0
        else:
            volume_ratio = result.chapters_with_volumes / result.chapter_count

            # High confidence for volume-based if:
            # - More than 70% of chapters have explicit volumes
            # - Multiple unique volumes exist
            # - Volume numbers are not just "1"
            if volume_ratio > 0.7 and result.volume_count > 1:
                result.has_volumes = True
                result.confidence_score = min(0.9, 0.5 + volume_ratio * 0.4 + (result.volume_count / 10))
                result.recommended_pattern = "volume_based"
            # Medium confidence for chapter-based if:
            # - Less than 30% have volumes, or all volumes are "1"
            elif volume_ratio < 0.3 or result.volume_count <= 1:
                result.has_volumes = False
                result.confidence_score = min(0.8, 0.5 + (1 - volume_ratio) * 0.3)
                result.recommended_pattern = "chapter_based"
            else:
                # Mixed scenario - use heuristics
                result.has_volumes = volume_ratio >= 0.5
                result.confidence_score = 0.5
                result.recommended_pattern = "volume_based" if result.has_volumes else "chapter_based"

        return result

    def get_recommended_template(self, detection_result: VolumeDetectionResult) -> str:
        """
        Get recommended template based on volume detection results.

        Args:
            detection_result: Result from volume analysis

        Returns:
            Recommended template string
        """
        if detection_result.recommended_pattern == "chapter_based":
            return self.CHAPTER_BASED_MANGA_FORMAT
        else:
            return self.DEFAULT_MANGA_FORMAT

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename for filesystem safety.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename safe for filesystem use
        """
        if not filename:
            return "Unknown"

        # Normalize unicode characters
        filename = unicodedata.normalize("NFKD", filename)

        # Remove or replace unsafe characters
        filename = re.sub(self.UNSAFE_CHARS, self.REPLACEMENT_CHAR, filename)

        # Remove leading/trailing whitespace and dots
        filename = filename.strip(" .")

        # Replace multiple consecutive underscores with single underscore
        filename = re.sub(r"_{2,}", "_", filename)

        # Ensure filename is not empty
        if not filename:
            return "Unknown"

        # Limit length to reasonable filesystem limits
        if len(filename) > 200:
            filename = filename[:200].rstrip("_")

        return filename

    def extract_variables(self, template: str) -> list[str]:
        """
        Extract all variable names from a template.

        Args:
            template: The template string

        Returns:
            List of variable names found in the template
        """
        matches = self.VARIABLE_PATTERN.findall(template)
        return [match.strip() for match in matches]

    def build_variable_context(
        self, manga: Manga, chapter: Optional[Chapter] = None
    ) -> Dict[str, str]:
        """
        Build a context dictionary with all available variables for template substitution.

        Args:
            manga: The manga object
            chapter: The chapter object (optional)

        Returns:
            Dictionary mapping variable names to their values
        """
        context = {}

        # Manga-level variables - use getattr to safely access SQLAlchemy attributes
        manga_title = getattr(manga, 'title', None) or "Unknown Manga"
        manga_year = getattr(manga, 'year', None)
        manga_provider = getattr(manga, 'provider', None) or "Unknown"

        context["Manga Title"] = self.sanitize_filename(str(manga_title))
        context["Year"] = str(manga_year) if manga_year else "Unknown"
        context["Source"] = self.sanitize_filename(str(manga_provider))

        # Chapter-level variables (if chapter provided)
        if chapter:
            chapter_number = getattr(chapter, 'number', None) or "0"
            chapter_title = getattr(chapter, 'title', None) or "Untitled"
            chapter_volume = getattr(chapter, 'volume', None) or "1"
            chapter_language = getattr(chapter, 'language', None) or "en"

            context["Chapter Number"] = self.sanitize_filename(str(chapter_number))
            context["Chapter Name"] = self.sanitize_filename(str(chapter_title))
            context["Volume"] = self.sanitize_filename(str(chapter_volume))
            context["Language"] = str(chapter_language)
        else:
            # Default values when no chapter is provided
            context["Chapter Number"] = "0"
            context["Chapter Name"] = "Untitled"
            context["Volume"] = "1"
            context["Language"] = "en"

        return context

    def apply_template(self, template: str, context: Dict[str, str]) -> str:
        """
        Apply a template with the given context variables.

        Args:
            template: The template string with variables
            context: Dictionary of variable values

        Returns:
            Formatted string with variables substituted
        """
        if not template:
            return ""

        result = template

        # Replace each variable in the template
        for variable_match in self.VARIABLE_PATTERN.finditer(template):
            variable_name = variable_match.group(1).strip()
            variable_placeholder = variable_match.group(0)

            # Get the value from context, with fallback
            value = context.get(
                variable_name, f"Unknown_{variable_name.replace(' ', '_')}"
            )

            # Replace the placeholder with the value
            result = result.replace(variable_placeholder, value)

        # Clean up the result by sanitizing each path component separately
        # This preserves path separators while sanitizing individual components
        if "/" in result:
            # Split by path separator, sanitize each component, then rejoin
            components = result.split("/")
            sanitized_components = [self.sanitize_filename(comp) for comp in components]
            result = "/".join(sanitized_components)
        else:
            # No path separators, sanitize the whole thing
            result = self.sanitize_filename(result)

        return result

    def generate_manga_path(
        self,
        manga: Manga,
        chapter: Optional[Chapter] = None,
        template: Optional[str] = None,
        auto_detect_pattern: bool = False,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Generate a standardized manga folder path.

        Args:
            manga: The manga object
            chapter: The chapter object (optional, for chapter-specific paths)
            template: Custom template (uses default if not provided)
            auto_detect_pattern: Whether to auto-detect the best pattern
            db: Database session (required for auto-detection)

        Returns:
            Generated folder path
        """
        if not template:
            if auto_detect_pattern and db:
                # Use async detection - this would need to be called from an async context
                # For now, fall back to simple heuristics
                template = self._detect_template_from_chapter(chapter)
            else:
                template = self.DEFAULT_MANGA_FORMAT

        context = self.build_variable_context(manga, chapter)
        return self.apply_template(template, context)

    def _detect_template_from_chapter(self, chapter: Optional[Chapter]) -> str:
        """
        Simple heuristic to detect appropriate template from a single chapter.

        Args:
            chapter: Chapter to analyze

        Returns:
            Recommended template
        """
        if not chapter:
            return self.DEFAULT_MANGA_FORMAT

        volume = getattr(chapter, 'volume', None)

        # If no volume or volume is "1" (default), prefer chapter-based
        if not volume or str(volume).strip() in ("", "1"):
            return self.CHAPTER_BASED_MANGA_FORMAT
        else:
            return self.DEFAULT_MANGA_FORMAT

    async def generate_manga_path_smart(
        self,
        manga: Manga,
        chapter: Optional[Chapter] = None,
        template: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """
        Generate manga path with smart template detection.

        Args:
            manga: The manga object
            chapter: The chapter object (optional)
            template: Custom template (overrides auto-detection)
            db: Database session for volume analysis

        Returns:
            Generated folder path with optimal template
        """
        if template:
            # Use provided template
            context = self.build_variable_context(manga, chapter)
            return self.apply_template(template, context)

        if db:
            # Perform full volume analysis
            detection_result = await self.analyze_manga_volume_usage(manga, db)
            recommended_template = self.get_recommended_template(detection_result)
        else:
            # Fall back to simple heuristics
            recommended_template = self._detect_template_from_chapter(chapter)

        context = self.build_variable_context(manga, chapter)
        return self.apply_template(recommended_template, context)

    def generate_chapter_filename(
        self,
        manga: Manga,
        chapter: Chapter,
        template: Optional[str] = None,
        include_extension: bool = True,
    ) -> str:
        """
        Generate a standardized chapter filename.

        Args:
            manga: The manga object
            chapter: The chapter object
            template: Custom template (uses default if not provided)
            include_extension: Whether to include .cbz extension

        Returns:
            Generated filename
        """
        if not template:
            template = self.DEFAULT_CHAPTER_FORMAT

        context = self.build_variable_context(manga, chapter)
        filename = self.apply_template(template, context)

        if include_extension and not filename.endswith(".cbz"):
            filename += ".cbz"

        return filename

    def validate_template(self, template: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a naming template for syntax and safety.

        Args:
            template: The template to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not template:
            return False, "Template cannot be empty"

        # Check for balanced braces
        open_braces = template.count("{")
        close_braces = template.count("}")

        if open_braces != close_braces:
            return False, "Unbalanced braces in template"

        # Extract variables and check for known variables
        variables = self.extract_variables(template)
        known_variables = {
            "Manga Title",
            "Volume",
            "Chapter Number",
            "Chapter Name",
            "Language",
            "Year",
            "Source",
        }

        unknown_variables = set(variables) - known_variables
        if unknown_variables:
            return False, f"Unknown variables: {', '.join(unknown_variables)}"

        # Test template with sample data
        try:
            sample_context = {
                "Manga Title": "Test Manga",
                "Volume": "1",
                "Chapter Number": "1",
                "Chapter Name": "Test Chapter",
                "Language": "en",
                "Year": "2023",
                "Source": "test",
            }
            result = self.apply_template(template, sample_context)

            # Check if result is reasonable
            if len(result) > 250:
                return False, "Template produces names that are too long"

            if not result or result.isspace():
                return False, "Template produces empty names"

        except Exception as e:
            return False, f"Template processing error: {str(e)}"

        return True, None

    def get_template_presets(self) -> Dict[str, str]:
        """
        Get available template presets.

        Returns:
            Dictionary of preset names to template strings
        """
        return self.TEMPLATE_PRESETS.copy()

    def get_preset_description(self, preset_name: str) -> str:
        """
        Get human-readable description for a template preset.

        Args:
            preset_name: Name of the preset

        Returns:
            Description of what the preset does
        """
        descriptions = {
            "volume_based": "Organizes by volumes: Manga Title/Volume X/Chapter Y - Name",
            "chapter_based": "Simple chapter organization: Manga Title/ch.X",
            "simple": "Flat structure: Manga Title/Chapter Y - Name",
            "year_based": "Includes publication year: Manga Title (Year)/Volume X/Chapter Y - Name",
            "source_based": "Groups by source: Source/Manga Title/Volume X/Chapter Y - Name",
        }
        return descriptions.get(preset_name, "Custom template")


# Global instance
naming_engine = NamingFormatEngine()
