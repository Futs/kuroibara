import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.core.providers.base import BaseProvider
from app.core.providers.factory import ProviderFactory
from app.core.providers.generic import GenericProvider
from app.core.providers.mangadex import MangaDexProvider


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def __init__(self, name="Test", url="https://test.com", supports_nsfw=False):
        self._name = name
        self._url = url
        self._supports_nsfw = supports_nsfw

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    @property
    def supports_nsfw(self) -> bool:
        return self._supports_nsfw

    async def search(self, query, page=1, limit=20):
        return [], 0, False

    async def get_manga_details(self, manga_id):
        return {}

    async def get_chapters(self, manga_id, page=1, limit=100):
        return [], 0, False

    async def get_pages(self, manga_id, chapter_id):
        return []

    async def download_page(self, page_url):
        return b""

    async def download_cover(self, manga_id):
        return b""


def test_provider_factory_register_provider_class():
    """Test registering a provider class."""
    factory = ProviderFactory()
    factory.register_provider_class(MockProvider)

    assert "MockProvider" in factory._provider_classes
    assert factory._provider_classes["MockProvider"] == MockProvider


def test_provider_factory_create_provider():
    """Test creating a provider."""
    factory = ProviderFactory()
    factory.register_provider_class(MockProvider)

    # Add provider config
    factory._provider_configs["test"] = {
        "id": "test",
        "name": "Test Provider",
        "class_name": "MockProvider",
        "url": "https://test.com",
        "supports_nsfw": False,
        "params": {
            "name": "Test Provider",
            "url": "https://test.com",
            "supports_nsfw": False,
        },
    }

    # Create provider
    provider = factory.create_provider("test")

    assert provider is not None
    assert isinstance(provider, MockProvider)
    assert provider.name == "Test Provider"
    assert provider.url == "https://test.com"
    assert provider.supports_nsfw is False


def test_provider_factory_create_all_providers():
    """Test creating all providers."""
    factory = ProviderFactory()
    factory.register_provider_class(MockProvider)

    # Add provider configs
    factory._provider_configs["test1"] = {
        "id": "test1",
        "name": "Test Provider 1",
        "class_name": "MockProvider",
        "url": "https://test1.com",
        "supports_nsfw": False,
        "params": {
            "name": "Test Provider 1",
            "url": "https://test1.com",
            "supports_nsfw": False,
        },
    }
    factory._provider_configs["test2"] = {
        "id": "test2",
        "name": "Test Provider 2",
        "class_name": "MockProvider",
        "url": "https://test2.com",
        "supports_nsfw": True,
        "params": {
            "name": "Test Provider 2",
            "url": "https://test2.com",
            "supports_nsfw": True,
        },
    }

    # Create all providers
    providers = factory.create_all_providers()

    assert len(providers) == 2
    assert all(isinstance(provider, MockProvider) for provider in providers)
    assert any(provider.name == "Test Provider 1" for provider in providers)
    assert any(provider.name == "Test Provider 2" for provider in providers)


def test_provider_factory_load_provider_configs():
    """Test loading provider configs from a file."""
    factory = ProviderFactory()
    factory.register_provider_class(MockProvider)

    # Create a temporary config file
    config = [
        {
            "id": "test1",
            "name": "Test Provider 1",
            "class_name": "MockProvider",
            "url": "https://test1.com",
            "supports_nsfw": False,
            "params": {
                "name": "Test Provider 1",
                "url": "https://test1.com",
                "supports_nsfw": False,
            },
        },
        {
            "id": "test2",
            "name": "Test Provider 2",
            "class_name": "MockProvider",
            "url": "https://test2.com",
            "supports_nsfw": True,
            "params": {
                "name": "Test Provider 2",
                "url": "https://test2.com",
                "supports_nsfw": True,
            },
        },
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as temp_file:
        json.dump(config, temp_file)
        temp_file.flush()

        # Load provider configs
        factory.load_provider_configs(temp_file.name)

    assert "test1" in factory._provider_configs
    assert "test2" in factory._provider_configs
    assert factory._provider_configs["test1"]["name"] == "Test Provider 1"
    assert factory._provider_configs["test2"]["name"] == "Test Provider 2"


def test_provider_factory_discover_provider_classes():
    """Test discovering provider classes."""
    factory = ProviderFactory()

    # Mock the Path.glob to return some mock files
    mock_files = [MagicMock(), MagicMock()]
    mock_files[0].name = "module1.py"
    mock_files[0].stem = "module1"
    mock_files[1].name = "module2.py"
    mock_files[1].stem = "module2"

    # Mock the package module (first call to import_module)
    mock_package = MagicMock()
    mock_package.__file__ = "/path/to/package/__init__.py"

    # Mock the individual module (second call to import_module)
    mock_module = MagicMock()
    mock_module.MockProvider = MockProvider

    # Mock importlib.import_module to return different objects based on call
    def mock_import_module(module_name):
        if module_name == "app.core.providers":
            return mock_package
        else:
            return mock_module

    with (
        patch("pathlib.Path.glob", return_value=mock_files),
        patch("importlib.import_module", side_effect=mock_import_module),
    ):

        # Discover provider classes
        factory.discover_provider_classes("app.core.providers")

    assert "MockProvider" in factory._provider_classes
    assert factory._provider_classes["MockProvider"] == MockProvider
