import pytest

from app.core.providers.mangaplus import MangaPlusProvider
from app.core.providers.registry import provider_registry


@pytest.mark.asyncio
async def test_provider_registry_additional_providers():
    """Test the provider registry with additional providers."""
    # Check if MangaPlus provider is registered
    assert "mangaplus" in [
        p.name.lower() for p in provider_registry.get_all_providers()
    ]

    # Check if Toonily provider is registered (active provider)
    assert "toonily" in [p.name.lower() for p in provider_registry.get_all_providers()]

    # Get MangaPlus provider
    provider = provider_registry.get_provider("mangaplus")
    assert provider is not None
    assert isinstance(provider, MangaPlusProvider)

    # Check provider properties
    assert provider.name == "MangaPlus"
    assert provider.url == "https://jumpg-api.tokyo-cdn.com/api"
    assert provider.supports_nsfw is False

    # Get Toonily provider (active provider)
    provider = provider_registry.get_provider("toonily")
    assert provider is not None
    # Toonily is an EnhancedGenericProvider

    # Check provider properties
    assert provider.name == "Toonily"
    assert provider.url == "https://toonily.com"
    assert provider.supports_nsfw is True


@pytest.mark.asyncio
async def test_mangaplus_search():
    """Test MangaPlus search - should return empty results since provider is disabled."""
    # Get MangaPlus provider
    provider = provider_registry.get_provider("mangaplus")

    # Search for manga - should return empty results due to disabled API
    results, total, has_next = await provider.search("test", page=1, limit=20)

    # Check results - provider is disabled so should return empty
    assert len(results) == 0
    assert total == 0
    assert has_next is False


@pytest.mark.asyncio
async def test_mangaplus_get_manga_details():
    """Test MangaPlus get_manga_details - should return empty dict since provider is disabled."""
    # Get MangaPlus provider
    provider = provider_registry.get_provider("mangaplus")

    # Get manga details - should return empty dict due to disabled API
    manga_details = await provider.get_manga_details("123")

    # Check manga details - provider is disabled so should return empty dict
    assert manga_details == {}
