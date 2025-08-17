#!/usr/bin/env python3
"""
Quick test for MangaPill fixes.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.providers.mangapill import MangaPillProvider


async def test_mangapill():
    """Test MangaPill search and available manga."""
    print("Testing MangaPill Provider Fixes")
    print("=" * 40)
    
    provider = MangaPillProvider()
    
    # Test search functionality
    print("\n1. Testing Search for 'naruto':")
    try:
        results, total, has_more = await provider.search("naruto", page=1, limit=3)
        print(f"   Results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   {i+1}. Title: {result.title}")
            print(f"      ID: {result.id}")
            print(f"      Cover: {result.cover_image[:60]}..." if result.cover_image else "      Cover: None")
            print(f"      URL: {result.url}")
            print()
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test available manga
    print("\n2. Testing Available Manga:")
    try:
        results, total, has_more = await provider.get_available_manga(page=1, limit=3)
        print(f"   Results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"   {i+1}. Title: {result.title}")
            print(f"      ID: {result.id}")
            print(f"      Cover: {result.cover_image[:60]}..." if result.cover_image else "      Cover: None")
            print(f"      URL: {result.url}")
            print()
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mangapill())
