#!/usr/bin/env python3
"""
Debug MangaSail provider to see why it's not returning results.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.providers.enhanced_generic import EnhancedGenericProvider
from bs4 import BeautifulSoup


async def debug_mangasail():
    """Debug MangaSail step by step."""
    print("Debugging MangaSail Provider")
    print("=" * 40)
    
    # Create MangaSail provider with the exact config from providers_default.json
    provider = EnhancedGenericProvider(
        base_url="https://www.sailmg.com",
        search_url="https://www.sailmg.com/search?q={query}",
        manga_url_pattern="https://www.sailmg.com/content/{manga_id}",
        chapter_url_pattern="https://www.sailmg.com/content/{chapter_id}",
        name="MangaSail",
        selectors={
            "search_items": ["a.mtitle", "a[href*='/content/']"],
            "title": ["text()", ".mtitle", "a.mtitle"],
            "cover": ["img", ".cover img", ".thumbnail img"],
            "link": ["self", "a.mtitle", "a[href*='/content/']"],
            "description": [".description", ".summary"]
        },
        supports_nsfw=False
    )
    
    try:
        print("1. Testing get_available_manga method:")
        print("-" * 40)
        
        # Get the homepage content manually first
        html = await provider._make_request("https://www.sailmg.com/")
        if not html:
            print("Failed to fetch homepage")
            return
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Test the search_items selector
        print("2. Testing search_items selectors:")
        for selector in ["a.mtitle", "a[href*='/content/']"]:
            items = soup.select(selector)
            print(f"   '{selector}' found {len(items)} items")
            
            if items:
                for i, item in enumerate(items[:3]):
                    print(f"      {i+1}. Text: '{item.get_text(strip=True)[:50]}...'")
                    print(f"         Href: {item.get('href', 'No href')}")
                    print(f"         Tag: {item.name}")
                    print(f"         Classes: {item.get('class', [])}")
                    print()
        
        # Test the enhanced provider's extraction methods
        print("3. Testing title extraction on a.mtitle elements:")
        print("-" * 40)
        
        mtitle_items = soup.select("a.mtitle")
        for i, item in enumerate(mtitle_items[:3]):
            print(f"   Item {i+1}:")
            
            # Test different title extraction methods
            title_methods = [
                ("get_text()", item.get_text(strip=True)),
                ("text content", item.string),
                ("title attribute", item.get('title', 'None')),
                ("aria-label", item.get('aria-label', 'None'))
            ]
            
            for method, result in title_methods:
                print(f"      {method}: '{result}'")
            
            # Test link extraction
            href = item.get('href', '')
            if href:
                # Extract manga ID manually like the provider does
                manga_id = href.split("/")[-1] or href.split("/")[-2]
                print(f"      Extracted manga_id: '{manga_id}'")
            
            print()
        
        # Now test the actual get_available_manga method
        print("4. Testing get_available_manga method:")
        print("-" * 40)
        
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
            print("No results returned - investigating why...")
            
            # Let's manually test the extraction process
            print("\n5. Manual extraction test:")
            print("-" * 40)
            
            items = soup.select("a.mtitle")
            print(f"Found {len(items)} a.mtitle items")
            
            for i, item in enumerate(items[:2]):
                print(f"\nProcessing item {i+1}:")
                
                # Test manual extraction
                title = item.get_text(strip=True)
                print(f"   Manual title: '{title}'")

                href = item.get('href', '')
                print(f"   Manual link: '{href}'")

                if href:
                    manga_id = href.split("/")[-1] or href.split("/")[-2]
                    print(f"   Manual manga_id: '{manga_id}'")
                
                if not title or title == "Unknown Title":
                    print(f"   ❌ Title extraction failed!")
                if not manga_id:
                    print(f"   ❌ Manga ID extraction failed!")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_mangasail())
