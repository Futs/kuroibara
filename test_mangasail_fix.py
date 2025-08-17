#!/usr/bin/env python3
"""
Test MangaSail provider fixes.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.providers.enhanced_generic import EnhancedGenericProvider
from bs4 import BeautifulSoup
import aiohttp


async def test_mangasail_selectors():
    """Test different selectors on MangaSail homepage to find the right ones."""
    print("Testing MangaSail Selectors")
    print("=" * 40)
    
    # Create MangaSail provider instance with correct selectors
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
        # Get the homepage content
        print("1. Fetching MangaSail homepage...")
        html = await provider._make_request("https://www.sailmg.com/")
        
        if not html:
            print("   Failed to fetch homepage")
            return
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Test different selectors to find manga items
        test_selectors = [
            "a[href*='/content/']",
            "a[href*='/manga/']", 
            ".manga-item",
            ".item",
            ".entry",
            ".post",
            ".content-item",
            ".list-item",
            ".grid-item",
            "article",
            ".card",
            ".media",
            ".thumbnail",
            "div[class*='item']",
            "div[class*='manga']",
            "div[class*='content']",
            "li",
            "div.row div",
            ".container div",
            "a[title]"
        ]
        
        print("\n2. Testing selectors for manga items:")
        print("-" * 40)
        
        for selector in test_selectors:
            try:
                items = soup.select(selector)
                if items and len(items) > 0:
                    print(f"✓ '{selector}' found {len(items)} items")
                    
                    # Show first few items
                    for i, item in enumerate(items[:3]):
                        text = item.get_text(strip=True)[:50]
                        href = item.get('href', 'No href')
                        print(f"   {i+1}. Text: '{text}...' | Href: {href}")
                    
                    if len(items) > 3:
                        print(f"   ... and {len(items) - 3} more")
                    print()
                else:
                    print(f"✗ '{selector}' found 0 items")
            except Exception as e:
                print(f"✗ '{selector}' error: {e}")
        
        # Look for specific content we know exists
        print("\n3. Looking for known manga titles:")
        print("-" * 40)
        
        known_titles = ["Boruto", "One Piece", "Naruto", "Swordmaster", "Mercenary"]
        
        for title in known_titles:
            # Find elements containing these titles
            elements = soup.find_all(text=lambda text: text and title.lower() in text.lower())
            print(f"'{title}' found in {len(elements)} text elements")
            
            for i, elem in enumerate(elements[:2]):
                parent = elem.parent if elem.parent else None
                if parent:
                    tag_info = f"{parent.name}"
                    if parent.get('class'):
                        tag_info += f".{'.'.join(parent.get('class'))}"
                    if parent.get('href'):
                        tag_info += f" href='{parent.get('href')[:30]}...'"
                    print(f"   {i+1}. {tag_info}: '{elem.strip()[:50]}...'")
        
        print("\n4. Testing specific a.mtitle selector:")
        print("-" * 40)

        mtitle_links = soup.select("a.mtitle")
        print(f"Found {len(mtitle_links)} a.mtitle links")

        for i, link in enumerate(mtitle_links[:5]):
            title = link.get_text(strip=True)
            href = link.get('href', 'No href')
            print(f"   {i+1}. Title: '{title}' | Href: {href}")

        print("\n5. Testing get_available_manga method:")
        print("-" * 40)
        
        results, total, has_more = await provider.get_available_manga(page=1, limit=5)
        print(f"Results: {len(results)}")
        print(f"Total: {total}")
        print(f"Has more: {has_more}")
        
        if results:
            print("\nFirst few results:")
            for i, result in enumerate(results):
                print(f"  {i+1}. Title: {result.title}")
                print(f"     ID: {result.id}")
                print(f"     URL: {result.url}")
                print(f"     Cover: {result.cover_image[:50]}..." if result.cover_image else "     Cover: None")
                print()
        else:
            print("No results returned")
            
    except Exception as e:
        print(f"Error testing MangaSail: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mangasail_selectors())
