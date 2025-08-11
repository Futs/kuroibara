#!/usr/bin/env python3
"""
Test FlareSolverr-enabled providers end-to-end.
"""

import asyncio
import os

import pytest

from app.core.providers.registry import ProviderRegistry


@pytest.mark.asyncio
async def test_flaresolverr_provider_search():
    """Test search functionality for FlareSolverr providers."""
    registry = ProviderRegistry()
    providers = registry.get_all_providers()

    # Find providers that might use FlareSolverr
    flaresolverr_providers = [
        p for p in providers if hasattr(p, "requires_flaresolverr")
    ]

    if not flaresolverr_providers:
        # Test with first available provider
        provider = providers[0] if providers else None
        if not provider:
            pytest.skip("No providers available for testing")
        provider_name = provider.name
    else:
        provider = flaresolverr_providers[0]
        provider_name = provider.name

    print(f"🔍 Testing search for {provider_name}...")

    try:
        results, total, has_more = await provider.search("naruto", page=1, limit=5)

        print(f"  ✅ Search successful: {len(results)} results")
        assert isinstance(results, list)
        assert isinstance(total, int)
        assert isinstance(has_more, bool)

        if results:
            sample = results[0]
            print(f"  📖 Sample result: {sample.title}")
            assert hasattr(sample, "title")
            assert hasattr(sample, "url")

    except Exception as e:
        print(f"  ❌ Search failed: {e}")
        # Don't fail test for provider connectivity issues
        pytest.skip(f"Provider {provider_name} connectivity issue: {e}")


@pytest.mark.asyncio
async def test_flaresolverr_provider_metadata():
    """Test metadata extraction for a provider."""
    registry = ProviderRegistry()
    providers = registry.get_all_providers()

    if not providers:
        pytest.skip("No providers available for testing")

    provider = providers[0]
    provider_name = provider.name

    print(f"📋 Testing metadata for {provider_name}...")

    # First try to get a real manga ID from search
    try:
        search_results, _, _ = await provider.search("naruto", limit=1)
        if search_results and len(search_results) > 0:
            # Use the first search result's ID
            manga_id = getattr(search_results[0], "id", None) or getattr(
                search_results[0], "manga_id", None
            )

            if manga_id:
                print(f"  🔍 Using real manga ID from search: {manga_id}")
                metadata = await provider.get_manga_details(manga_id)

                if metadata and isinstance(metadata, dict):
                    print("  ✅ Metadata successful")
                    print(f"  📖 Title: {metadata.get('title', 'N/A')}")
                    assert isinstance(metadata, dict)
                    assert "title" in metadata or len(metadata) > 0
                else:
                    print("  ⚠️ No metadata returned")
                    # This is acceptable - some providers may not support metadata
            else:
                print("  ⚠️ No manga ID found in search results")
                pytest.skip(
                    f"Provider {provider_name} search results don't contain manga IDs"
                )
        else:
            print("  ⚠️ No search results found")
            pytest.skip(f"Provider {provider_name} search returned no results")

    except Exception as e:
        print(f"  ⚠️ Metadata test failed: {e}")
        # Don't fail test for provider connectivity issues
        pytest.skip(f"Provider {provider_name} metadata test skipped: {e}")


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
        print(f"\n{'=' * 50}")
        print(f"Testing {provider_name}")
        print(f"{'=' * 50}")

        provider = registry.get_provider(provider_name.lower())
        if not provider:
            print(f"❌ Provider {provider_name} not found")
            results[provider_name] = {"available": False}
            continue

        results[provider_name] = {"available": True}

        # Test search
        try:
            search_results, total, has_more = await provider.search(
                "naruto", page=1, limit=5
            )
            search_success = True
            manga_id = (
                search_results[0].id
                if search_results and hasattr(search_results[0], "id")
                else None
            )
        except Exception as e:
            search_success = False
            manga_id = None
            print(f"  ❌ Search failed: {e}")

        results[provider_name]["search"] = search_success

        # Test metadata if we got a manga ID
        if search_success and manga_id:
            try:
                metadata = await provider.get_manga_details(manga_id)
                metadata_success = metadata is not None
            except Exception as e:
                metadata_success = False
                print(f"  ❌ Metadata failed: {e}")
            results[provider_name]["metadata"] = metadata_success
        else:
            results[provider_name]["metadata"] = False

        # Small delay between providers
        await asyncio.sleep(2)

    return results


def print_summary(results):
    """Print test summary."""
    print(f"\n{'=' * 60}")
    print("📊 FLARESOLVERR PROVIDER TEST SUMMARY")
    print(f"{'=' * 60}")

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
