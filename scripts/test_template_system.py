#!/usr/bin/env python3
"""
Test script for the template-based provider system.

This script simulates the GitHub Actions workflow locally to test the system.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

def create_test_provider_data():
    """Create test provider data simulating GitHub issue parsing."""
    return {
        "name": "Test Manga Site",
        "id": "testmangasite",
        "base_url": "https://testmanga.example.com",
        "search_url": "https://testmanga.example.com/search?q={query}",
        "type": "Generic (Standard HTML scraping)",
        "priority": "Medium (Well-known community source)",
        "selectors": json.dumps({
            "search_items": [".manga-item", ".search-result"],
            "title": [".title", "h3 a"],
            "cover": [".cover img", ".thumbnail img"],
            "link": ["a[href*='manga']"],
            "description": [".description"],
            "chapters": [".chapter-item"],
            "pages": [".page-image img"]
        }),
        "test_manga": "Title: Test Manga\nURL: https://testmanga.example.com/manga/test\nExpected chapters: 50+",
        "additional_info": "Test provider for validation",
        "features": [],
        "requires_flaresolverr": False,
        "issue_number": 123
    }

def test_config_generation():
    """Test the provider configuration generation."""
    print("🧪 Testing provider configuration generation...")
    
    # Create test data
    test_data = create_test_provider_data()
    
    # Save test data
    with open('provider_config.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Import and run the generator
    sys.path.append('scripts')
    try:
        from generate_provider_config import generate_provider_config
        config = generate_provider_config()
        
        # Validate generated config
        assert config['id'] == 'testmangasite'
        assert config['name'] == 'Test Manga Site'
        assert config['class_name'] == 'GenericProvider'
        assert 'selectors' in config['params']
        
        print("✅ Configuration generation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration generation test failed: {e}")
        return False

def test_provider_loading():
    """Test loading the generated provider."""
    print("🧪 Testing provider loading...")
    
    try:
        # Check if generated config exists
        if not os.path.exists('generated_provider.json'):
            print("❌ Generated provider config not found")
            return False
        
        # Load the config
        with open('generated_provider.json', 'r') as f:
            configs = json.load(f)
        
        if not configs:
            print("❌ No configurations in generated file")
            return False
        
        config = configs[0]
        
        # Validate structure
        required_fields = ['id', 'name', 'class_name', 'url', 'params']
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ Provider loading test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Provider loading test failed: {e}")
        return False

def test_community_provider_structure():
    """Test the community provider directory structure."""
    print("🧪 Testing community provider structure...")
    
    try:
        community_dir = Path('backend/app/core/providers/config/community')
        
        # Check if directory exists
        if not community_dir.exists():
            print("❌ Community providers directory not found")
            return False
        
        # Check if example provider exists
        example_file = community_dir / 'example_provider.json'
        if not example_file.exists():
            print("❌ Example provider not found")
            return False
        
        # Validate example provider
        with open(example_file, 'r') as f:
            example_config = json.load(f)
        
        if not example_config or not isinstance(example_config, list):
            print("❌ Invalid example provider format")
            return False
        
        print("✅ Community provider structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Community provider structure test failed: {e}")
        return False

def test_github_templates():
    """Test GitHub issue templates."""
    print("🧪 Testing GitHub templates...")
    
    try:
        template_file = Path('.github/ISSUE_TEMPLATE/provider-request.yml')
        
        if not template_file.exists():
            print("❌ Provider request template not found")
            return False
        
        # Read and validate template
        with open(template_file, 'r') as f:
            template_content = f.read()
        
        # Check for required fields
        required_sections = [
            'provider_name',
            'provider_id',
            'base_url',
            'search_url',
            'provider_type',
            'selectors'
        ]
        
        for section in required_sections:
            if section not in template_content:
                print(f"❌ Missing template section: {section}")
                return False
        
        print("✅ GitHub templates test passed!")
        return True
        
    except Exception as e:
        print(f"❌ GitHub templates test failed: {e}")
        return False

def test_workflow_file():
    """Test GitHub Actions workflow."""
    print("🧪 Testing GitHub Actions workflow...")
    
    try:
        workflow_file = Path('.github/workflows/provider-validation.yml')
        
        if not workflow_file.exists():
            print("❌ Provider validation workflow not found")
            return False
        
        # Read and validate workflow
        with open(workflow_file, 'r') as f:
            workflow_content = f.read()
        
        # Check for required steps
        required_steps = [
            'Parse issue template',
            'Generate provider config',
            'Test provider functionality',
            'Create Pull Request'
        ]
        
        for step in required_steps:
            if step not in workflow_content:
                print(f"❌ Missing workflow step: {step}")
                return False
        
        print("✅ GitHub Actions workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ GitHub Actions workflow test failed: {e}")
        return False

def cleanup():
    """Clean up test files."""
    test_files = [
        'provider_config.json',
        'generated_provider.json'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)

def main():
    """Run all tests."""
    print("🚀 Template-Based Provider System Test Suite")
    print("=" * 60)
    
    tests = [
        ("GitHub Templates", test_github_templates),
        ("GitHub Actions Workflow", test_workflow_file),
        ("Community Provider Structure", test_community_provider_structure),
        ("Configuration Generation", test_config_generation),
        ("Provider Loading", test_provider_loading),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    # Cleanup
    cleanup()
    
    # Results
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Template system is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
