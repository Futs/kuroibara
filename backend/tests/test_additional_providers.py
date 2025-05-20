import pytest
import httpx
from unittest.mock import patch, MagicMock

from app.core.providers.registry import provider_registry
from app.core.providers.mangaplus import MangaPlusProvider
from app.core.providers.mangasee import MangaSeeProvider


@pytest.mark.asyncio
async def test_provider_registry_additional_providers():
    """Test the provider registry with additional providers."""
    # Check if MangaPlus provider is registered
    assert "mangaplus" in [p.name.lower() for p in provider_registry.get_all_providers()]
    
    # Check if MangaSee provider is registered
    assert "mangasee" in [p.name.lower() for p in provider_registry.get_all_providers()]
    
    # Get MangaPlus provider
    provider = provider_registry.get_provider("mangaplus")
    assert provider is not None
    assert isinstance(provider, MangaPlusProvider)
    
    # Check provider properties
    assert provider.name == "MangaPlus"
    assert provider.url == "https://jumpg-webapi.tokyo-cdn.com/api"
    assert provider.supports_nsfw is False
    
    # Get MangaSee provider
    provider = provider_registry.get_provider("mangasee")
    assert provider is not None
    assert isinstance(provider, MangaSeeProvider)
    
    # Check provider properties
    assert provider.name == "MangaSee"
    assert provider.url == "https://mangasee123.com"
    assert provider.supports_nsfw is True


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_mangaplus_search(mock_get):
    """Test MangaPlus search."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "titleGroups": [
            {
                "titles": [
                    {
                        "titleId": 123,
                        "name": "Test Manga",
                        "author": "Test Author",
                        "portraitImageUrl": "https://example.com/cover.jpg",
                        "overview": "Test description",
                        "isCompleted": False,
                    }
                ]
            }
        ]
    }
    mock_get.return_value = mock_response
    
    # Get MangaPlus provider
    provider = provider_registry.get_provider("mangaplus")
    
    # Search for manga
    results, total, has_next = await provider.search("test", page=1, limit=20)
    
    # Check results
    assert len(results) == 1
    assert total == 1
    assert has_next is False
    
    # Check first result
    result = results[0]
    assert result.id == "123"
    assert result.title == "Test Manga"
    assert result.description == "Test description"
    assert result.is_nsfw is False
    assert result.type == "manga"
    assert result.status == "ongoing"
    assert result.authors == ["Test Author"]
    assert result.provider == "MangaPlus"
    assert result.url == "https://mangaplus.shueisha.co.jp/titles/123"
    assert result.cover_image == "https://example.com/cover.jpg"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
@patch("app.core.providers.mangasee.MangaSeeProvider._get_all_manga")
async def test_mangasee_search(mock_get_all_manga, mock_get):
    """Test MangaSee search."""
    # Mock _get_all_manga
    mock_get_all_manga.return_value = [
        {
            "i": "test-manga-id",
            "s": "Test Manga",
            "al": "Alternative Title",
            "t": "Manga",
            "ss": "Ongoing",
            "g": ["Action", "Adventure"],
        }
    ]
    
    # Get MangaSee provider
    provider = provider_registry.get_provider("mangasee")
    
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
    assert result.alternative_titles == {"alternative": "Alternative Title"}
    assert result.is_nsfw is False
    assert result.type == "manga"
    assert result.status == "ongoing"
    assert result.genres == ["Action", "Adventure"]
    assert result.provider == "MangaSee"
    assert result.url == "https://mangasee123.com/manga/test-manga-id"
    assert result.cover_image == "https://temp.compsci88.com/cover/test-manga-id.jpg"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_mangaplus_get_manga_details(mock_get):
    """Test MangaPlus get_manga_details."""
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "success": True,
        "titleDetail": {
            "title": {
                "titleId": 123,
                "name": "Test Manga",
                "author": "Test Author",
                "portraitImageUrl": "https://example.com/cover.jpg",
                "overview": "Test description",
                "isCompleted": False,
            }
        }
    }
    mock_get.return_value = mock_response
    
    # Get MangaPlus provider
    provider = provider_registry.get_provider("mangaplus")
    
    # Get manga details
    manga_details = await provider.get_manga_details("123")
    
    # Check manga details
    assert manga_details["id"] == "123"
    assert manga_details["title"] == "Test Manga"
    assert manga_details["description"] == "Test description"
    assert manga_details["is_nsfw"] is False
    assert manga_details["type"] == "manga"
    assert manga_details["status"] == "ongoing"
    assert manga_details["authors"] == ["Test Author"]
    assert manga_details["provider"] == "MangaPlus"
    assert manga_details["url"] == "https://mangaplus.shueisha.co.jp/titles/123"
    assert manga_details["cover_image"] == "https://example.com/cover.jpg"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
@patch("re.search")
async def test_mangasee_get_manga_details(mock_re_search, mock_get):
    """Test MangaSee get_manga_details."""
    # Mock re.search
    mock_match = MagicMock()
    mock_match.group.return_value = '{"SeriesName":"Test Manga","AlternativeNames":"Alternative Title","Description":"Test description","Author":"Test Author","Genres":["Action","Adventure"],"Type":"Manga","Status":"Ongoing","YearOfRelease":"2023"}'
    mock_re_search.return_value = mock_match
    
    # Mock response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.text = "vm.SeriesJSON = {};"
    mock_get.return_value = mock_response
    
    # Get MangaSee provider
    provider = provider_registry.get_provider("mangasee")
    
    # Get manga details
    manga_details = await provider.get_manga_details("test-manga-id")
    
    # Check manga details
    assert manga_details["id"] == "test-manga-id"
    assert manga_details["title"] == "Test Manga"
    assert manga_details["alternative_titles"] == {"alternative": "Alternative Title"}
    assert manga_details["description"] == "Test description"
    assert manga_details["is_nsfw"] is False
    assert manga_details["type"] == "manga"
    assert manga_details["status"] == "ongoing"
    assert manga_details["year"] == 2023
    assert manga_details["genres"] == ["Action", "Adventure"]
    assert manga_details["authors"] == ["Test Author"]
    assert manga_details["provider"] == "MangaSee"
    assert manga_details["url"] == "https://mangasee123.com/manga/test-manga-id"
    assert manga_details["cover_image"] == "https://temp.compsci88.com/cover/test-manga-id.jpg"
