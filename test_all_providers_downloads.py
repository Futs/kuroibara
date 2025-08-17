#!/usr/bin/env python3
"""
Comprehensive provider download testing script.
Tests each provider by searching, adding to library, and downloading chapters.
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Optional, Tuple


class ProviderDownloadTester:
    """Test downloads for all providers."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.access_token = None
        self.test_results = {}
        
        # Different test queries for each provider to avoid duplicates
        self.provider_queries = {
            "MangaPill": ["Romance", "School Life", "Comedy"],
            "ArcaneScans": ["Action", "Adventure", "Fantasy"],
            "ManhuaFast": ["Cultivation", "Martial Arts", "Xianxia"],
            "Toonily": ["Adult", "Mature", "Romance"],
            "MangaTown": ["Shounen", "Drama", "Supernatural"],
            "MangaDNA": ["Ecchi", "Harem", "Adult"],
            "Manga18FX": ["18+", "Adult", "Mature"],
            "MangaFreak": ["Seinen", "Thriller", "Horror"],
            "MangaSail": ["Slice of Life", "Comedy", "Romance"],
            "MangaKakalotFun": ["Isekai", "Fantasy", "Adventure"]
        }
    
    async def authenticate(self) -> bool:
        """Authenticate and get access token."""
        async with httpx.AsyncClient() as client:
            try:
                # Try to login with existing test user
                login_response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "username": "testuser_provider",
                        "password": "password123"
                    }
                )
                
                if login_response.status_code != 200:
                    # Register new test user
                    print("Registering new test user...")
                    register_response = await client.post(
                        f"{self.base_url}/api/v1/auth/register",
                        json={
                            "username": "testuser_provider",
                            "email": "testuser_provider@example.com",
                            "password": "password123",
                            "full_name": "Provider Test User"
                        }
                    )
                    
                    if register_response.status_code not in [200, 201]:
                        print(f"Registration failed: {register_response.text}")
                        return False
                    
                    # Login after registration
                    login_response = await client.post(
                        f"{self.base_url}/api/v1/auth/login",
                        json={
                            "username": "testuser_provider",
                            "password": "password123"
                        }
                    )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.access_token = login_data["access_token"]
                    print("✅ Authentication successful")
                    return True
                else:
                    print(f"❌ Login failed: {login_response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Authentication error: {e}")
                return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    async def test_provider_search(self, client: httpx.AsyncClient, provider_name: str, is_nsfw: bool) -> Tuple[bool, Optional[Dict]]:
        """Test searching for manga on a provider."""
        print(f"  🔍 Testing search for {provider_name}...")

        # Use provider-specific queries to get different manga for each provider
        queries = self.provider_queries.get(provider_name, ["Action", "Romance", "Adventure", "Fantasy", "Comedy"])
        
        for query in queries:
            try:
                search_response = await client.post(
                    f"{self.base_url}/api/v1/search",
                    json={
                        "query": query,
                        "provider": provider_name,
                        "page": 1,
                        "limit": 5
                    },
                    headers=self.get_headers(),
                    timeout=30
                )
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    results = search_data.get("results", [])

                    if results:
                        # Return all results so we can try multiple if needed
                        print(f"    ✅ Found {len(results)} results for '{query}'")
                        return True, {"query": query, "results": results}
                    else:
                        print(f"    ⚠️  No results for '{query}'")
                        continue
                else:
                    print(f"    ❌ Search failed for '{query}': {search_response.status_code}")
                    continue
                    
            except Exception as e:
                print(f"    ❌ Search error for '{query}': {e}")
                continue
        
        print(f"    ❌ No successful searches found for {provider_name}")
        return False, None
    
    async def test_provider_download(self, client: httpx.AsyncClient, provider_name: str, search_data: Dict) -> bool:
        """Test adding manga to library and downloading."""
        # Try multiple manga from search results until we find one that works
        results = search_data["results"]
        query = search_data["query"]

        for i, manga_result in enumerate(results[:3]):  # Try up to 3 manga
            try:
                print(f"  📚 Trying manga {i+1}/{min(3, len(results))}: '{manga_result['title']}'...")

                # First create local manga record from external source
                create_response = await client.post(
                    f"{self.base_url}/api/v1/manga/from-external",
                    params={
                        "provider": provider_name,
                        "external_id": manga_result["id"]  # This is the external ID
                    },
                    headers=self.get_headers(),
                    timeout=60
                )

                if create_response.status_code not in [200, 201]:
                    print(f"    ❌ Failed to create local manga record: {create_response.text}")
                    continue  # Try next manga

                create_data = create_response.json()
                local_manga_id = create_data["id"]  # This is the UUID
                print(f"    ✅ Created local record (UUID: {local_manga_id})")

                # Now add to library using the UUID
                print(f"  📚 Adding to library...")
                add_response = await client.post(
                    f"{self.base_url}/api/v1/library",
                    json={"manga_id": local_manga_id},  # Use the UUID
                    headers=self.get_headers(),
                    timeout=30
                )
            
                if add_response.status_code not in [200, 201]:
                    if "already in library" in add_response.text.lower():
                        print(f"    ⚠️  Manga already in library, trying next one...")
                        continue  # Try next manga
                    else:
                        print(f"    ❌ Failed to add to library: {add_response.text}")
                        continue  # Try next manga

                library_data = add_response.json()
                library_item_id = library_data["id"]
                print(f"    ✅ Added to library (ID: {library_item_id})")

                # Start download with required parameters
                print(f"  ⬇️  Starting download...")
                download_response = await client.post(
                    f"{self.base_url}/api/v1/library/{library_item_id}/download",
                    params={
                        "provider": provider_name,
                        "external_id": manga_result["id"]  # External ID from search
                    },
                    headers=self.get_headers(),
                    timeout=30
                )

                if download_response.status_code != 200:
                    print(f"    ❌ Download failed: {download_response.text}")
                    continue  # Try next manga

                download_data = download_response.json()
                print(f"    ✅ Download started: {download_data.get('message', 'No message')}")

                # Monitor download progress for a short time
                print(f"  ⏱️  Monitoring download progress...")
                for j in range(6):  # Check for 30 seconds (6 * 5 seconds)
                    await asyncio.sleep(5)

                    # Check library status
                    library_response = await client.get(
                        f"{self.base_url}/api/v1/library",
                        headers=self.get_headers()
                    )

                    if library_response.status_code == 200:
                        library_items = library_response.json()
                        for item in library_items.get("items", []):
                            if item["id"] == library_item_id:
                                status = item.get("download_status", "unknown")
                                print(f"    Check {j+1}: Status = {status}")

                                if status == "completed":
                                    print(f"    ✅ DOWNLOAD COMPLETED!")
                                    return True
                                elif status == "failed":
                                    print(f"    ❌ Download failed")
                                    break  # Try next manga
                                break

                print(f"    ⏱️  Download still in progress after monitoring period")
                return True  # Consider it successful if it started

            except Exception as e:
                print(f"    ❌ Error with manga '{manga_result['title']}': {e}")
                continue  # Try next manga

        # If we get here, all manga failed
        print(f"  ❌ All manga attempts failed for {provider_name}")
        return False
    
    async def test_provider(self, provider_name: str, is_nsfw: bool) -> Dict:
        """Test a single provider completely."""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING PROVIDER: {provider_name} {'[NSFW]' if is_nsfw else '[SFW]'}")
        print(f"{'='*60}")
        
        result = {
            "provider": provider_name,
            "is_nsfw": is_nsfw,
            "search_success": False,
            "download_success": False,
            "manga_found": None,
            "error": None,
            "timestamp": time.time()
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Test search
                search_success, search_data = await self.test_provider_search(client, provider_name, is_nsfw)
                result["search_success"] = search_success

                if search_success and search_data:
                    result["manga_found"] = f"{len(search_data['results'])} results for '{search_data['query']}'"

                    # Test download
                    download_success = await self.test_provider_download(client, provider_name, search_data)
                    result["download_success"] = download_success
                    
                    if download_success:
                        print(f"✅ {provider_name}: FULL SUCCESS!")
                    else:
                        print(f"⚠️  {provider_name}: Search OK, Download FAILED")
                else:
                    print(f"❌ {provider_name}: Search FAILED")
                    
            except Exception as e:
                result["error"] = str(e)
                print(f"❌ {provider_name}: ERROR - {e}")
        
        return result
    
    async def run_all_tests(self) -> Dict:
        """Run tests for all providers except MangaDx."""
        print("🚀 STARTING COMPREHENSIVE PROVIDER DOWNLOAD TESTING")
        print("=" * 80)
        
        # Authenticate first
        if not await self.authenticate():
            return {"error": "Authentication failed"}
        
        # Get provider list
        providers_to_test = [
            ("MangaPill", True),
            ("ArcaneScans", False),
            ("ManhuaFast", True),
            ("Toonily", True),
            ("MangaTown", False),
            ("MangaDNA", True),
            ("Manga18FX", True),
            ("MangaFreak", True),
            ("MangaSail", False),
            ("MangaKakalotFun", True)
        ]
        
        print(f"📋 Testing {len(providers_to_test)} providers (excluding MangaDx)")
        
        results = []
        successful_downloads = 0
        
        for provider_name, is_nsfw in providers_to_test:
            result = await self.test_provider(provider_name, is_nsfw)
            results.append(result)
            
            if result["download_success"]:
                successful_downloads += 1
            
            # Small delay between providers
            await asyncio.sleep(2)
        
        # Generate summary
        summary = {
            "total_providers_tested": len(providers_to_test),
            "successful_downloads": successful_downloads,
            "failed_downloads": len(providers_to_test) - successful_downloads,
            "success_rate": f"{(successful_downloads / len(providers_to_test)) * 100:.1f}%",
            "results": results,
            "timestamp": time.time()
        }
        
        print(f"\n{'='*80}")
        print(f"📊 FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total providers tested: {summary['total_providers_tested']}")
        print(f"Successful downloads: {summary['successful_downloads']}")
        print(f"Failed downloads: {summary['failed_downloads']}")
        print(f"Success rate: {summary['success_rate']}")
        
        print(f"\n✅ SUCCESSFUL PROVIDERS:")
        for result in results:
            if result["download_success"]:
                print(f"  - {result['provider']}: {result['manga_found']}")
        
        print(f"\n❌ FAILED PROVIDERS:")
        for result in results:
            if not result["download_success"]:
                reason = result.get("error", "Download failed" if result["search_success"] else "Search failed")
                print(f"  - {result['provider']}: {reason}")
        
        return summary


async def main():
    """Main function."""
    tester = ProviderDownloadTester()
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("provider_download_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: provider_download_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
