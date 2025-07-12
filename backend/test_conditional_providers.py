#!/usr/bin/env python3
"""
Test conditional provider loading based on FlareSolverr availability.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.providers.registry import ProviderRegistry


def test_without_flaresolverr():
    """Test provider loading without FlareSolverr."""
    print("=" * 60)
    print("Testing WITHOUT FlareSolverr")
    print("=" * 60)

    # Ensure FlareSolverr is not set
    if "FLARESOLVERR_URL" in os.environ:
        del os.environ["FLARESOLVERR_URL"]

    # Create registry
    registry = ProviderRegistry()

    # Get provider info
    providers = registry.get_provider_info()

    print(f"Total providers loaded: {len(providers)}")
    print("\nProviders:")
    for provider in providers:
        print(f"  - {provider['name']} ({provider['id']})")

    # Check for Cloudflare providers
    cloudflare_providers = [
        p for p in providers if p["name"] in ["ReaperScans", "Manhuaga", "MangaFire"]
    ]
    print(f"\nCloudflare providers found: {len(cloudflare_providers)}")
    for provider in cloudflare_providers:
        print(f"  - {provider['name']}")

    return len(providers), len(cloudflare_providers)


def test_with_flaresolverr():
    """Test provider loading with FlareSolverr."""
    print("\n" + "=" * 60)
    print("Testing WITH FlareSolverr")
    print("=" * 60)

    # Set FlareSolverr URL
    os.environ["FLARESOLVERR_URL"] = "http://172.16.40.12:8191"

    # Create registry
    registry = ProviderRegistry()

    # Get provider info
    providers = registry.get_provider_info()

    print(f"Total providers loaded: {len(providers)}")
    print("\nProviders:")
    for provider in providers:
        print(f"  - {provider['name']} ({provider['id']})")

    # Check for Cloudflare providers
    cloudflare_providers = [
        p for p in providers if p["name"] in ["ReaperScans", "Manhuaga", "MangaFire"]
    ]
    print(f"\nCloudflare providers found: {len(cloudflare_providers)}")
    for provider in cloudflare_providers:
        print(f"  - {provider['name']}")

    return len(providers), len(cloudflare_providers)


def main():
    """Main test function."""
    print("🧪 Testing Conditional Provider Loading")

    # Test without FlareSolverr
    total_without, cloudflare_without = test_without_flaresolverr()

    # Test with FlareSolverr
    total_with, cloudflare_with = test_with_flaresolverr()

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(
        f"Without FlareSolverr: {total_without} total, {cloudflare_without} Cloudflare"
    )
    print(f"With FlareSolverr:    {total_with} total, {cloudflare_with} Cloudflare")
    print(
        f"Difference:           +{total_with - total_without} total, +{cloudflare_with - cloudflare_without} Cloudflare"
    )

    # Validation
    if cloudflare_without == 0 and cloudflare_with > 0:
        print("✅ Conditional loading working correctly!")
    else:
        print("❌ Conditional loading may not be working as expected")

    if total_with > total_without:
        print("✅ More providers available with FlareSolverr")
    else:
        print("⚠️  Same number of providers with/without FlareSolverr")


if __name__ == "__main__":
    main()
