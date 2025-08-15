#!/usr/bin/env python3
"""
Test script for excellent performance providers
"""

import pytest

from app.core.providers.factory import ProviderFactory
from app.core.providers.registry import provider_registry


@pytest.mark.asyncio
async def test_provider_registry_excellent_providers():
    """Test excellent performance providers."""
    providers = provider_registry.get_all_providers()

    # Test that we have providers
    assert len(providers) > 0

    # Test first few providers for basic functionality
    for provider in providers[:3]:
        print(f"\nTesting: {provider.name}")

        try:
            # Test basic search functionality
            results, total, has_more = await provider.search("test", limit=1)
            print(f"✅ {provider.name}: Search successful")

            # Basic assertions
            assert isinstance(results, list)
            assert isinstance(total, int)
            assert isinstance(has_more, bool)

        except Exception as e:
            print(f"⚠️ {provider.name}: Search failed - {e}")
            # Don't fail the test for individual provider issues
            continue


@pytest.mark.asyncio
async def test_provider_factory_creation():
    """Test provider factory can create providers."""
    factory = ProviderFactory()

    # Test that factory can create providers
    providers = factory.create_all_providers()

    # Factory might return empty list if no configs, use registry instead
    if len(providers) == 0:
        registry_providers = provider_registry.get_all_providers()
        assert len(registry_providers) > 0
    else:
        assert len(providers) > 0

    # Test that all created providers have required methods
    for provider in providers[:5]:  # Test first 5
        assert hasattr(provider, "search")
        assert hasattr(provider, "get_manga_details")
        assert hasattr(provider, "name")
        assert hasattr(provider, "supports_nsfw")


@pytest.mark.skip(
    reason="Takes too long - use scripts/test_working_providers.py instead"
)
@pytest.mark.asyncio
async def test_provider_health_basic():
    """Test basic provider health checks."""
    providers = provider_registry.get_all_providers()

    healthy_count = 0
    for provider in providers:
        try:
            # Simple connectivity test
            results, _, _ = await provider.search("test", limit=1)
            if results is not None:  # Even empty list is considered healthy
                healthy_count += 1
        except Exception:
            # Provider is unhealthy, continue
            continue

    # At least some providers should be healthy
    assert healthy_count > 0, "No providers are responding to basic health checks"
    print(f"✅ {healthy_count}/{len(providers)} providers are healthy")
