#!/usr/bin/env python3
"""Debug provider matching for specific manga."""

import asyncio
import sys
from difflib import SequenceMatcher

sys.path.insert(0, "/app")

from app.core.providers.registry import provider_registry
from app.core.services.mangaupdates import mangaupdates_service
from app.db.session import AsyncSessionLocal


async def debug_provider_matching():
    """Debug provider matching for One Piece."""
    print("🔍 DEBUG: Provider Matching for 'One Piece'\n")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Step 0: Show what MangaUpdates search returns
        print("\n0️⃣  Checking MangaUpdates search results for 'One Piece'...")
        search_results = await mangaupdates_service.search("One Piece")
        if search_results:
            print(f"✅ MangaUpdates returned {len(search_results)} results:")
            for i, result in enumerate(search_results[:5], 1):
                print(f"   {i}. {result.get('title')} (ID: {result.get('series_id')})")
        else:
            print("❌ No search results")

        # Step 1: Get MangaUpdates entry for One Piece
        print("\n1️⃣  Getting MangaUpdates entry for 'One Piece'...")
        mu_entry = await mangaupdates_service.search_and_create_entry(
            "One Piece", db, auto_select_best=True
        )

        if not mu_entry:
            print("❌ Failed to find One Piece in MangaUpdates")
            return

        print(f"✅ Found: {mu_entry.title}")
        print(f"   MU Series ID: {mu_entry.mu_series_id}")
        print(f"   Year: {mu_entry.year}")
        print(f"   Alternative titles: {mu_entry.alternative_titles}")

        # Step 2: Get all providers
        print("\n2️⃣  Getting available providers...")
        all_providers = provider_registry.get_all_providers()
        print(f"✅ Found {len(all_providers)} total providers")

        # Step 3: Select 3 providers to test
        test_providers = ["MangaDex", "MangaPill", "MangaSail"]
        print(f"\n3️⃣  Testing with providers: {', '.join(test_providers)}")

        # Step 4: Search each provider
        for provider_name in test_providers:
            print(f"\n{'=' * 80}")
            print(f"🔎 Testing Provider: {provider_name}")
            print(f"{'=' * 80}")

            provider = provider_registry.get_provider(provider_name)
            if not provider:
                print(f"❌ Provider '{provider_name}' not found in registry")
                continue

            # Search with main title
            search_term = mu_entry.title
            print(f"\n📝 Search term: '{search_term}'")

            try:
                print(f"   Calling provider.search('{search_term}', limit=5)...")
                results, total, has_next = await provider.search(search_term, limit=5)

                print(f"   ✅ Search returned {len(results)} results (total: {total})")

                if not results:
                    print(f"   ⚠️  No results found")
                    continue

                # Analyze each result
                print(f"\n   📊 Analyzing results:")
                for i, result in enumerate(results, 1):
                    # Calculate confidence
                    title_similarity = SequenceMatcher(
                        None, mu_entry.title.lower(), result.title.lower()
                    ).ratio()
                    confidence = title_similarity * 0.7

                    # Check year match
                    year_match = False
                    if (
                        mu_entry.year
                        and hasattr(result, "year")
                        and result.year
                        and abs(mu_entry.year - result.year) <= 1
                    ):
                        confidence += 0.1
                        year_match = True

                    print(f"\n   Result #{i}:")
                    print(f"      Title: {result.title}")
                    print(f"      ID: {result.id}")
                    print(f"      URL: {result.url if hasattr(result, 'url') else 'N/A'}")
                    print(
                        f"      Year: {result.year if hasattr(result, 'year') else 'N/A'}"
                    )
                    print(f"      Title Similarity: {title_similarity:.3f}")
                    print(f"      Confidence Score: {confidence:.3f}")
                    print(
                        f"      Meets Threshold (0.7): {'✅ YES' if confidence >= 0.7 else '❌ NO'}"
                    )

            except Exception as e:
                print(f"   ❌ Error searching provider: {e}")
                import traceback

                traceback.print_exc()

        print(f"\n{'=' * 80}")
        print("✅ Debug complete")


if __name__ == "__main__":
    asyncio.run(debug_provider_matching())

