#!/usr/bin/env python3
"""Test script for MadaraDex HTML parsing functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.services.tiered_indexing import MadaraDexIndexer


async def test_madaradex_search():
    """Test MadaraDex search functionality."""
    print("🔍 Testing MadaraDex Search Functionality")
    print("=" * 50)

    async with MadaraDexIndexer() as indexer:
        # Test connection first
        print("📡 Testing connection...")
        success, message = await indexer.test_connection()
        print(f"Connection: {'✅ Success' if success else '❌ Failed'} - {message}")

        if not success:
            print("❌ Cannot proceed with tests - connection failed")
            return

        # Test search
        print("\n🔍 Testing search for 'Dead Tube'...")
        try:
            results = await indexer.search("Dead Tube", limit=5)
            print(f"Found {len(results)} results")

            for i, result in enumerate(results, 1):
                print(f"\n📖 Result {i}:")
                print(f"  Title: {result.title}")
                print(f"  Source ID: {result.source_id}")
                print(f"  URL: {result.source_url}")
                print(f"  Type: {result.type}")
                print(f"  NSFW: {result.is_nsfw}")
                print(f"  Genres: {result.genres}")
                print(f"  Cover: {result.cover_image_url}")
                print(f"  Latest Chapter: {result.latest_chapter}")
                print(f"  Confidence: {result.confidence_score}")

                # Test getting details for first result
                if i == 1 and result.source_id:
                    print(f"\n📋 Testing details for: {result.title}")
                    details = await indexer.get_details(result.source_id)
                    if details:
                        print("✅ Details retrieved successfully")
                        print(
                            f"  Description: {details.description[:100] if details.description else 'None'}..."
                        )
                        print(f"  Authors: {details.authors}")
                        print(f"  Artists: {details.artists}")
                        print(f"  Status: {details.status}")
                        print(f"  Year: {details.year}")
                        print(f"  Rating: {details.rating}")
                        print(f"  Alternative Titles: {details.alternative_titles}")
                    else:
                        print("❌ Failed to get details")

        except Exception as e:
            print(f"❌ Search failed: {e}")
            import traceback

            traceback.print_exc()


async def test_madaradex_specific_manga():
    """Test MadaraDex with a specific known manga."""
    print("\n🎯 Testing Specific Manga Details")
    print("=" * 50)

    async with MadaraDexIndexer() as indexer:
        # Test with a known manga URL path
        test_manga_id = "manga/dead-tube"  # Common MadaraDex URL pattern

        print(f"📋 Testing details for manga ID: {test_manga_id}")
        try:
            details = await indexer.get_details(test_manga_id)
            if details:
                print("✅ Details retrieved successfully")
                print(f"  Title: {details.title}")
                print(
                    f"  Description: {details.description[:200] if details.description else 'None'}..."
                )
                print(f"  Type: {details.type}")
                print(f"  Status: {details.status}")
                print(f"  Year: {details.year}")
                print(f"  NSFW: {details.is_nsfw}")
                print(f"  Content Rating: {details.content_rating}")
                print(f"  Genres: {details.genres}")
                print(f"  Tags: {details.tags}")
                print(f"  Authors: {details.authors}")
                print(f"  Artists: {details.artists}")
                print(f"  Rating: {details.rating}")
                print(f"  Latest Chapter: {details.latest_chapter}")
                print(f"  Cover Image: {details.cover_image_url}")
                print(f"  Alternative Titles: {details.alternative_titles}")
                print(f"  Confidence Score: {details.confidence_score}")
            else:
                print("❌ Failed to get details")

        except Exception as e:
            print(f"❌ Details retrieval failed: {e}")
            import traceback

            traceback.print_exc()


async def test_madaradex_error_handling():
    """Test MadaraDex error handling."""
    print("\n🛡️ Testing Error Handling")
    print("=" * 50)

    async with MadaraDexIndexer() as indexer:
        # Test with invalid manga ID
        print("🚫 Testing with invalid manga ID...")
        try:
            details = await indexer.get_details("invalid/manga/id")
            if details:
                print("⚠️ Unexpected success with invalid ID")
            else:
                print("✅ Correctly handled invalid manga ID")
        except Exception as e:
            print(f"✅ Correctly caught exception: {e}")

        # Test with empty search
        print("\n🔍 Testing empty search...")
        try:
            results = await indexer.search("", limit=5)
            print(f"✅ Empty search handled, returned {len(results)} results")
        except Exception as e:
            print(f"✅ Correctly caught exception for empty search: {e}")

        # Test with very long search query
        print("\n📏 Testing very long search query...")
        try:
            long_query = "a" * 1000
            results = await indexer.search(long_query, limit=5)
            print(f"✅ Long query handled, returned {len(results)} results")
        except Exception as e:
            print(f"✅ Correctly caught exception for long query: {e}")


async def test_madaradex_nsfw_detection():
    """Test NSFW content detection."""
    print("\n🔞 Testing NSFW Detection")
    print("=" * 50)

    async with MadaraDexIndexer() as indexer:
        # Test with known NSFW content
        nsfw_queries = ["Secret Class", "Sweet Guy", "Boarding Diary"]

        for query in nsfw_queries:
            print(f"\n🔍 Testing NSFW detection for: {query}")
            try:
                results = await indexer.search(query, limit=3)
                for result in results:
                    nsfw_status = "🔞 NSFW" if result.is_nsfw else "✅ Safe"
                    print(f"  {result.title}: {nsfw_status}")
                    print(f"    Content Rating: {result.content_rating}")
                    print(f"    Genres: {result.genres}")
            except Exception as e:
                print(f"❌ NSFW test failed for {query}: {e}")


async def main():
    """Run all MadaraDex tests."""
    print("🧪 MadaraDex HTML Parsing Test Suite")
    print("=" * 60)

    try:
        # Check if BeautifulSoup is available
        try:
            from bs4 import BeautifulSoup

            print("✅ BeautifulSoup is available")
        except ImportError:
            print(
                "❌ BeautifulSoup not available - install with: pip install beautifulsoup4 lxml"
            )
            return

        # Run all tests
        await test_madaradex_search()
        await test_madaradex_specific_manga()
        await test_madaradex_error_handling()
        await test_madaradex_nsfw_detection()

        print("\n🎉 All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
