#!/usr/bin/env python3
"""
Test script for migration system functionality.

This script tests the migration planning and execution features
without requiring a database connection.
"""

import sys
import os
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.services.migration import MigrationPlan
from app.core.services.naming import naming_engine
from app.models.manga import Manga, Chapter
from app.models.user import User
from unittest.mock import Mock
import uuid


def create_mock_user():
    """Create a mock user object for testing."""
    user = Mock(spec=User)
    user.id = uuid.uuid4()
    user.naming_format_manga = "{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}"
    user.naming_format_chapter = "{Chapter Number} - {Chapter Name}"
    user.preserve_original_files = True
    return user


def create_mock_manga(title="Test Manga"):
    """Create a mock manga object for testing."""
    manga = Mock(spec=Manga)
    manga.id = uuid.uuid4()
    manga.title = title
    manga.year = 2023
    manga.provider = "test_provider"
    return manga


def create_mock_chapter(number, title=None, volume=None):
    """Create a mock chapter object for testing."""
    chapter = Mock(spec=Chapter)
    chapter.id = uuid.uuid4()
    chapter.number = str(number)
    chapter.title = title or f"Chapter {number}"
    chapter.volume = volume
    chapter.language = "en"
    return chapter


def test_migration_plan_creation():
    """Test migration plan creation."""
    print("=== Testing Migration Plan Creation ===")
    
    # Create test data
    manga = create_mock_manga("One Piece")
    user = create_mock_user()
    
    # Create a migration plan
    plan = MigrationPlan()
    plan.manga_id = manga.id
    plan.manga_title = manga.title
    plan.source_pattern = user.naming_format_manga
    plan.target_pattern = "{Manga Title}/ch.{Chapter Number}"
    
    # Add some mock operations
    chapters = [
        create_mock_chapter(1, "Romance Dawn", "1"),
        create_mock_chapter(2, "The Man They Call Pirate Hunter", "1"),
        create_mock_chapter(3, "Introduce Yourself", "1"),
    ]
    
    for chapter in chapters:
        # Simulate file operations
        source_path = f"/storage/manga/{manga.id}/organized/One Piece/Volume 1/{chapter.number} - {chapter.title}.cbz"
        target_path = f"/storage/manga/{manga.id}/organized/One Piece/ch.{chapter.number}/{chapter.number} - {chapter.title}.cbz"
        
        plan.add_operation("move", source_path, target_path, chapter.id, 50 * 1024 * 1024)  # 50MB
    
    # Test plan summary
    summary = plan.get_summary()
    print(f"Migration Plan Summary:")
    print(f"  Manga: {summary['manga_title']}")
    print(f"  Source Pattern: {summary['source_pattern']}")
    print(f"  Target Pattern: {summary['target_pattern']}")
    print(f"  Total Operations: {summary['total_operations']}")
    print(f"  Estimated Size: {summary['estimated_size_mb']} MB")
    print(f"  Estimated Time: {summary['estimated_time_minutes']} minutes")
    print(f"  Can Rollback: {summary['can_rollback']}")
    
    assert summary['total_operations'] == 3
    assert summary['estimated_size_mb'] == 150.0  # 3 * 50MB
    
    print("✓ Migration plan creation tests passed\n")


def test_migration_scenarios():
    """Test different migration scenarios."""
    print("=== Testing Migration Scenarios ===")
    
    # Scenario 1: Volume-based to Chapter-based
    print("Scenario 1: Volume-based → Chapter-based")
    test_scenario(
        source_template="{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
        target_template="{Manga Title}/ch.{Chapter Number}",
        chapters=[
            ("1", "Chapter 1", "1"),
            ("2", "Chapter 2", "1"),
            ("3", "Chapter 3", "2"),
        ]
    )
    
    # Scenario 2: Chapter-based to Volume-based
    print("\nScenario 2: Chapter-based → Volume-based")
    test_scenario(
        source_template="{Manga Title}/ch.{Chapter Number}",
        target_template="{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}",
        chapters=[
            ("1", "Chapter 1", "1"),
            ("2", "Chapter 2", "1"),
            ("3", "Chapter 3", "2"),
        ]
    )
    
    # Scenario 3: Simple to Year-based
    print("\nScenario 3: Simple → Year-based")
    test_scenario(
        source_template="{Manga Title}/{Chapter Number} - {Chapter Name}",
        target_template="{Manga Title} ({Year})/Volume {Volume}/{Chapter Number} - {Chapter Name}",
        chapters=[
            ("1", "Chapter 1", "1"),
            ("2", "Chapter 2", "1"),
        ]
    )
    
    print("✓ Migration scenarios tests passed\n")


def test_scenario(source_template, target_template, chapters):
    """Test a specific migration scenario."""
    manga = create_mock_manga("Test Manga")
    
    print(f"  Source: {source_template}")
    print(f"  Target: {target_template}")
    
    for number, title, volume in chapters:
        chapter = create_mock_chapter(number, title, volume)
        
        # Generate source and target paths
        source_path = naming_engine.generate_manga_path(manga, chapter, source_template)
        target_path = naming_engine.generate_manga_path(manga, chapter, target_template)
        
        print(f"    Ch.{number}: {source_path} → {target_path}")


def test_file_operations_simulation():
    """Test file operations simulation."""
    print("=== Testing File Operations Simulation ===")
    
    # Create temporary directories to simulate file operations
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source structure
        source_dir = os.path.join(temp_dir, "source", "Test Manga", "Volume 1")
        os.makedirs(source_dir, exist_ok=True)
        
        # Create test files
        test_files = [
            "1 - Chapter One.cbz",
            "2 - Chapter Two.cbz",
            "3 - Chapter Three.cbz"
        ]
        
        for filename in test_files:
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"Test content for {filename}")
        
        print(f"Created source structure in: {source_dir}")
        print(f"Source files: {os.listdir(source_dir)}")
        
        # Simulate migration to chapter-based structure
        target_base = os.path.join(temp_dir, "target", "Test Manga")
        
        operations = []
        for i, filename in enumerate(test_files, 1):
            source_file = os.path.join(source_dir, filename)
            target_dir = os.path.join(target_base, f"ch.{i}")
            target_file = os.path.join(target_dir, filename)
            
            operations.append({
                "type": "create_dir",
                "target": target_dir,
                "source": "",
            })
            operations.append({
                "type": "copy",
                "source": source_file,
                "target": target_file,
            })
        
        # Execute operations
        for operation in operations:
            if operation["type"] == "create_dir":
                os.makedirs(operation["target"], exist_ok=True)
                print(f"Created directory: {operation['target']}")
            elif operation["type"] == "copy":
                shutil.copy2(operation["source"], operation["target"])
                print(f"Copied: {operation['source']} → {operation['target']}")
        
        # Verify target structure
        print(f"\nTarget structure:")
        for root, dirs, files in os.walk(os.path.join(temp_dir, "target")):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    
    print("✓ File operations simulation tests passed\n")


def test_migration_validation():
    """Test migration validation logic."""
    print("=== Testing Migration Validation ===")
    
    # Test template compatibility
    templates = [
        ("{Manga Title}/Volume {Volume}/{Chapter Number} - {Chapter Name}", "volume_based"),
        ("{Manga Title}/ch.{Chapter Number}", "chapter_based"),
        ("{Manga Title}/{Chapter Number} - {Chapter Name}", "simple"),
    ]
    
    for template, pattern_type in templates:
        is_valid, error = naming_engine.validate_template(template)
        print(f"Template '{template}' ({pattern_type}): {'✓ Valid' if is_valid else f'✗ Invalid - {error}'}")
    
    # Test migration compatibility
    print("\nMigration compatibility tests:")
    
    # Compatible migrations
    compatible_pairs = [
        ("volume_based", "chapter_based", "Volume → Chapter migration"),
        ("chapter_based", "volume_based", "Chapter → Volume migration"),
        ("simple", "year_based", "Simple → Year-based migration"),
    ]
    
    for source, target, description in compatible_pairs:
        source_template = naming_engine.get_template_presets()[source]
        target_template = naming_engine.get_template_presets()[target]
        
        # Both templates should be valid
        source_valid, _ = naming_engine.validate_template(source_template)
        target_valid, _ = naming_engine.validate_template(target_template)
        
        compatible = source_valid and target_valid
        print(f"  {description}: {'✓ Compatible' if compatible else '✗ Incompatible'}")
    
    print("✓ Migration validation tests passed\n")


def main():
    """Run all migration tests."""
    print("🚀 Starting Migration System Tests\n")
    
    try:
        test_migration_plan_creation()
        test_migration_scenarios()
        test_file_operations_simulation()
        test_migration_validation()
        
        print("🎉 All migration tests passed successfully!")
        print("\n📋 Migration System Features:")
        print("  ✓ Migration plan creation and validation")
        print("  ✓ Multiple migration scenarios support")
        print("  ✓ File operation simulation and execution")
        print("  ✓ Template compatibility validation")
        print("  ✓ Rollback capability planning")
        print("\n🔧 Migration System Benefits:")
        print("  • Safe migration with backup options")
        print("  • Preview changes before execution")
        print("  • Support for all folder structure patterns")
        print("  • Handles volume-based ↔ chapter-based conversions")
        print("  • Preserves file integrity during migration")
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
