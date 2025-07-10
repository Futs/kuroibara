"""
Naming format engine for manga and chapter organization.

This module provides a flexible template system for naming manga folders and chapter files
following the *arr suite conventions (Sonarr, Radarr, etc.).
"""

import logging
import re
import unicodedata
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from app.models.manga import Chapter, Manga

logger = logging.getLogger(__name__)


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
    DEFAULT_MANGA_FORMAT = "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
    DEFAULT_CHAPTER_FORMAT = "{Chapter Number} - {Chapter Name}"
    
    # Template variable patterns
    VARIABLE_PATTERN = re.compile(r'\{([^}]+)\}')
    
    # Characters to remove or replace for filesystem safety
    UNSAFE_CHARS = r'[<>:"/\\|?*]'
    REPLACEMENT_CHAR = '_'
    
    def __init__(self):
        """Initialize the naming format engine."""
        pass
    
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
        filename = unicodedata.normalize('NFKD', filename)
        
        # Remove or replace unsafe characters
        filename = re.sub(self.UNSAFE_CHARS, self.REPLACEMENT_CHAR, filename)
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Replace multiple consecutive underscores with single underscore
        filename = re.sub(r'_{2,}', '_', filename)
        
        # Ensure filename is not empty
        if not filename:
            return "Unknown"
        
        # Limit length to reasonable filesystem limits
        if len(filename) > 200:
            filename = filename[:200].rstrip('_')
        
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
        self, 
        manga: Manga, 
        chapter: Optional[Chapter] = None
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
        
        # Manga-level variables
        context["Manga Title"] = self.sanitize_filename(manga.title or "Unknown Manga")
        context["Year"] = str(manga.year) if manga.year else "Unknown"
        context["Source"] = self.sanitize_filename(manga.provider or "Unknown")
        
        # Chapter-level variables (if chapter provided)
        if chapter:
            context["Chapter Number"] = self.sanitize_filename(chapter.number or "0")
            context["Chapter Name"] = self.sanitize_filename(chapter.title or "Untitled")
            context["Volume"] = self.sanitize_filename(chapter.volume or "1")
            context["Language"] = chapter.language or "en"
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
            value = context.get(variable_name, f"Unknown_{variable_name.replace(' ', '_')}")

            # Replace the placeholder with the value
            result = result.replace(variable_placeholder, value)

        # Clean up the result by sanitizing each path component separately
        # This preserves path separators while sanitizing individual components
        if '/' in result:
            # Split by path separator, sanitize each component, then rejoin
            components = result.split('/')
            sanitized_components = [self.sanitize_filename(comp) for comp in components]
            result = '/'.join(sanitized_components)
        else:
            # No path separators, sanitize the whole thing
            result = self.sanitize_filename(result)

        return result
    
    def generate_manga_path(
        self, 
        manga: Manga, 
        chapter: Optional[Chapter] = None,
        template: Optional[str] = None
    ) -> str:
        """
        Generate a standardized manga folder path.
        
        Args:
            manga: The manga object
            chapter: The chapter object (optional, for chapter-specific paths)
            template: Custom template (uses default if not provided)
            
        Returns:
            Generated folder path
        """
        if not template:
            template = self.DEFAULT_MANGA_FORMAT
        
        context = self.build_variable_context(manga, chapter)
        return self.apply_template(template, context)
    
    def generate_chapter_filename(
        self, 
        manga: Manga, 
        chapter: Chapter,
        template: Optional[str] = None,
        include_extension: bool = True
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
        
        if include_extension and not filename.endswith('.cbz'):
            filename += '.cbz'
        
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
        open_braces = template.count('{')
        close_braces = template.count('}')
        
        if open_braces != close_braces:
            return False, "Unbalanced braces in template"
        
        # Extract variables and check for known variables
        variables = self.extract_variables(template)
        known_variables = {
            "Manga Title", "Volume", "Chapter Number", "Chapter Name", 
            "Language", "Year", "Source"
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
                "Source": "test"
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


# Global instance
naming_engine = NamingFormatEngine()
