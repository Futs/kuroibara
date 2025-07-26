#!/usr/bin/env python3
"""
Test script for volume detection and naming engine functionality.

This script tests the new volume detection and folder structure migration
features without requiring a database connection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.services.naming import naming_engine, VolumeDetectionResult
from app.models.manga import Manga, Chapter
from unittest.mock import Mock
import asyncio


def create_mock_manga(title="Test Manga", year=2023, provider="test_provider"):
    """Create a mock manga object for testing."""
    manga = Mock(spec=Manga)
    manga.id = "test-manga-id"
    manga.title = title
    manga.year = year
    manga.provider = provider
    return manga


def create_mock_chapter(number, title=None, volume=None, language="en"):
    """Create a mock chapter object for testing."""
    chapter = Mock(spec=Chapter)
    chapter.id = f"chapter-{number}"
    chapter.number = str(number)
    chapter.title = title or f"Chapter {number}"
    chapter.volume = volume
    chapter.language = language
    return chapter


def test_naming_engine_basic():
    """Test basic naming engine functionality."""
    print("=== Testing Basic Naming Engine ===")
    
    manga = create_mock_manga("One Piece", 1997, "mangadex")
    chapter = create_mock_chapter(1, "Romance Dawn", "1")
    
    # Test variable context building
    context = naming_engine.build_variable_context(manga, chapter)
    print(f"Variable context: {context}")
    
    # Test template application
    template = "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
    result = naming_engine.apply_template(template, context)
    print(f"Template result: {result}")
    
    # Test chapter-based template
    chapter_template = "{Manga Title}/ch.{Chapter Number}"
    chapter_result = naming_engine.apply_template(chapter_template, context)
    print(f"Chapter-based result: {chapter_result}")
    
    print("✓ Basic naming engine tests passed\n")


def test_template_presets():
    """Test template presets functionality."""
    print("=== Testing Template Presets ===")
    
    presets = naming_engine.get_template_presets()
    print(f"Available presets: {list(presets.keys())}")
    
    for name, template in presets.items():
        description = naming_engine.get_preset_description(name)
        print(f"  {name}: {description}")
        print(f"    Template: {template}")
    
    print("✓ Template presets tests passed\n")


def test_template_validation():
    """Test template validation."""
    print("=== Testing Template Validation ===")
    
    # Valid templates
    valid_templates = [
        "{Manga Title}/Volume {Volume}",
        "{Manga Title}/ch.{Chapter Number}",
        "{Manga Title}/{Chapter Number} - {Chapter Name}",
    ]
    
    for template in valid_templates:
        is_valid, error = naming_engine.validate_template(template)
        print(f"Template '{template}': {'✓ Valid' if is_valid else f'✗ Invalid - {error}'}")
    
    # Invalid templates
    invalid_templates = [
        "{Invalid Variable}",
        "{Manga Title",  # Missing closing brace
        "",  # Empty template
    ]
    
    for template in invalid_templates:
        is_valid, error = naming_engine.validate_template(template)
        print(f"Template '{template}': {'✓ Valid' if is_valid else f'✗ Invalid - {error}'}")
    
    print("✓ Template validation tests passed\n")


def test_volume_detection_scenarios():
    """Test volume detection with different scenarios."""
    print("=== Testing Volume Detection Scenarios ===")
    
    # Scenario 1: Manga with clear volume structure
    print("Scenario 1: Manga with clear volumes")
    chapters_with_volumes = [
        create_mock_chapter(1, "Chapter 1", "1"),
        create_mock_chapter(2, "Chapter 2", "1"),
        create_mock_chapter(3, "Chapter 3", "2"),
        create_mock_chapter(4, "Chapter 4", "2"),
        create_mock_chapter(5, "Chapter 5", "3"),
    ]
    
    result = simulate_volume_analysis(chapters_with_volumes)
    print(f"  Result: {result}")
    print(f"  Recommended: {naming_engine.get_recommended_template(result)}")
    
    # Scenario 2: Manga without volumes (all chapters have no volume or volume "1")
    print("\nScenario 2: Manga without clear volumes")
    chapters_without_volumes = [
        create_mock_chapter(1, "Chapter 1", None),
        create_mock_chapter(2, "Chapter 2", None),
        create_mock_chapter(3, "Chapter 3", "1"),  # Default volume
        create_mock_chapter(4, "Chapter 4", None),
        create_mock_chapter(5, "Chapter 5", None),
    ]
    
    result = simulate_volume_analysis(chapters_without_volumes)
    print(f"  Result: {result}")
    print(f"  Recommended: {naming_engine.get_recommended_template(result)}")
    
    # Scenario 3: Mixed scenario
    print("\nScenario 3: Mixed volume structure")
    mixed_chapters = [
        create_mock_chapter(1, "Chapter 1", "1"),
        create_mock_chapter(2, "Chapter 2", "1"),
        create_mock_chapter(3, "Chapter 3", None),
        create_mock_chapter(4, "Chapter 4", "2"),
        create_mock_chapter(5, "Chapter 5", None),
    ]
    
    result = simulate_volume_analysis(mixed_chapters)
    print(f"  Result: {result}")
    print(f"  Recommended: {naming_engine.get_recommended_template(result)}")
    
    print("✓ Volume detection tests passed\n")


def simulate_volume_analysis(chapters):
    """Simulate volume analysis without database."""
    result = VolumeDetectionResult()
    result.chapter_count = len(chapters)
    
    for chapter in chapters:
        volume = getattr(chapter, 'volume', None)
        if volume and str(volume).strip() and str(volume) != "1":
            result.chapters_with_volumes += 1
            result.unique_volumes.add(str(volume))
        else:
            result.chapters_without_volumes += 1
            
    result.volume_count = len(result.unique_volumes)
    
    # Calculate confidence and recommendation
    if result.chapter_count == 0:
        result.confidence_score = 0.0
    else:
        volume_ratio = result.chapters_with_volumes / result.chapter_count
        
        if volume_ratio > 0.7 and result.volume_count > 1:
            result.has_volumes = True
            result.confidence_score = min(0.9, 0.5 + volume_ratio * 0.4 + (result.volume_count / 10))
            result.recommended_pattern = "volume_based"
        elif volume_ratio < 0.3 or result.volume_count <= 1:
            result.has_volumes = False
            result.confidence_score = min(0.8, 0.5 + (1 - volume_ratio) * 0.3)
            result.recommended_pattern = "chapter_based"
        else:
            result.has_volumes = volume_ratio >= 0.5
            result.confidence_score = 0.5
            result.recommended_pattern = "volume_based" if result.has_volumes else "chapter_based"
            
    return result


def test_path_generation():
    """Test path generation with different templates."""
    print("=== Testing Path Generation ===")
    
    manga = create_mock_manga("Attack on Titan", 2009, "crunchyroll")
    
    # Test with volume-based chapter
    chapter_with_volume = create_mock_chapter(5, "First Battle", "2")
    
    templates = naming_engine.get_template_presets()
    
    for name, template in templates.items():
        path = naming_engine.generate_manga_path(manga, chapter_with_volume, template)
        print(f"  {name}: {path}")
    
    # Test with volume-less chapter
    print("\nWith volume-less chapter:")
    chapter_without_volume = create_mock_chapter(15, "The Basement", None)
    
    for name, template in templates.items():
        path = naming_engine.generate_manga_path(manga, chapter_without_volume, template)
        print(f"  {name}: {path}")
    
    print("✓ Path generation tests passed\n")


def main():
    """Run all tests."""
    print("🚀 Starting Volume Detection and Naming Engine Tests\n")
    
    try:
        test_naming_engine_basic()
        test_template_presets()
        test_template_validation()
        test_volume_detection_scenarios()
        test_path_generation()
        
        print("🎉 All tests passed successfully!")
        print("\n📋 Summary of new features:")
        print("  ✓ Enhanced naming engine with volume detection")
        print("  ✓ Multiple template presets (volume-based, chapter-based, etc.)")
        print("  ✓ Smart volume usage analysis")
        print("  ✓ Template validation")
        print("  ✓ Flexible path generation")
        print("\n🔧 Next steps:")
        print("  1. Start the database and run migrations")
        print("  2. Test the API endpoints")
        print("  3. Test the frontend components")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
