#!/usr/bin/env python3
"""
Comprehensive test suite for all Kuroibara providers
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict

import aiohttp


class ComprehensiveProviderTester:
    def __init__(self):
        self.session = None
        self.results = {
            "working": [],
            "partial": [],
            "failed": [],
            "cloudflare_blocked": [],
            "timeout": [],
            "connection_error": [],
        }

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_provider_comprehensive(self, provider_config: Dict) -> Dict:
        """Comprehensive test of a single provider."""
        provider_name = provider_config.get("name", "Unknown")
        provider_id = provider_config.get("id", "unknown")
        base_url = provider_config.get("params", {}).get("base_url", "")
        search_url = provider_config.get("params", {}).get("search_url", "")
        supports_nsfw = provider_config.get("supports_nsfw", False)
        priority = provider_config.get("priority", 999)

        result = {
            "id": provider_id,
            "name": provider_name,
            "base_url": base_url,
            "search_url": search_url,
            "supports_nsfw": supports_nsfw,
            "priority": priority,
            "status": "unknown",
            "response_time": None,
            "status_code": None,
            "accessibility_test": False,
            "search_test": False,
            "content_detection": False,
            "cloudflare_protected": False,
            "requires_js": False,
            "error_details": None,
            "test_results": {
                "homepage_load": False,
                "search_functionality": False,
                "manga_content_found": False,
                "proper_structure": False,
            },
        }

        if not base_url:
            result["status"] = "failed"
            result["error_details"] = "No base URL configured"
            return result

        try:
            # Test 1: Homepage accessibility
            print("  Testing homepage accessibility...")
            homepage_result = await self._test_homepage(base_url)
            result.update(homepage_result)

            if result["accessibility_test"]:
                # Test 2: Search functionality
                print("  Testing search functionality...")
                search_result = await self._test_search(search_url or base_url)
                result.update(search_result)

                # Test 3: Content detection
                print("  Testing content detection...")
                content_result = await self._test_content_detection(base_url)
                result.update(content_result)

            # Determine overall status
            if (
                result["accessibility_test"]
                and result["search_test"]
                and result["content_detection"]
            ):
                result["status"] = "working"
            elif result["accessibility_test"]:
                result["status"] = "partial"
            else:
                result["status"] = "failed"

        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error_details"] = "Connection timeout"
        except Exception as e:
            result["status"] = "connection_error"
            result["error_details"] = str(e)

        return result

    async def _test_homepage(self, base_url: str) -> Dict:
        """Test homepage accessibility."""
        result = {
            "accessibility_test": False,
            "response_time": None,
            "status_code": None,
            "cloudflare_protected": False,
            "requires_js": False,
        }

        start_time = time.time()

        try:
            async with self.session.get(base_url) as response:
                result["response_time"] = round((time.time() - start_time) * 1000)
                result["status_code"] = response.status

                if response.status == 200:
                    content = await response.text()

                    # Check for Cloudflare protection
                    cf_indicators = [
                        "cloudflare",
                        "cf-ray",
                        "checking your browser",
                        "ddos protection",
                    ]
                    if any(indicator in content.lower() for indicator in cf_indicators):
                        result["cloudflare_protected"] = True

                    # Check for JavaScript requirements
                    js_indicators = [
                        "please enable javascript",
                        "javascript is required",
                        "noscript",
                    ]
                    if any(indicator in content.lower() for indicator in js_indicators):
                        result["requires_js"] = True

                    result["accessibility_test"] = True
                    result["test_results"] = {"homepage_load": True}

                elif response.status == 403:
                    result["cloudflare_protected"] = True
                    result["error_details"] = "Cloudflare protection (403)"
                else:
                    result["error_details"] = f"HTTP {response.status}"

        except Exception as e:
            result["error_details"] = f"Homepage test failed: {str(e)}"

        return result

    async def _test_search(self, search_url: str) -> Dict:
        """Test search functionality."""
        result = {"search_test": False, "test_results": {"search_functionality": False}}

        if not search_url:
            return result

        try:
            # Test with a common search term
            test_query = "naruto"
            test_url = search_url.replace("{query}", test_query)

            async with self.session.get(test_url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Look for search result indicators
                    search_indicators = [
                        "result",
                        "found",
                        "search",
                        "manga",
                        "comic",
                        "chapter",
                        "title",
                        "naruto",
                        "no results",
                        "not found",
                    ]

                    if any(
                        indicator in content.lower() for indicator in search_indicators
                    ):
                        result["search_test"] = True
                        result["test_results"]["search_functionality"] = True

        except Exception as e:
            result["error_details"] = f"Search test failed: {str(e)}"

        return result

    async def _test_content_detection(self, base_url: str) -> Dict:
        """Test for manga/comic content detection."""
        result = {
            "content_detection": False,
            "test_results": {"manga_content_found": False, "proper_structure": False},
        }

        try:
            async with self.session.get(base_url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Check for manga/comic content indicators
                    content_indicators = [
                        "manga",
                        "manhwa",
                        "manhua",
                        "comic",
                        "webtoon",
                        "chapter",
                        "volume",
                        "read",
                        "latest",
                        "popular",
                        "genre",
                        "category",
                        "series",
                    ]

                    found_indicators = [
                        ind for ind in content_indicators if ind in content.lower()
                    ]

                    if len(found_indicators) >= 3:
                        result["content_detection"] = True
                        result["test_results"]["manga_content_found"] = True

                        # Check for proper structure
                        structure_indicators = ["title", "link", "href", "img", "src"]
                        if all(ind in content.lower() for ind in structure_indicators):
                            result["test_results"]["proper_structure"] = True

        except Exception as e:
            result["error_details"] = f"Content detection failed: {str(e)}"

        return result


def load_all_providers():
    """Load all provider configurations."""
    config_file = Path(
        "kuroibara/backend/app/core/providers/config/providers_default.json"
    )

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading providers: {e}")
        return []


async def main():
    """Main testing function."""
    print("=== Comprehensive Kuroibara Provider Testing ===\n")

    # Load all providers
    providers = load_all_providers()
    print(f"Testing {len(providers)} providers...\n")

    async with ComprehensiveProviderTester() as tester:
        for i, provider in enumerate(providers, 1):
            provider_name = provider.get("name", "Unknown")
            print(f"[{i:2d}/{len(providers)}] Testing {provider_name}...")

            result = await tester.test_provider_comprehensive(provider)

            # Categorize results
            if result["status"] == "working":
                tester.results["working"].append(result)
                flags = []
                if result["cloudflare_protected"]:
                    flags.append("CF")
                if result["supports_nsfw"]:
                    flags.append("NSFW")
                flag_str = f" [{'/'.join(flags)}]" if flags else ""
                print(f"  ✅ WORKING - {result['response_time']}ms{flag_str}")

            elif result["status"] == "partial":
                tester.results["partial"].append(result)
                print(
                    f"  ⚠️  PARTIAL - {result['response_time']}ms (limited functionality)"
                )

            elif result["status"] == "timeout":
                tester.results["timeout"].append(result)
                print("  ⏱️  TIMEOUT - Connection timeout")

            elif result["status"] == "connection_error":
                tester.results["connection_error"].append(result)
                print(f"  🔌 CONNECTION ERROR - {result['error_details']}")

            else:
                if result["cloudflare_protected"]:
                    tester.results["cloudflare_blocked"].append(result)
                    print(f"  🛡️  CLOUDFLARE BLOCKED - {result['error_details']}")
                else:
                    tester.results["failed"].append(result)
                    print(f"  ❌ FAILED - {result['error_details']}")

            # Be respectful with delays
            await asyncio.sleep(1)

    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 60)

    total_tested = len(providers)
    working_count = len(tester.results["working"])
    partial_count = len(tester.results["partial"])
    failed_count = len(tester.results["failed"])
    cf_blocked_count = len(tester.results["cloudflare_blocked"])
    timeout_count = len(tester.results["timeout"])
    connection_error_count = len(tester.results["connection_error"])

    print(f"Total Providers Tested: {total_tested}")
    print(
        f"✅ Fully Working: {working_count} ({working_count / total_tested * 100:.1f}%)"
    )
    print(
        f"⚠️  Partially Working: {partial_count} "
        f"({partial_count / total_tested * 100:.1f}%)"
    )
    print(f"❌ Failed: {failed_count} ({failed_count / total_tested * 100:.1f}%)")
    print(
        f"🛡️  Cloudflare Blocked: {cf_blocked_count} "
        f"({cf_blocked_count / total_tested * 100:.1f}%)"
    )
    print(f"⏱️  Timeout: {timeout_count} ({timeout_count / total_tested * 100:.1f}%)")
    print(
        f"🔌 Connection Error: {connection_error_count} "
        f"({connection_error_count / total_tested * 100:.1f}%)"
    )

    # Detailed results
    if tester.results["working"]:
        print(f"\n🎉 FULLY WORKING PROVIDERS ({len(tester.results['working'])}):")
        for result in sorted(
            tester.results["working"], key=lambda x: x["response_time"] or 9999
        ):
            flags = []
            if result["supports_nsfw"]:
                flags.append("NSFW")
            if result["cloudflare_protected"]:
                flags.append("CF")
            flag_str = f" [{'/'.join(flags)}]" if flags else ""
            print(f"  • {result['name']}{flag_str} - {result['response_time']}ms")

    if tester.results["partial"]:
        print(f"\n⚠️  PARTIALLY WORKING PROVIDERS ({len(tester.results['partial'])}):")
        for result in tester.results["partial"]:
            print(
                f"  • {result['name']} - {result['error_details'] or 'Limited functionality'}"
            )

    if tester.results["cloudflare_blocked"]:
        print(
            f"\n🛡️  CLOUDFLARE BLOCKED PROVIDERS ({len(tester.results['cloudflare_blocked'])}):"
        )
        for result in tester.results["cloudflare_blocked"]:
            print(f"  • {result['name']} - Requires FlareSolverr")

    # Save detailed results
    with open("comprehensive_provider_test_results.json", "w") as f:
        json.dump(tester.results, f, indent=2)

    print("\n📊 Detailed results saved to comprehensive_provider_test_results.json")

    return tester.results


if __name__ == "__main__":
    asyncio.run(main())
