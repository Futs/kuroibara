#!/usr/bin/env python3
"""
Comprehensive provider testing script.
Tests all providers for URL accessibility, search functionality, metadata extraction, and image retrieval.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.providers.factory import ProviderFactory
from app.core.providers.generic import GenericProvider
from app.core.providers.mangadex import MangaDexProvider
from app.core.providers.mangaplus import MangaPlusProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ProviderTester:
    """Comprehensive provider testing class."""

    def __init__(self):
        self.results = {}
        self.factory = ProviderFactory()
        self.timeout = 30.0

        # Register provider classes
        self.factory.register_provider_class(MangaDexProvider)
        self.factory.register_provider_class(MangaPlusProvider)
        self.factory.register_provider_class(GenericProvider)

    async def test_url_accessibility(
        self, url: str, provider_name: str
    ) -> Dict[str, Any]:
        """Test if a URL is accessible."""
        result = {
            "accessible": False,
            "status_code": None,
            "response_time": None,
            "error": None,
            "content_type": None,
            "redirected_url": None,
        }

        try:
            start_time = time.time()
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                end_time = time.time()

                result["accessible"] = True
                result["status_code"] = response.status_code
                result["response_time"] = round(end_time - start_time, 2)
                result["content_type"] = response.headers.get("content-type", "")
                result["redirected_url"] = (
                    str(response.url) if str(response.url) != url else None
                )

                # Check if it's a valid response
                if response.status_code >= 400:
                    result["accessible"] = False
                    result["error"] = f"HTTP {response.status_code}"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing URL {url} for {provider_name}: {e}")

        return result

    async def test_provider_search(
        self, provider, test_query: str = "naruto"
    ) -> Dict[str, Any]:
        """Test provider search functionality."""
        result = {
            "search_works": False,
            "results_count": 0,
            "has_results": False,
            "error": None,
            "sample_result": None,
        }

        try:
            search_results, total, has_more = await provider.search(
                test_query, page=1, limit=5
            )

            result["search_works"] = True
            result["results_count"] = len(search_results)
            result["has_results"] = len(search_results) > 0
            result["total_available"] = total
            result["has_more_pages"] = has_more

            if search_results:
                # Get sample result details
                sample = search_results[0]
                result["sample_result"] = {
                    "id": getattr(sample, "id", None),
                    "title": getattr(sample, "title", None),
                    "cover_image": getattr(sample, "cover_image", None),
                    "description": getattr(sample, "description", None),
                }

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing search for {provider.name}: {e}")

        return result

    async def test_provider_metadata(
        self, provider, manga_id: str = None
    ) -> Dict[str, Any]:
        """Test provider metadata extraction."""
        result = {
            "metadata_works": False,
            "has_title": False,
            "has_description": False,
            "has_cover": False,
            "has_genres": False,
            "error": None,
            "metadata_sample": None,
        }

        if not manga_id:
            # Try to get a manga ID from search first
            try:
                search_results, _, _ = await provider.search("test", page=1, limit=1)
                if search_results:
                    # Handle both SearchResult objects and dictionaries
                    first_result = search_results[0]
                    if hasattr(first_result, "id"):
                        manga_id = first_result.id
                    elif isinstance(first_result, dict):
                        manga_id = first_result.get("id")
                    else:
                        # Try to extract from string representation or other formats
                        manga_id = str(first_result)[:50]  # Fallback
            except Exception as e:
                logger.warning(
                    f"Error getting manga ID from search for {provider.name}: {e}"
                )

        if not manga_id:
            result["error"] = "No manga ID available for testing"
            return result

        try:
            metadata = await provider.get_manga_details(manga_id)

            if metadata and isinstance(metadata, dict):
                result["metadata_works"] = True
                result["has_title"] = bool(metadata.get("title"))
                result["has_description"] = bool(metadata.get("description"))
                result["has_cover"] = bool(metadata.get("cover_image"))
                result["has_genres"] = bool(metadata.get("genres"))

                result["metadata_sample"] = {
                    "title": str(metadata.get("title", ""))[:100],
                    "description": str(metadata.get("description", ""))[:200],
                    "cover_image": str(metadata.get("cover_image", "")),
                    "genres": (
                        metadata.get("genres", [])[:5]
                        if isinstance(metadata.get("genres"), list)
                        else []
                    ),
                }

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing metadata for {provider.name}: {e}")

        return result

    async def test_image_accessibility(
        self, image_url: str, provider_name: str
    ) -> Dict[str, Any]:
        """Test if an image URL is accessible."""
        result = {
            "accessible": False,
            "status_code": None,
            "content_type": None,
            "content_length": None,
            "error": None,
        }

        if not image_url:
            result["error"] = "No image URL provided"
            return result

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": urlparse(image_url).netloc,
                }
                response = await client.head(image_url, headers=headers)

                result["accessible"] = response.status_code == 200
                result["status_code"] = response.status_code
                result["content_type"] = response.headers.get("content-type", "")
                result["content_length"] = response.headers.get("content-length")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing image {image_url} for {provider_name}: {e}")

        return result

    async def test_provider_comprehensive(
        self, provider_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive test of a single provider."""
        provider_id = provider_config.get("id", "unknown")
        provider_name = provider_config.get("name", "Unknown")

        logger.info(f"Testing provider: {provider_name} ({provider_id})")

        result = {
            "provider_id": provider_id,
            "provider_name": provider_name,
            "provider_url": provider_config.get("url", ""),
            "class_name": provider_config.get("class_name", ""),
            "supports_nsfw": provider_config.get("supports_nsfw", False),
            "timestamp": time.time(),
            "url_test": {},
            "search_test": {},
            "metadata_test": {},
            "cover_image_test": {},
            "overall_status": "unknown",
        }

        # Test URL accessibility
        base_url = provider_config.get("url", "")
        if base_url:
            result["url_test"] = await self.test_url_accessibility(
                base_url, provider_name
            )

        # Create provider instance for functional testing
        provider = None
        try:
            # Add config to factory
            self.factory._provider_configs[provider_id] = provider_config
            provider = self.factory.create_provider(provider_id)
        except Exception as e:
            result["provider_creation_error"] = str(e)
            logger.error(f"Failed to create provider {provider_name}: {e}")

        if provider:
            # Test search functionality
            result["search_test"] = await self.test_provider_search(provider)

            # Test metadata extraction
            result["metadata_test"] = await self.test_provider_metadata(provider)

            # Test cover image if available
            if result["metadata_test"].get("metadata_sample", {}).get("cover_image"):
                cover_url = result["metadata_test"]["metadata_sample"]["cover_image"]
                result["cover_image_test"] = await self.test_image_accessibility(
                    cover_url, provider_name
                )

        # Determine overall status
        url_ok = result["url_test"].get("accessible", False)
        search_ok = result["search_test"].get("search_works", False)

        if url_ok and search_ok:
            result["overall_status"] = "working"
        elif url_ok:
            result["overall_status"] = "partial"
        else:
            result["overall_status"] = "broken"

        return result

    async def load_and_test_config_file(self, config_file: str) -> List[Dict[str, Any]]:
        """Load and test all providers from a config file."""
        config_path = Path(f"app/core/providers/config/{config_file}")

        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return []

        try:
            with open(config_path, "r") as f:
                providers = json.load(f)

            logger.info(f"Testing {len(providers)} providers from {config_file}")

            results = []
            for i, provider_config in enumerate(providers):
                try:
                    logger.info(
                        f"Testing provider {i + 1}/{len(providers)}: {provider_config.get('name', 'Unknown')}"
                    )
                    result = await self.test_provider_comprehensive(provider_config)
                    results.append(result)

                    # Small delay between tests to be respectful
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(
                        f"Error testing provider {provider_config.get('name', 'Unknown')}: {e}"
                    )
                    # Create a basic error result
                    error_result = {
                        "provider_id": provider_config.get("id", "unknown"),
                        "provider_name": provider_config.get("name", "Unknown"),
                        "provider_url": provider_config.get("url", ""),
                        "overall_status": "error",
                        "error": str(e),
                    }
                    results.append(error_result)

            return results

        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
            return []

    async def test_all_providers(self) -> Dict[str, Any]:
        """Test all providers from all config files."""
        config_files = [
            "providers_batch1.json",
            "providers_batch2.json",
            "providers_batch3.json",
            "providers_batch4.json",
        ]

        all_results = []
        summary = {
            "total_providers": 0,
            "working_providers": 0,
            "partial_providers": 0,
            "broken_providers": 0,
            "test_timestamp": time.time(),
        }

        for config_file in config_files:
            logger.info(f"Processing {config_file}")
            results = await self.load_and_test_config_file(config_file)
            all_results.extend(results)

        # Calculate summary statistics
        summary["total_providers"] = len(all_results)
        for result in all_results:
            status = result.get("overall_status", "unknown")
            if status == "working":
                summary["working_providers"] += 1
            elif status == "partial":
                summary["partial_providers"] += 1
            elif status == "broken":
                summary["broken_providers"] += 1

        return {"summary": summary, "detailed_results": all_results}

    def save_results(
        self, results: Dict[str, Any], filename: str = "provider_test_results.json"
    ):
        """Save test results to a JSON file."""
        try:
            with open(filename, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")


async def main():
    """Main function to run all provider tests."""
    logger.info("Starting comprehensive provider testing...")

    tester = ProviderTester()
    results = await tester.test_all_providers()

    # Save results
    tester.save_results(results)

    # Print summary
    summary = results["summary"]
    logger.info("=" * 60)
    logger.info("PROVIDER TESTING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total providers tested: {summary['total_providers']}")
    logger.info(f"Working providers: {summary['working_providers']}")
    logger.info(f"Partially working: {summary['partial_providers']}")
    logger.info(f"Broken providers: {summary['broken_providers']}")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(main())
