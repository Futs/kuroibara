"""
Test suite for improved provider error handling (Issue #58).

Tests the new error classes, header methods, and error handling improvements.
"""

import pytest

from app.core.providers.base import (
    AntiBotError,
    BaseProvider,
    ContentError,
    NetworkError,
    ParsingError,
    ProviderError,
    RateLimitError,
)
from app.core.providers.mangadex import MangaDexProvider


class TestErrorClasses:
    """Test the new error classes."""

    def test_provider_error_basic(self):
        """Test basic ProviderError functionality."""
        error = ProviderError(
            message="Test error",
            provider="TestProvider",
            recoverable=True,
            context={"url": "http://test.com"},
        )

        assert error.message == "Test error"
        assert error.provider == "TestProvider"
        assert error.recoverable is True
        assert error.context == {"url": "http://test.com"}

        # Test to_dict
        error_dict = error.to_dict()
        assert error_dict["type"] == "ProviderError"
        assert error_dict["message"] == "Test error"
        assert error_dict["provider"] == "TestProvider"
        assert error_dict["recoverable"] is True
        assert error_dict["context"] == {"url": "http://test.com"}

    def test_network_error(self):
        """Test NetworkError with error_type."""
        error = NetworkError(
            message="Connection timeout",
            provider="TestProvider",
            error_type="timeout",
            context={"url": "http://test.com"},
        )

        assert error.error_type == "timeout"
        assert error.recoverable is True

        error_dict = error.to_dict()
        assert error_dict["type"] == "NetworkError"
        # NetworkError doesn't add error_type to dict, just stores it as attribute
        assert error.error_type == "timeout"

    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError(
            message="Rate limited",
            provider="TestProvider",
            retry_after=60,
        )

        assert error.retry_after == 60
        assert error.recoverable is True

        error_dict = error.to_dict()
        assert error_dict["type"] == "RateLimitError"
        assert error_dict["retry_after"] == 60
        assert "suggestion" in error_dict
        assert "60 seconds" in error_dict["suggestion"]

    def test_anti_bot_error(self):
        """Test AntiBotError with protection_type."""
        error = AntiBotError(
            message="Cloudflare detected",
            provider="TestProvider",
            protection_type="cloudflare",
        )

        assert error.protection_type == "cloudflare"
        assert error.recoverable is True

        error_dict = error.to_dict()
        assert error_dict["type"] == "AntiBotError"
        assert error_dict["protection_type"] == "cloudflare"
        assert "suggestion" in error_dict
        assert "cloudflare" in error_dict["suggestion"].lower()

    def test_parsing_error(self):
        """Test ParsingError."""
        error = ParsingError(
            message="Invalid HTML",
            provider="TestProvider",
            context={"selector": ".manga-title"},
        )

        assert error.recoverable is False
        assert error.context["selector"] == ".manga-title"

        error_dict = error.to_dict()
        assert error_dict["type"] == "ParsingError"

    def test_content_error(self):
        """Test ContentError."""
        error = ContentError(
            message="Page not found",
            provider="TestProvider",
        )

        assert error.recoverable is False

        error_dict = error.to_dict()
        assert error_dict["type"] == "ContentError"


class TestHeaderMethods:
    """Test the new header methods in BaseProvider."""

    @pytest.fixture
    def provider(self):
        """Create a MangaDex provider instance for testing."""
        return MangaDexProvider()

    def test_get_user_agent(self, provider):
        """Test get_user_agent method."""
        user_agent = provider.get_user_agent()

        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        assert "Mozilla" in user_agent

    def test_get_page_headers(self, provider):
        """Test get_page_headers method."""
        chapter_url = "https://mangadex.org/chapter/test-123"
        headers = provider.get_page_headers(chapter_url)

        assert isinstance(headers, dict)
        assert headers["Referer"] == chapter_url
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "image" in headers["Accept"]
        assert headers["Sec-Fetch-Dest"] == "image"

    def test_get_api_headers(self, provider):
        """Test get_api_headers method."""
        headers = provider.get_api_headers()

        assert isinstance(headers, dict)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "application/json" in headers["Accept"]
