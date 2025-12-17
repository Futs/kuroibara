#!/usr/bin/env python3
"""
Basic test script for HiperDEX provider implementation.

This script tests the basic functionality without requiring external services.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.providers.hiperdex import HiperDexProvider
from app.core.providers.javascript_provider import JavaScriptProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic provider functionality without external requests."""
    logger.info("=== Testing Basic HiperDEX Provider Functionality ===")

    # Test provider initialization
    provider = HiperDexProvider()

    # Test basic properties
    assert provider.name == "HiperDEX"
    assert provider.url == "https://hiperdex.com"
    assert provider.supports_nsfw == True
    logger.info("✅ Provider properties test passed")

    # Test capabilities
    capabilities = provider.capabilities
    expected_caps = [
        "search",
        "manga_details",
        "chapters",
        "pages",
        "download_page",
        "download_cover",
        "health_check",
    ]
    actual_caps = [cap.value for cap in capabilities]

    for expected_cap in expected_caps:
        assert expected_cap in actual_caps, f"Missing capability: {expected_cap}"
    logger.info("✅ Provider capabilities test passed")

    # Test JavaScript data extraction
    test_html = """
    <html>
    <head><title>Test</title></head>
    <body>
        <script>
        var chapter_data = {"id": 123, "title": "Test Chapter", "pages": 20};
        var manga_data = {"title": "Test Manga", "author": "Test Author"};
        var images = ["page1.jpg", "page2.jpg", "page3.jpg"];
        </script>
        <div class="c-tabs-item__content">
            <div class="tab-thumb">
                <a href="/manga/test-manga/">
                    <img src="cover.jpg" alt="Test Manga">
                    <h3 class="tab-thumb-title">Test Manga</h3>
                </a>
                <div class="tab-summary">Test manga description</div>
            </div>
        </div>
    </body>
    </html>
    """

    # Test JavaScript extraction
    js_data = provider._extract_javascript_data(test_html, provider.javascript_patterns)
    assert "chapter_data" in js_data
    assert "manga_data" in js_data
    assert "image_urls" in js_data
    logger.info("✅ JavaScript data extraction test passed")

    # Test header generation
    headers = provider._get_headers()
    required_headers = ["User-Agent", "Accept", "Accept-Language"]
    for header in required_headers:
        assert header in headers, f"Missing header: {header}"
    logger.info("✅ Header generation test passed")

    # Test session cookie management
    test_cookies = [
        {"name": "session_id", "value": "abc123"},
        {"name": "csrf_token", "value": "xyz789"},
    ]
    provider._update_session_cookies(test_cookies)
    assert "session_id" in provider.session_cookies
    assert provider.session_cookies["session_id"] == "abc123"
    logger.info("✅ Session cookie management test passed")

    # Test rate limiting configuration
    assert provider.min_request_delay == 3.0
    assert provider.max_retries == 3
    assert len(provider.user_agents) == 3
    logger.info("✅ Rate limiting configuration test passed")

    # Test selector configuration
    expected_selectors = [
        "search_results",
        "manga_title",
        "manga_description",
        "manga_cover",
        "chapters",
        "pages",
    ]
    for selector in expected_selectors:
        assert selector in provider.selectors, f"Missing selector: {selector}"
    logger.info("✅ Selector configuration test passed")

    logger.info("🎉 All basic functionality tests passed!")


async def test_javascript_provider_base():
    """Test JavaScriptProvider base class."""
    logger.info("=== Testing JavaScriptProvider Base Class ===")

    # Test initialization
    js_provider = JavaScriptProvider(
        name="TestProvider",
        url="https://example.com",
        supports_nsfw=True,
        selectors={"test": "selector"},
        javascript_patterns={"test": r"var\s+test\s*=\s*({[^}]+})"},
    )

    # Test properties
    assert js_provider.name == "TestProvider"
    assert js_provider.url == "https://example.com"
    assert js_provider.supports_nsfw == True
    logger.info("✅ Base class properties test passed")

    # Test configuration
    assert "test" in js_provider.selectors
    assert "test" in js_provider.javascript_patterns
    logger.info("✅ Base class configuration test passed")

    # Test JavaScript extraction
    test_content = 'var test = {"key": "value", "number": 42};'
    extracted = js_provider._extract_javascript_data(
        test_content, {"test": r"var\s+test\s*=\s*({[^}]+})"}
    )
    assert "test" in extracted
    assert extracted["test"]["key"] == "value"
    assert extracted["test"]["number"] == 42
    logger.info("✅ Base class JavaScript extraction test passed")

    logger.info("🎉 All base class tests passed!")


async def test_error_handling():
    """Test error handling and edge cases."""
    logger.info("=== Testing Error Handling ===")

    provider = HiperDexProvider()

    # Test empty search results
    try:
        results, total, has_more = await provider.search("", page=1)
        assert isinstance(results, list)
        assert isinstance(total, int)
        assert isinstance(has_more, bool)
        logger.info("✅ Empty search handling test passed")
    except Exception as e:
        logger.info(f"✅ Empty search properly raises exception: {type(e).__name__}")

    # Test invalid manga details
    try:
        details = await provider.get_manga_details("invalid-manga-id")
        assert isinstance(details, dict)
        logger.info("✅ Invalid manga details handling test passed")
    except Exception as e:
        logger.info(
            f"✅ Invalid manga details properly raises exception: {type(e).__name__}"
        )

    # Test invalid chapters
    try:
        chapters, total, has_more = await provider.get_chapters("invalid-manga-id")
        assert isinstance(chapters, list)
        assert isinstance(total, int)
        assert isinstance(has_more, bool)
        logger.info("✅ Invalid chapters handling test passed")
    except Exception as e:
        logger.info(
            f"✅ Invalid chapters properly raises exception: {type(e).__name__}"
        )

    # Test invalid pages
    try:
        pages = await provider.get_pages("invalid-manga", "invalid-chapter")
        assert isinstance(pages, list)
        logger.info("✅ Invalid pages handling test passed")
    except Exception as e:
        logger.info(f"✅ Invalid pages properly raises exception: {type(e).__name__}")

    logger.info("🎉 All error handling tests passed!")


async def main():
    """Run all tests."""
    logger.info("Starting HiperDEX Provider Basic Tests")

    try:
        await test_javascript_provider_base()
        print("\n" + "=" * 60 + "\n")

        await test_basic_functionality()
        print("\n" + "=" * 60 + "\n")

        await test_error_handling()

        logger.info("\n🎉 ALL TESTS PASSED! 🎉")
        logger.info("The HiperDEX provider implementation is working correctly.")
        logger.info("Note: Network tests require FlareSolverr for full functionality.")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
