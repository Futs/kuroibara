#!/usr/bin/env python3
"""
Test MangaSail provider with cleaned titles.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.providers.mangasail import MangaSailProvider


async def test_mangasail_cleaned():
    """Test MangaSail provider with title cleaning."""
    print("Testing MangaSail Provider - Title Cleaning")
    print("=" * 50)
    
    provider = MangaSailProvider()
    
    # Test title cleaning function directly
    print("1. Testing title cleaning function:")
    print("-" * 40)
    
    test_titles = [
        "Mercenary Enrollment 251",
        "One Piece 1157", 
        "Murim Login 234",
        "Boruto: Two Blue Vortex 24",
        "Superhuman Era 200",
        "Swordmaster'S Youngest Son 172",
        "Attack on Titan",  # No number
        "My Hero Academia 123.5",  # Decimal number
    ]
    
    for title in test_titles:
        cleaned = provider._clean_manga_title(title)
        print(f"  '{title}' -> '{cleaned}'")
    
    # Test base manga ID extraction
    print("\n2. Testing base manga ID extraction:")
    print("-" * 40)
    
    test_urls = [
        "mercenary-enrollment-251",
        "one-piece-1157",
        "murim-login-234", 
        "boruto-two-blue-vortex-24",
        "superhuman-era-200",
        "attack-on-titan",  # No number
        "my-hero-academia-123.5",  # Decimal
    ]
    
    for url_id in test_urls:
        base_id = provider._extract_base_manga_id(url_id)
        print(f"  '{url_id}' -> '{base_id}'")
    
    # Test get_available_manga with cleaned titles
    print("\n3. Testing get_available_manga with cleaned titles:")
    print("-" * 40)
    
    try:
        results, total, has_more = await provider.get_available_manga(page=1, limit=5)
        print(f"Results: {len(results)}")
        print(f"Total: {total}")
        print(f"Has more: {has_more}")
        
        if results:
            print("\nCleaned results:")
            for i, result in enumerate(results):
                print(f"  {i+1}. Title: '{result.title}'")
                print(f"     ID: '{result.id}'")
                print(f"     URL: '{result.url}'")
                print()
        else:
            print("No results returned")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mangasail_cleaned())
