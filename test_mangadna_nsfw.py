#!/usr/bin/env python3
"""
Test MangaDNA NSFW detection improvements.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.providers.enhanced_generic import EnhancedGenericProvider


async def test_mangadna_nsfw():
    """Test MangaDNA NSFW detection."""
    print("Testing MangaDNA & Manga18FX NSFW Detection")
    print("=" * 50)

    # Create MangaDNA provider instance
    mangadna_provider = EnhancedGenericProvider(
        base_url="https://mangadna.com",
        search_url="https://mangadna.com/manga",
        manga_url_pattern="https://mangadna.com/manga/{manga_id}",
        chapter_url_pattern="https://mangadna.com/manga/{manga_id}/{chapter_id}",
        name="MangaDNA",
        supports_nsfw=True
    )

    # Create Manga18FX provider instance
    manga18fx_provider = EnhancedGenericProvider(
        base_url="https://manga18fx.com",
        search_url="https://manga18fx.com/manga",
        manga_url_pattern="https://manga18fx.com/manga/{manga_id}",
        chapter_url_pattern="https://manga18fx.com/manga/{manga_id}/{chapter_id}",
        name="Manga18FX",
        supports_nsfw=True
    )

    # Create a regular provider for comparison
    regular_provider = EnhancedGenericProvider(
        base_url="https://example.com",
        search_url="https://example.com/manga",
        manga_url_pattern="https://example.com/manga/{manga_id}",
        chapter_url_pattern="https://example.com/manga/{manga_id}/{chapter_id}",
        name="RegularProvider",
        supports_nsfw=True
    )

    # Test cases - ALL titles from NSFW-only providers should be NSFW
    test_titles = [
        "The Boss's Daughter",
        "My Body Got Switched",
        "Love Limit Exceeded",
        "One Piece",  # Even mainstream titles should be NSFW on these sites
        "Naruto",
        "Dragon Ball",
        "Completely Normal Title",
        "Adventure Story",
        "School Life",
    ]
    
    print("1. Testing MangaDNA (should mark ALL titles as NSFW):")
    print("-" * 50)

    for title in test_titles:
        result = mangadna_provider._detect_nsfw_from_content(title, [])
        status = "✓" if result else "✗"
        print(f"{status} MangaDNA: '{title}' -> NSFW: {result}")

    print(f"\n2. Testing Manga18FX (should mark ALL titles as NSFW):")
    print("-" * 50)

    for title in test_titles:
        result = manga18fx_provider._detect_nsfw_from_content(title, [])
        status = "✓" if result else "✗"
        print(f"{status} Manga18FX: '{title}' -> NSFW: {result}")

    print(f"\n3. Testing Regular Provider (should use normal NSFW detection):")
    print("-" * 50)

    for title in test_titles:
        result = regular_provider._detect_nsfw_from_content(title, [])
        print(f"  RegularProvider: '{title}' -> NSFW: {result}")

    print(f"\n" + "=" * 50)
    print("Summary:")
    print("- MangaDNA: ALL titles should be NSFW = True")
    print("- Manga18FX: ALL titles should be NSFW = True")
    print("- Regular Provider: Only explicit titles should be NSFW = True")


if __name__ == "__main__":
    asyncio.run(test_mangadna_nsfw())
