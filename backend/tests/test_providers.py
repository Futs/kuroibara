import pytest
import httpx
from unittest.mock import patch, MagicMock

from app.core.providers.registry import provider_registry
from app.core.providers.mangadex import MangaDexProvider


@pytest.mark.asyncio
async def test_provider_registry():
    """Test the provider registry."""
    # Check if MangaDex provider is registered
    assert "mangadex" in [p.name.lower() for p in provider_registry.get_all_providers()]
    
    # Get MangaDex provider
    provider = provider_registry.get_provider("mangadex")
    assert provider is not None
    assert isinstance(provider, MangaDexProvider)
    
    # Check provider properties
    assert provider.name == "MangaDex"
    assert provider.url == "https://api.mangadex.org"
    assert provider.supports_nsfw is True


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_mangadex_search(mock_get):
    """Test MangaDex search."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": "test-manga-id",
                "attributes": {
                    "title": {"en": "Test Manga"},
                    "description": {"en": "Test description"},
                    "year": 2020,
                    "contentRating": "safe",
                    "status": "ongoing",
                    "tags": [
                        {
                            "type": "genre",
                            "attributes": {"name": {"en": "Action"}},
                        }
                    ],
                },
                "relationships": [
                    {
                        "type": "cover_art",
                        "attributes": {"fileName": "cover.jpg"},
                    },
                    {
                        "type": "author",
                        "attributes": {"name": "Test Author"},
                    },
                ],
            }
        ],
        "total": 1,
    }
    mock_get.return_value = mock_response
    
    # Get MangaDex provider
    provider = provider_registry.get_provider("mangadex")
    
    # Search for manga
    results, total, has_next = await provider.search("test", page=1, limit=20)
    
    # Check results
    assert len(results) == 1
    assert total == 1
    assert has_next is False
    
    # Check first result
    result = results[0]
    assert result.id == "test-manga-id"
    assert result.title == "Test Manga"
    assert result.description == "Test description"
    assert result.year == 2020
    assert result.is_nsfw is False
    assert result.type == "manga"
    assert result.status == "ongoing"
    assert result.genres == ["Action"]
    assert result.authors == ["Test Author"]
    assert result.provider == "MangaDex"
    assert result.url == "https://mangadex.org/title/test-manga-id"
    assert result.cover_image == "https://uploads.mangadex.org/covers/test-manga-id/cover.jpg"
