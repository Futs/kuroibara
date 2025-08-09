#!/usr/bin/env python3
"""
Quick test script for excellent performance providers
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.providers.factory import ProviderFactory
from app.core.providers.generic import GenericProvider


async def test_provider(provider_config, factory):
    """Test a single provider configuration."""
    print(f"\n{'=' * 50}")
    print(f"Testing: {provider_config['name']}")
    print(f"URL: {provider_config['url']}")
    print(f"{'=' * 50}")

    try:
        # Create provider instance using provider ID
        provider_id = provider_config["id"]
        provider = factory.create_provider(provider_id)

        # Test basic connectivity by trying a simple search
        print("Testing basic connectivity...")
        try:
            # Try a simple search to test connectivity
            results, total, has_more = await provider.search("test", limit=1)
            print("✅ Connection successful")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

        # Test search functionality with a popular manga
        print("Testing search functionality...")
        try:
            results, total, has_more = await provider.search("naruto", limit=3)
            if results and len(results) > 0:
                print(f"✅ Search successful - found {len(results)} results")

                # Show first result
                first_result = results[0]
                print(
                    f"   First result: {first_result.title if hasattr(first_result, 'title') else 'No title'}"
                )
                print(
                    f"   URL: {first_result.url if hasattr(first_result, 'url') else 'No URL'}"
                )

                # Test manga details if we have a URL
                if hasattr(first_result, "url") and first_result.url:
                    print("Testing manga details...")
                    try:
                        manga_id = first_result.url.split("/")[-1]
                        details = await provider.get_manga_details(manga_id)
                        if details:
                            print("✅ Manga details successful")
                            print(f"   Title: {details.get('title', 'No title')}")
                            print(f"   Chapters: {len(details.get('chapters', []))}")
                        else:
                            print("⚠️  Manga details returned empty")
                    except Exception as e:
                        print(f"❌ Manga details failed: {e}")

            else:
                print("⚠️  Search returned no results")
                return False

        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False

        print("✅ Provider test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Provider creation failed: {e}")
        return False


async def main():
    """Main test function."""
    config_file = "app/core/providers/config/providers_excellent_performance.json"

    if not os.path.exists(config_file):
        print(f"Config file not found: {config_file}")
        return

    # Load provider configurations
    with open(config_file, "r") as f:
        providers = json.load(f)

    print(f"Testing {len(providers)} excellent performance providers...")

    # Create factory and load configs
    factory = ProviderFactory()
    factory.register_provider_class(GenericProvider)
    factory.load_provider_configs(config_file)

    results = {}

    for provider_config in providers:
        provider_name = provider_config["name"]
        success = await test_provider(provider_config, factory)
        results[provider_name] = success

    # Summary
    print(f"\n{'=' * 60}")
    print("EXCELLENT PERFORMANCE PROVIDERS TEST SUMMARY")
    print(f"{'=' * 60}")

    successful = sum(1 for success in results.values() if success)
    total = len(results)

    print(f"Total providers tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {successful / total * 100:.1f}%")

    print("\nDetailed results:")
    for provider_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {provider_name}: {status}")

    if successful > 0:
        print(f"\n🎉 {successful} excellent performance providers are ready to use!")
    else:
        print("\n⚠️  No providers passed all tests. Configuration may need adjustment.")


if __name__ == "__main__":
    asyncio.run(main())
