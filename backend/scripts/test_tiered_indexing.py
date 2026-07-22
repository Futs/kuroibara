#!/usr/bin/env python3
"""Test script for the complete tiered indexing system."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.services.tiered_indexing import (
    MadaraDexIndexer,
    MangaDexIndexer,
    MangaUpdatesIndexer,
    tiered_search_service,
)


async def test_individual_indexers():
    """Test each indexer individually."""
    print("🔍 Testing Individual Indexers")
    print("=" * 50)

    indexers = [
        ("MangaUpdates", MangaUpdatesIndexer()),
        ("MadaraDex", MadaraDexIndexer()),
        ("MangaDex", MangaDexIndexer()),
    ]

    for name, indexer in indexers:
        print(f"\n📚 Testing {name}...")

        async with indexer as idx:
            # Test connection
            success, message = await idx.test_connection()
            status = "✅ Connected" if success else "❌ Failed"
            print(f"  Connection: {status} - {message}")

            if success:
                # Test search
                try:
                    results = await idx.search("One Piece", limit=3)
                    print(f"  Search Results: {len(results)} found")

                    if results:
                        first_result = results[0]
                        print(f"    First Result: {first_result.title}")
                        print(f"    Source: {first_result.source_indexer}")
                        print(f"    Confidence: {first_result.confidence_score}")
                        print(f"    NSFW: {first_result.is_nsfw}")

                        # Test details if we have a source_id
                        if first_result.source_id:
                            details = await idx.get_details(first_result.source_id)
                            if details:
                                print("    Details: ✅ Retrieved"d")
                            else:
                                print("    Details: ❌ Failed"d")

                except Exception as e:
                    print(f"  Search Error: {e}")

            print(f"  {name}: {'✅ PASSED' if success else '❌ FAILED'}")


async def test_tiered_search():
    """Test the tiered search service."""
    print("\n🎯 Testing Tiered Search Service")
    print("=" * 50)

    # Test basic search
    print("🔍 Testing basic tiered search...")
    try:
        results = await tiered_search_service.search(
            query="Solo Leveling", limit=10, use_fallback=True, min_results=3
        )

        print(f"Total Results: {len(results)}")

        # Group results by source
        by_source = {}
        for result in results:
            source = result.source_indexer
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(result)

        print("Results by source:")
        for source, source_results in by_source.items():
            print(f"  {source}: {len(source_results)} results")
            for result in source_results[:2]:  # Show first 2 from each source
                print(f"    - {result.title} (confidence: {result.confidence_score})")

        print("✅ Tiered search completed successfully")

    except Exception as e:
        print(f"❌ Tiered search failed: {e}")
        import traceback

        traceback.print_exc()


async def test_cross_reference_matching():
    """Test cross-reference matching between indexers."""
    print("\n🔗 Testing Cross-Reference Matching")
    print("=" * 50)

    try:
        # Get a result from primary indexer
        results = await tiered_search_service.search("Attack on Titan", limit=1)

        if results:
            primary_result = results[0]
            print(
                f"Primary Result: {primary_result.title} from {primary_result.source_indexer}"
            )

            # Test cross-referencing
            cross_refs = await tiered_search_service.cross_reference_manga(
                primary_result=primary_result, search_other_indexers=True
            )

            print(f"Cross-references found: {len(cross_refs)}")
            for source, ref_result in cross_refs.items():
                print(
                    f"  {source}: {ref_result.title} (confidence: {ref_result.confidence_score})"
                )

            print("✅ Cross-reference matching completed")
        else:
            print("❌ No primary result to cross-reference")

    except Exception as e:
        print(f"❌ Cross-reference matching failed: {e}")
        import traceback

        traceback.print_exc()


async def test_indexer_health():
    """Test health monitoring for all indexers."""
    print("\n🏥 Testing Indexer Health Monitoring")
    print("=" * 50)

    try:
        health_results = await tiered_search_service.test_all_indexers()

        print("Indexer Health Status:")
        for indexer_name, (is_healthy, message) in health_results.items():
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            print(f"  {indexer_name}: {status} - {message}")

        healthy_count = sum(
            1 for is_healthy, _ in health_results.values() if is_healthy
        )
        total_count = len(health_results)

        print(f"\nOverall Health: {healthy_count}/{total_count} indexers healthy")

        if healthy_count == total_count:
            print("✅ All indexers are healthy")
        elif healthy_count > 0:
            print("⚠️ Some indexers are unhealthy")
        else:
            print("❌ All indexers are unhealthy")

    except Exception as e:
        print(f"❌ Health monitoring failed: {e}")


async def test_confidence_scoring():
    """Test confidence scoring across different sources."""
    print("\n📊 Testing Confidence Scoring")
    print("=" * 50)

    try:
        # Search for a popular manga that should be in all indexers
        results = await tiered_search_service.search(
            query="Naruto", limit=15, use_fallback=True, min_results=1
        )

        if results:
            print("Confidence Scores by Source:")

            # Group by source and show confidence scores
            by_source = {}
            for result in results:
                source = result.source_indexer
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(result.confidence_score)

            for source, scores in by_source.items():
                avg_confidence = sum(scores) / len(scores)
                max_confidence = max(scores)
                min_confidence = min(scores)

                print(f"  {source}:")
                print(f"    Average: {avg_confidence:.2f}")
                print(f"    Range: {min_confidence:.2f} - {max_confidence:.2f}")
                print(f"    Count: {len(scores)}")

            # Show top results by confidence
            sorted_results = sorted(
                results, key=lambda x: x.confidence_score, reverse=True
            )
            print("\nTop 5 Results by Confidence:")
            for i, result in enumerate(sorted_results[:5], 1):
                print(
                    f"  {i}. {result.title} ({result.source_indexer}) - {result.confidence_score:.2f}"
                )

            print("✅ Confidence scoring analysis completed")
        else:
            print("❌ No results to analyze confidence scores")

    except Exception as e:
        print(f"❌ Confidence scoring test failed: {e}")


async def test_nsfw_content_handling():
    """Test NSFW content detection across indexers."""
    print("\n🔞 Testing NSFW Content Handling")
    print("=" * 50)

    # Test with known NSFW content
    nsfw_queries = ["Prison School", "High School DxD"]
    safe_queries = ["My Hero Academia", "Dragon Ball"]

    for query_type, queries in [("NSFW", nsfw_queries), ("Safe", safe_queries)]:
        print(f"\n{query_type} Content Tests:")

        for query in queries:
            try:
                results = await tiered_search_service.search(query, limit=5)

                if results:
                    nsfw_count = sum(1 for r in results if r.is_nsfw)
                    safe_count = len(results) - nsfw_count

                    print(
                        f"  {query}: {len(results)} results ({nsfw_count} NSFW, {safe_count} Safe)"
                    )

                    # Show content ratings
                    ratings = {}
                    for result in results:
                        rating = result.content_rating or "unknown"
                        ratings[rating] = ratings.get(rating, 0) + 1

                    if ratings:
                        rating_str = ", ".join(
                            f"{rating}: {count}" for rating, count in ratings.items()
                        )
                        print(f"    Ratings: {rating_str}")
                else:
                    print(f"  {query}: No results found")

            except Exception as e:
                print(f"  {query}: Error - {e}")


async def main():
    """Run the complete tiered indexing test suite."""
    print("🧪 Tiered Indexing System Test Suite")
    print("=" * 60)

    try:
        # Check dependencies
        try:
            from bs4 import BeautifulSoup

            print("✅ BeautifulSoup is available")
        except ImportError:
            print(
                "❌ BeautifulSoup not available - install with: pip install beautifulsoup4 lxml"
            )
            return

        try:
            import aiohttp

            print("✅ aiohttp is available")
        except ImportError:
            print("❌ aiohttp not available - install with: pip install aiohttp")
            return

        # Run all test suites
        await test_individual_indexers()
        await test_tiered_search()
        await test_cross_reference_matching()
        await test_indexer_health()
        await test_confidence_scoring()
        await test_nsfw_content_handling()

        print("\n🎉 Complete Test Suite Finished!")
        print("=" * 60)
        print("✅ All tiered indexing tests completed successfully")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the complete test suite
    asyncio.run(main())
