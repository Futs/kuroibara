#!/usr/bin/env python3
"""Search all providers for a specific query and display results."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.providers.registry import provider_registry


async def search_all_providers(query: str):
    """Search all providers for a query and display results."""
    print(f"🔍 Searching all providers for '{query}'")
    print("=" * 80)
    print()

    # Get all providers
    providers = provider_registry.get_all_providers()
    print(f"📋 Found {len(providers)} providers")
    print()

    results_summary = []

    for i, provider in enumerate(providers, 1):
        print(f"{i}️⃣  {provider.name}")
        print("-" * 80)

        try:
            # Search the provider
            results, total, has_more = await provider.search(query, limit=5)

            if not results:
                print("  ❌ No results found")
                results_summary.append(
                    {"provider": provider.name, "count": 0, "status": "no_results"}
                )
            else:
                print(f"  ✅ Found {len(results)} results (total: {total})")
                results_summary.append(
                    {
                        "provider": provider.name,
                        "count": len(results),
                        "status": "success",
                    }
                )

                # Display first 3 results
                for j, result in enumerate(results[:3], 1):
                    print(f"    Result #{j}:")
                    print(f"      Title: {result.title}")
                    print(f"      ID: {result.id}")
                    print(f"      URL: {result.url}")
                    if result.year:
                        print(f"      Year: {result.year}")
                    if result.cover_image:
                        print(f"      Cover: {result.cover_image[:60]}...")
                    print()

                if len(results) > 3:
                    print(f"    ... and {len(results) - 3} more results")
                    print()

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results_summary.append(
                {"provider": provider.name, "count": 0, "status": f"error: {e}"}
            )

        print()

    # Print summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print()

    success_count = sum(1 for r in results_summary if r["status"] == "success")
    no_results_count = sum(1 for r in results_summary if r["status"] == "no_results")
    error_count = sum(1 for r in results_summary if r["status"].startswith("error"))

    print(f"✅ Successful: {success_count}")
    print(f"❌ No Results: {no_results_count}")
    print(f"⚠️  Errors: {error_count}")
    print()

    # Show providers with results
    providers_with_results = [r for r in results_summary if r["count"] > 0]
    if providers_with_results:
        print("Providers with results:")
        for r in providers_with_results:
            print(f"  • {r['provider']}: {r['count']} results")
    else:
        print("No providers returned results")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "One Piece"
    asyncio.run(search_all_providers(query))
