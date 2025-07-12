#!/usr/bin/env python3
"""
Test FlareSolverr-enabled providers end-to-end.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.providers.registry import ProviderRegistry


async def test_provider_search(provider, provider_name: str):
    """Test search functionality for a provider."""
    print(f"🔍 Testing search for {provider_name}...")

    try:
        results, total, has_more = await provider.search("naruto", page=1, limit=5)

        print(f"  ✅ Search successful: {len(results)} results")
        if results:
            sample = results[0]
            print(f"  📖 Sample result: {sample.title}")
            print(f"  🔗 URL: {sample.url}")
            if sample.cover_image:
                print(f"  🖼️  Cover: {sample.cover_image}")

            return True, sample.id if hasattr(sample, "id") else None
        else:
            print(f"  ⚠️  No results found")
            return True, None

    except Exception as e:
        print(f"  ❌ Search failed: {e}")
        return False, None


async def test_provider_metadata(provider, provider_name: str, manga_id: str):
    """Test metadata extraction for a provider."""
    if not manga_id:
        print(f"  ⏭️  Skipping metadata test - no manga ID")
        return False

    print(f"📋 Testing metadata for {provider_name} (ID: {manga_id})...")

    try:
        metadata = await provider.get_manga_details(manga_id)

        if metadata and isinstance(metadata, dict):
            print(f"  ✅ Metadata successful")
            print(f"  📖 Title: {metadata.get('title', 'N/A')}")
            print(f"  📝 Description: {metadata.get('description', 'N/A')[:100]}...")
            if metadata.get("cover_image"):
                print(f"  🖼️  Cover: {metadata.get('cover_image')}")
            return True
        else:
            print(f"  ❌ No metadata returned")
            return False

    except Exception as e:
        print(f"  ❌ Metadata failed: {e}")
        return False


async def test_cloudflare_providers():
    """Test all Cloudflare-enabled providers."""
    print("🚀 Testing FlareSolverr-enabled providers...")

    # Set FlareSolverr URL
    os.environ["FLARESOLVERR_URL"] = "http://172.16.40.12:8191"

    # Create registry
    registry = ProviderRegistry()

    # Get Cloudflare providers
    cloudflare_provider_names = [
        "ReaperScans",
        "Manhuaga",
        "MangaFire",
        "MangaReaderTo",
    ]

    results = {}

    for provider_name in cloudflare_provider_names:
        print(f"\n{'='*50}")
        print(f"Testing {provider_name}")
        print(f"{'='*50}")

        provider = registry.get_provider(provider_name.lower())
        if not provider:
            print(f"❌ Provider {provider_name} not found")
            results[provider_name] = {"available": False}
            continue

        results[provider_name] = {"available": True}

        # Test search
        search_success, manga_id = await test_provider_search(provider, provider_name)
        results[provider_name]["search"] = search_success

        # Test metadata if we got a manga ID
        if search_success and manga_id:
            metadata_success = await test_provider_metadata(
                provider, provider_name, manga_id
            )
            results[provider_name]["metadata"] = metadata_success
        else:
            results[provider_name]["metadata"] = False

        # Small delay between providers
        await asyncio.sleep(2)

    return results


def print_summary(results):
    """Print test summary."""
    print(f"\n{'='*60}")
    print("📊 FLARESOLVERR PROVIDER TEST SUMMARY")
    print(f"{'='*60}")

    total_providers = len(results)
    available_providers = sum(1 for r in results.values() if r.get("available", False))
    working_search = sum(1 for r in results.values() if r.get("search", False))
    working_metadata = sum(1 for r in results.values() if r.get("metadata", False))

    print(f"Total Cloudflare providers: {total_providers}")
    print(f"Available providers: {available_providers}")
    print(f"Working search: {working_search}")
    print(f"Working metadata: {working_metadata}")
    print()

    for provider_name, result in results.items():
        status_parts = []
        if not result.get("available", False):
            status_parts.append("❌ Not Available")
        else:
            if result.get("search", False):
                status_parts.append("✅ Search")
            else:
                status_parts.append("❌ Search")

            if result.get("metadata", False):
                status_parts.append("✅ Metadata")
            else:
                status_parts.append("❌ Metadata")

        status = " | ".join(status_parts)
        print(f"{provider_name:15} : {status}")

    print()
    success_rate = (
        (working_search / available_providers * 100) if available_providers > 0 else 0
    )
    print(
        f"🎯 Success Rate: {success_rate:.1f}% ({working_search}/{available_providers} providers working)"
    )

    if working_search > 0:
        print("🎉 FlareSolverr integration is working!")
    else:
        print("⚠️  No providers are working - check FlareSolverr configuration")


async def main():
    """Main test function."""
    print("🧪 Testing FlareSolverr Provider Integration")
    print("=" * 60)

    # Test providers
    results = await test_cloudflare_providers()

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
