"""
Tests for the manga organizer functionality.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.core.services.naming import NamingFormatEngine
from app.core.services.organizer import MangaOrganizer
from app.core.services.cbz_converter import CBZConverter
from app.models.manga import Manga, Chapter, MangaType, MangaStatus
from app.models.user import User


class TestNamingFormatEngine:
    """Test the naming format engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = NamingFormatEngine()
        
        # Create mock manga and chapter
        self.manga = Mock(spec=Manga)
        self.manga.id = uuid4()
        self.manga.title = "Test Manga"
        self.manga.year = 2023
        self.manga.provider = "test_provider"
        
        self.chapter = Mock(spec=Chapter)
        self.chapter.id = uuid4()
        self.chapter.number = "1"
        self.chapter.title = "Test Chapter"
        self.chapter.volume = "1"
        self.chapter.language = "en"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test basic sanitization
        assert self.engine.sanitize_filename("normal_name") == "normal_name"
        
        # Test unsafe characters (consecutive underscores are collapsed to single underscore)
        assert self.engine.sanitize_filename("name<>:\"/\\|?*") == "name_"
        
        # Test unicode normalization
        assert self.engine.sanitize_filename("café") == "café"
        
        # Test empty string
        assert self.engine.sanitize_filename("") == "Unknown"
        assert self.engine.sanitize_filename("   ") == "Unknown"
        
        # Test length limit
        long_name = "a" * 250
        result = self.engine.sanitize_filename(long_name)
        assert len(result) <= 200
    
    def test_extract_variables(self):
        """Test variable extraction from templates."""
        template = "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
        variables = self.engine.extract_variables(template)
        
        expected = ["Manga Title", "Volume", "Chapter Number", "Chapter Name"]
        assert variables == expected
    
    def test_build_variable_context(self):
        """Test building variable context."""
        context = self.engine.build_variable_context(self.manga, self.chapter)
        
        assert context["Manga Title"] == "Test Manga"
        assert context["Chapter Number"] == "1"
        assert context["Chapter Name"] == "Test Chapter"
        assert context["Volume"] == "1"
        assert context["Language"] == "en"
        assert context["Year"] == "2023"
        assert context["Source"] == "test_provider"
    
    def test_apply_template(self):
        """Test template application."""
        template = "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
        context = self.engine.build_variable_context(self.manga, self.chapter)
        
        result = self.engine.apply_template(template, context)
        expected = "Test Manga/Volume 1/1 - Test Chapter"
        assert result == expected
    
    def test_generate_manga_path(self):
        """Test manga path generation."""
        template = "{Manga Title}/Volume {Volume}"
        result = self.engine.generate_manga_path(self.manga, self.chapter, template)
        
        assert result == "Test Manga/Volume 1"
    
    def test_generate_chapter_filename(self):
        """Test chapter filename generation."""
        template = "{Chapter Number} - {Chapter Name}"
        result = self.engine.generate_chapter_filename(
            self.manga, self.chapter, template, include_extension=True
        )
        
        assert result == "1 - Test Chapter.cbz"
        
        # Test without extension
        result = self.engine.generate_chapter_filename(
            self.manga, self.chapter, template, include_extension=False
        )
        
        assert result == "1 - Test Chapter"
    
    def test_validate_template(self):
        """Test template validation."""
        # Valid template
        valid_template = "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
        is_valid, error = self.engine.validate_template(valid_template)
        assert is_valid is True
        assert error is None
        
        # Empty template
        is_valid, error = self.engine.validate_template("")
        assert is_valid is False
        assert "empty" in error.lower()
        
        # Unbalanced braces
        is_valid, error = self.engine.validate_template("{Manga Title")
        assert is_valid is False
        assert "braces" in error.lower()
        
        # Unknown variable
        is_valid, error = self.engine.validate_template("{Unknown Variable}")
        assert is_valid is False
        assert "unknown" in error.lower()


class TestMangaOrganizer:
    """Test the manga organizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.organizer = MangaOrganizer()
        
        # Create mock user
        self.user = Mock(spec=User)
        self.user.id = uuid4()
        self.user.naming_format_manga = "{Manga Title}/Volume {Volume}"
        self.user.naming_format_chapter = "{Chapter Number} - {Chapter Name}"
        self.user.create_cbz_files = True
        self.user.preserve_original_files = False
        
        # Create mock manga and chapter
        self.manga = Mock(spec=Manga)
        self.manga.id = uuid4()
        self.manga.title = "Test Manga"
        
        self.chapter = Mock(spec=Chapter)
        self.chapter.id = uuid4()
        self.chapter.number = "1"
        self.chapter.title = "Test Chapter"
        self.chapter.volume = "1"
        self.chapter.file_path = None
    
    def test_get_organized_base_path(self):
        """Test getting organized base path."""
        path = self.organizer.get_organized_base_path(self.manga.id)
        assert "organized" in path
        assert str(self.manga.id) in path
    
    def test_get_raw_base_path(self):
        """Test getting raw base path."""
        path = self.organizer.get_raw_base_path(self.manga.id)
        assert "raw" in path
        assert str(self.manga.id) in path
    
    def test_ensure_directory_exists(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test", "nested", "directory")
            
            # Directory doesn't exist initially
            assert not os.path.exists(test_dir)
            
            # Create directory
            result = self.organizer.ensure_directory_exists(test_dir)
            assert result is True
            assert os.path.exists(test_dir)
            
            # Directory already exists
            result = self.organizer.ensure_directory_exists(test_dir)
            assert result is True
    
    def test_safe_move_file(self):
        """Test safe file moving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source file
            source_file = os.path.join(temp_dir, "source.txt")
            with open(source_file, "w") as f:
                f.write("test content")
            
            # Move to new location
            dest_file = os.path.join(temp_dir, "dest", "moved.txt")
            result = self.organizer.safe_move_file(source_file, dest_file)
            
            assert result is True
            assert not os.path.exists(source_file)
            assert os.path.exists(dest_file)
            
            with open(dest_file, "r") as f:
                assert f.read() == "test content"
    
    def test_safe_copy_file(self):
        """Test safe file copying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create source file
            source_file = os.path.join(temp_dir, "source.txt")
            with open(source_file, "w") as f:
                f.write("test content")
            
            # Copy to new location
            dest_file = os.path.join(temp_dir, "dest", "copied.txt")
            result = self.organizer.safe_copy_file(source_file, dest_file)
            
            assert result is True
            assert os.path.exists(source_file)  # Original still exists
            assert os.path.exists(dest_file)
            
            with open(dest_file, "r") as f:
                assert f.read() == "test content"


class TestCBZConverter:
    """Test the CBZ converter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = CBZConverter()
        
        # Create mock manga and chapter
        self.manga = Mock(spec=Manga)
        self.manga.id = uuid4()
        self.manga.title = "Test Manga"
        self.manga.year = 2023
        self.manga.status = MangaStatus.ONGOING
        self.manga.type = MangaType.MANGA
        self.manga.provider = "test"
        self.manga.external_id = "test123"
        
        self.chapter = Mock(spec=Chapter)
        self.chapter.id = uuid4()
        self.chapter.title = "Test Chapter"
        self.chapter.number = "1"
        self.chapter.volume = "1"
        self.chapter.language = "en"
        self.chapter.source = "test"
    
    def test_get_image_files_from_directory(self):
        """Test getting image files from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            image_files = ["001.jpg", "002.png", "003.gif"]
            other_files = ["readme.txt", "metadata.json"]
            
            for filename in image_files + other_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "wb") as f:
                    # Write minimal file content
                    if filename.endswith(('.jpg', '.png', '.gif')):
                        # Write minimal image-like content
                        f.write(b'\x89PNG\r\n\x1a\n' if filename.endswith('.png') else b'\xff\xd8\xff')
                    else:
                        f.write(b"test content")
            
            # Mock is_image_file to return True for image extensions
            with patch('app.core.services.cbz_converter.is_image_file') as mock_is_image:
                mock_is_image.side_effect = lambda path: any(path.endswith(ext) for ext in ['.jpg', '.png', '.gif'])
                
                result = self.converter.get_image_files_from_directory(temp_dir)
                
                # Should return only image files, sorted
                assert len(result) == 3
                assert all(any(img in path for img in image_files) for path in result)
    
    def test_create_cbz_metadata(self):
        """Test CBZ metadata creation."""
        # Create mock image files
        image_files = ["/path/to/001.jpg", "/path/to/002.png"]
        
        with patch('app.core.services.cbz_converter.get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)
            
            metadata = self.converter.create_cbz_metadata(self.manga, self.chapter, image_files)
            
            assert metadata["manga"]["title"] == "Test Manga"
            assert metadata["chapter"]["title"] == "Test Chapter"
            assert metadata["chapter"]["pages_count"] == 2
            assert len(metadata["pages"]) == 2
            assert metadata["pages"][0]["number"] == 1
            assert metadata["pages"][0]["width"] == 800
            assert metadata["pages"][0]["height"] == 600


@pytest.mark.asyncio
class TestOrganizerIntegration:
    """Integration tests for the organizer system."""
    
    async def test_organize_chapter_workflow(self):
        """Test the complete chapter organization workflow."""
        # This would be a more complex integration test
        # that tests the full workflow with a real database
        # and file system operations
        pass
    
    async def test_batch_organization_workflow(self):
        """Test batch organization workflow."""
        # This would test the batch organizer with multiple
        # manga and chapters
        pass


if __name__ == "__main__":
    pytest.main([__file__])
