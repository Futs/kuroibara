#!/usr/bin/env python3
"""
Test custom MangaSail provider.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.providers.mangasail import MangaSailProvider


async def test_mangasail_custom():
    """Test custom MangaSail provider."""
    print("Testing Custom MangaSail Provider")
    print("=" * 40)
    
    provider = MangaSailProvider()
    
    # Test get_available_manga
    print("1. Testing get_available_manga:")
    print("-" * 40)
    
    try:
        results, total, has_more = await provider.get_available_manga(page=1, limit=5)
        print(f"Results: {len(results)}")
        print(f"Total: {total}")
        print(f"Has more: {has_more}")
        
        if results:
            print("\nResults:")
            for i, result in enumerate(results):
                print(f"  {i+1}. Title: '{result.title}'")
                print(f"     ID: '{result.id}'")
                print(f"     URL: '{result.url}'")
                print(f"     Cover: '{result.cover_image[:50]}...'" if result.cover_image else "     Cover: None")
                print()
        else:
            print("No results returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test search
    print("\n2. Testing search for 'naruto':")
    print("-" * 40)
    
    try:
        results, total, has_more = await provider.search("naruto", page=1, limit=3)
        print(f"Results: {len(results)}")
        print(f"Total: {total}")
        print(f"Has more: {has_more}")
        
        if results:
            print("\nSearch results:")
            for i, result in enumerate(results):
                print(f"  {i+1}. Title: '{result.title}'")
                print(f"     ID: '{result.id}'")
                print(f"     URL: '{result.url}'")
                print(f"     Cover: '{result.cover_image[:50]}...'" if result.cover_image else "     Cover: None")
                print()
        else:
            print("No search results returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mangasail_custom())
