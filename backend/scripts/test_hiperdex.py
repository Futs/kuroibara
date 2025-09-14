#!/usr/bin/env python3
"""
Test script for HiperDEX provider implementation.

This script tests the new JavaScriptProvider base class and HiperDexProvider
to ensure they work correctly with the Kuroibara system.
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_hiperdex_provider():
    """Test HiperDEX provider functionality."""
    logger.info("=== Testing HiperDEX Provider ===")
    
    # Initialize provider
    provider = HiperDexProvider()
    logger.info(f"Provider initialized: {provider.name}")
    logger.info(f"Base URL: {provider.url}")
    logger.info(f"Supports NSFW: {provider.supports_nsfw}")
    logger.info(f"Capabilities: {[cap.value for cap in provider.capabilities]}")
    
    # Test health check
    logger.info("\n--- Testing Health Check ---")
    try:
        is_healthy, response_time, error = await provider.health_check(timeout=30)
        logger.info(f"Health check result: {is_healthy}")
        logger.info(f"Response time: {response_time}ms")
        if error:
            logger.warning(f"Health check error: {error}")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    # Test search functionality
    logger.info("\n--- Testing Search ---")
    try:
        search_results, total, has_more = await provider.search("Stupidemic", page=1)
        logger.info(f"Search returned {len(search_results)} results (total: {total}, has_more: {has_more})")

        for i, result in enumerate(search_results[:3]):  # Show first 3 results
            logger.info(f"Result {i+1}:")
            logger.info(f"  Title: {result.get('title', 'N/A')}")
            logger.info(f"  URL: {result.get('url', 'N/A')}")
            logger.info(f"  NSFW: {result.get('nsfw', 'N/A')}")
            logger.info(f"  Description: {result.get('description', 'N/A')[:100]}...")

    except Exception as e:
        logger.error(f"Search test failed: {e}")
    
    # Test manga details (if we found results)
    if 'search_results' in locals() and search_results:
        logger.info("\n--- Testing Manga Details ---")
        try:
            first_manga = search_results[0]
            manga_url = first_manga.get('url')
            
            if manga_url:
                logger.info(f"Getting details for: {manga_url}")
                details = await provider.get_manga_details(manga_url)
                
                if details:
                    logger.info("Manga details retrieved successfully:")
                    logger.info(f"  Title: {details.get('title', 'N/A')}")
                    logger.info(f"  Status: {details.get('status', 'N/A')}")
                    logger.info(f"  Author: {details.get('author', 'N/A')}")
                    logger.info(f"  Genres: {details.get('genres', [])}")
                    logger.info(f"  Rating: {details.get('rating', 'N/A')}")
                    logger.info(f"  Cover URL: {details.get('cover_url', 'N/A')}")
                else:
                    logger.warning("No manga details retrieved")
                    
        except Exception as e:
            logger.error(f"Manga details test failed: {e}")
    
    # Test chapter list (if we have manga details)
    if 'details' in locals() and details:
        logger.info("\n--- Testing Chapter List ---")
        try:
            manga_url = details.get('url')
            if manga_url:
                chapters, total_chapters, has_more = await provider.get_chapters(manga_url)
                logger.info(f"Found {len(chapters)} chapters (total: {total_chapters}, has_more: {has_more})")
                
                for i, chapter in enumerate(chapters[:5]):  # Show first 5 chapters
                    logger.info(f"Chapter {i+1}:")
                    logger.info(f"  Title: {chapter.get('title', 'N/A')}")
                    logger.info(f"  Number: {chapter.get('chapter_number', 'N/A')}")
                    logger.info(f"  URL: {chapter.get('url', 'N/A')}")
                    logger.info(f"  Upload Date: {chapter.get('upload_date', 'N/A')}")
                    
        except Exception as e:
            logger.error(f"Chapter list test failed: {e}")
    
    # Test page extraction (if we have chapters)
    if 'chapters' in locals() and chapters:
        logger.info("\n--- Testing Page Extraction ---")
        try:
            first_chapter = chapters[0]
            chapter_url = first_chapter.get('url')
            
            if chapter_url:
                logger.info(f"Getting pages for: {chapter_url}")
                pages = await provider.get_pages("", chapter_url)  # manga_id not needed for HiperDEX
                logger.info(f"Found {len(pages)} pages")
                
                for i, page_url in enumerate(pages[:3]):  # Show first 3 pages
                    logger.info(f"Page {i+1}: {page_url}")
                    
        except Exception as e:
            logger.error(f"Page extraction test failed: {e}")
    
    logger.info("\n=== HiperDEX Provider Test Complete ===")


async def test_javascript_provider_base():
    """Test JavaScriptProvider base class functionality."""
    logger.info("=== Testing JavaScriptProvider Base Class ===")
    
    try:
        # Test basic initialization
        js_provider = JavaScriptProvider(
            name="TestJS",
            url="https://example.com",
            supports_nsfw=True
        )
        
        logger.info(f"JavaScriptProvider initialized: {js_provider.name}")
        logger.info(f"Capabilities: {[cap.value for cap in js_provider.capabilities]}")
        logger.info(f"Rate limiting delay: {js_provider.min_request_delay}s")
        logger.info(f"Max retries: {js_provider.max_retries}")
        logger.info(f"User agents available: {len(js_provider.user_agents)}")
        
        # Test header generation
        headers = js_provider._get_headers()
        logger.info(f"Generated headers: {list(headers.keys())}")
        
        # Test JavaScript data extraction
        test_content = '''
        <html>
        <script>
        var chapter_data = {"id": 123, "title": "Test Chapter"};
        var images = ["image1.jpg", "image2.jpg"];
        </script>
        </html>
        '''
        
        patterns = {
            'chapter_data': r'var\s+chapter_data\s*=\s*({[^}]+})',
            'images': r'var\s+images\s*=\s*(\[[^\]]+\])'
        }
        
        extracted = js_provider._extract_javascript_data(test_content, patterns)
        logger.info(f"JavaScript extraction test: {extracted}")
        
    except Exception as e:
        logger.error(f"JavaScriptProvider base test failed: {e}")
    
    logger.info("=== JavaScriptProvider Base Class Test Complete ===")


async def main():
    """Run all tests."""
    logger.info("Starting HiperDEX Provider Tests")
    
    # Test base class first
    await test_javascript_provider_base()
    
    print("\n" + "="*60 + "\n")
    
    # Test HiperDEX implementation
    await test_hiperdex_provider()
    
    logger.info("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
