#!/usr/bin/env python3
"""
Test provider priority ordering.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.providers.registry import ProviderRegistry


def test_provider_priority():
    """Test that providers are ordered by priority."""
    print("🧪 Testing Provider Priority Ordering")
    print("=" * 60)

    # Set FlareSolverr URL to load all providers
    os.environ["FLARESOLVERR_URL"] = "http://172.16.40.12:8191"

    # Create registry
    registry = ProviderRegistry()

    # Get provider info
    providers = registry.get_provider_info()

    print(f"Total providers loaded: {len(providers)}")
    print("\nProvider Order (by priority):")
    print("-" * 60)

    for i, provider in enumerate(providers, 1):
        priority_indicator = "🥇" if provider.get("is_priority", False) else "🥈"
        priority_value = provider.get("priority", "N/A")
        nsfw_indicator = "🔞" if provider.get("supports_nsfw", False) else "👨‍👩‍👧‍👦"

        print(
            f"{i:2d}. {priority_indicator} {provider['name']:15} "
            f"(Priority: {priority_value:3}, {nsfw_indicator})"
        )

    # Verify priority ordering
    print("\n" + "=" * 60)
    print("📊 PRIORITY ANALYSIS")
    print("=" * 60)

    # Check that default providers come first
    default_providers = [p for p in providers if p.get("is_priority", False)]
    cloudflare_providers = [p for p in providers if not p.get("is_priority", False)]

    print(f"Default (Priority) Providers: {len(default_providers)}")
    for provider in default_providers:
        print(f"  ✅ {provider['name']} (Priority: {provider.get('priority', 'N/A')})")

    print(f"\nCloudflare/Optional Providers: {len(cloudflare_providers)}")
    for provider in cloudflare_providers:
        print(f"  🔓 {provider['name']} (Priority: {provider.get('priority', 'N/A')})")

    # Verify ordering is correct
    priorities = [p.get("priority", 999) for p in providers]
    is_sorted = all(
        priorities[i] <= priorities[i + 1] for i in range(len(priorities) - 1)
    )

    print(f"\n🎯 Priority Ordering: {'✅ CORRECT' if is_sorted else '❌ INCORRECT'}")

    # Check that all default providers have priority < 100
    default_priorities_correct = all(
        p.get("priority", 999) < 100 for p in default_providers
    )
    cloudflare_priorities_correct = all(
        p.get("priority", 999) >= 100 for p in cloudflare_providers
    )

    print(
        f"🥇 Default Provider Priorities: {'✅ CORRECT' if default_priorities_correct else '❌ INCORRECT'}"
    )
    print(
        f"🔓 Cloudflare Provider Priorities: {'✅ CORRECT' if cloudflare_priorities_correct else '❌ INCORRECT'}"
    )

    # Summary
    if is_sorted and default_priorities_correct and cloudflare_priorities_correct:
        print("\n🎉 Provider priority system is working correctly!")
        print("   - Default providers are listed first")
        print("   - Cloudflare providers are listed after defaults")
        print("   - All providers are sorted by priority value")
    else:
        print("\n⚠️  Provider priority system needs adjustment")

    return providers


def test_without_flaresolverr():
    """Test provider ordering without FlareSolverr."""
    print("\n" + "=" * 60)
    print("🧪 Testing Priority WITHOUT FlareSolverr")
    print("=" * 60)

    # Remove FlareSolverr URL
    if "FLARESOLVERR_URL" in os.environ:
        del os.environ["FLARESOLVERR_URL"]

    # Create registry
    registry = ProviderRegistry()

    # Get provider info
    providers = registry.get_provider_info()

    print(f"Total providers loaded: {len(providers)}")
    print("\nProvider Order (default only):")
    print("-" * 40)

    for i, provider in enumerate(providers, 1):
        priority_value = provider.get("priority", "N/A")
        nsfw_indicator = "🔞" if provider.get("supports_nsfw", False) else "👨‍👩‍👧‍👦"

        print(
            f"{i:2d}. 🥇 {provider['name']:15} "
            f"(Priority: {priority_value:3}, {nsfw_indicator})"
        )

    # Verify all are default providers
    all_default = all(p.get("is_priority", False) for p in providers)
    print(f"\n🎯 All Default Providers: {'✅ YES' if all_default else '❌ NO'}")

    return providers


def main():
    """Main test function."""
    print("🚀 Testing Provider Priority System")

    # Test with FlareSolverr (all providers)
    providers_with_flare = test_provider_priority()

    # Test without FlareSolverr (default only)
    providers_without_flare = test_without_flaresolverr()

    # Final summary
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    print(f"With FlareSolverr:    {len(providers_with_flare)} providers")
    print(f"Without FlareSolverr: {len(providers_without_flare)} providers")
    print(
        f"Difference:           +{len(providers_with_flare) - len(providers_without_flare)} Cloudflare providers"
    )

    # Expected order for first few providers
    expected_order = ["MangaDex", "MangaPlus", "MangaSee", "Toonily"]
    actual_order = [p["name"] for p in providers_with_flare[:4]]

    print(f"\nExpected top 4: {expected_order}")
    print(f"Actual top 4:   {actual_order}")
    print(f"Order correct:  {'✅ YES' if expected_order == actual_order else '❌ NO'}")


if __name__ == "__main__":
    main()
