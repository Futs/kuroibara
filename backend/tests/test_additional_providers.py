import pytest

from app.core.providers.registry import provider_registry


@pytest.mark.asyncio
async def test_provider_registry_additional_providers():
    """Test the provider registry with additional providers."""
    # Check if MangaDex provider is registered (main provider)
    assert "mangadex" in [p.name.lower() for p in provider_registry.get_all_providers()]

    # Check if Toonily provider is registered (active provider)
    assert "toonily" in [p.name.lower() for p in provider_registry.get_all_providers()]

    # Check if MangaDNA provider is registered (NSFW provider)
    assert "mangadna" in [p.name.lower() for p in provider_registry.get_all_providers()]

    # Get MangaDex provider
    provider = provider_registry.get_provider("MangaDex")
    assert provider is not None

    # Check provider properties
    assert provider.name == "MangaDex"
    assert provider.supports_nsfw is True

    # Get Toonily provider (active provider)
    provider = provider_registry.get_provider("Toonily")
    assert provider is not None

    # Check provider properties
    assert provider.name == "Toonily"
    assert provider.supports_nsfw is True

    # Get MangaDNA provider (NSFW provider)
    provider = provider_registry.get_provider("MangaDNA")
    assert provider is not None

    # Check provider properties
    assert provider.name == "MangaDNA"
    assert provider.supports_nsfw is True


@pytest.mark.asyncio
async def test_provider_count():
    """Test that we have providers loaded and they meet basic requirements."""
    providers = provider_registry.get_all_providers()

    # Print provider details for debugging CI issues
    print(f"\n=== Provider Count Debug ===")
    print(f"Total providers found: {len(providers)}")
    print("Provider list:")
    for i, provider in enumerate(providers, 1):
        print(f"  {i:2d}. {provider.name} (NSFW: {provider.supports_nsfw})")
    print("=" * 30)

    # Test that we have providers loaded (basic sanity check)
    assert len(providers) > 0, "No providers found - this indicates a serious configuration issue"

    # Test that we have essential working providers (these should always be present)
    provider_names = [p.name for p in providers]
    essential_providers = ["MangaDex", "MangaTown", "Toonily"]  # Core working providers we know exist

    missing_essential = [name for name in essential_providers if name not in provider_names]
    assert len(missing_essential) == 0, f"Missing essential providers: {missing_essential}"

    # Check that we have both NSFW and SFW providers
    nsfw_providers = [p for p in providers if p.supports_nsfw]
    sfw_providers = [p for p in providers if not p.supports_nsfw]

    assert len(nsfw_providers) > 0, f"Expected NSFW providers, but got {len(nsfw_providers)}"
    assert len(sfw_providers) > 0, f"Expected SFW providers, but got {len(sfw_providers)}"

    print(f"✅ Provider validation passed: {len(providers)} total, {len(nsfw_providers)} NSFW, {len(sfw_providers)} SFW")


@pytest.mark.asyncio
async def test_provider_registry_get_provider():
    """Test getting specific providers from the registry."""
    # Test getting MangaDex provider
    mangadx_provider = provider_registry.get_provider("MangaDex")
    assert mangadx_provider is not None
    assert mangadx_provider.name == "MangaDex"

    # Test getting non-existent provider
    non_existent = provider_registry.get_provider("non_existent_provider")
    assert non_existent is None


@pytest.mark.asyncio
async def test_enhanced_providers():
    """Test enhanced providers functionality."""
    # Get an enhanced provider
    provider = provider_registry.get_provider("Toonily")
    assert provider is not None

    # Test that it has the expected interface
    assert hasattr(provider, "search")
    assert hasattr(provider, "get_manga_details")
    assert hasattr(provider, "get_chapters")
    assert hasattr(provider, "get_pages")
