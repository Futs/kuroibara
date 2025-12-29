#!/usr/bin/env python3
"""
Test the proper MangaUpdates workflow:
1. Search MangaUpdates (tiered indexing) - Get manga metadata
2. Add to library with MangaUpdates metadata + select provider
3. Verify chapters were fetched from PROVIDER (not MangaUpdates)
4. Download chapter content from provider
5. Monitor download progress

NOTE: MangaUpdates provides manga-level metadata only (title, description, cover, genres, etc.)
      Chapter lists and metadata come from providers!
"""

import asyncio
import time
from typing import Dict, Optional

import httpx


class MangaUpdatesWorkflowTester:
    """Test the complete MangaUpdates workflow."""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.access_token = None

        # Test titles that should exist in MangaUpdates
        self.test_titles = [
            "One Piece",
            "Naruto",
            "Solo Leveling",
            "Tower of God",
            "The Beginning After The End",
        ]

    async def authenticate(self) -> bool:
        """Authenticate and get access token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"username": "testuser_provider", "password": "password123"},
                )

                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    print("✅ Authentication successful\n")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status_code}")
                    return False

            except Exception as e:
                print(f"❌ Authentication error: {e}")
                return False

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    async def search_mangaupdates(
        self, client: httpx.AsyncClient, query: str
    ) -> Optional[Dict]:
        """Search MangaUpdates using enhanced search."""
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/search/enhanced",
                params={"query": query, "limit": 5, "include_provider_matches": True},
                headers=self.get_headers(),
                timeout=120.0,  # Increased timeout for provider matching
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    return data["results"][0]  # Return first result
                else:
                    print(f"    ⚠️  No results found for '{query}'")
                    return None
            else:
                print(f"    ❌ Search failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"    ❌ Search error: {e}")
            return None

    async def add_to_library(
        self,
        client: httpx.AsyncClient,
        mu_entry_id: str,
        title: str,
        provider_match: Optional[Dict] = None,
    ) -> Optional[str]:
        """Add manga to library from MangaUpdates entry with optional provider."""
        try:
            # Prepare request body
            request_data = {}
            if provider_match:
                request_data["selected_provider_match"] = provider_match

            response = await client.post(
                f"{self.base_url}/api/v1/search/enhanced/add-from-mangaupdates",
                params={"mu_entry_id": mu_entry_id},
                json=request_data if request_data else None,
                headers=self.get_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                manga_id = data.get("manga_id")
                print(f"    ✅ Added to library (Manga ID: {manga_id})")
                return manga_id
            else:
                error_detail = response.json().get("detail", response.text)
                print(f"    ❌ Failed to add to library: {error_detail}")
                return None

        except Exception as e:
            print(f"    ❌ Add to library error: {e}")
            return None

    async def get_library_item_id(
        self, client: httpx.AsyncClient, manga_id: str
    ) -> Optional[str]:
        """Get library item ID for a manga."""
        try:
            response = await client.get(
                f"{self.base_url}/api/v1/library", headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                for item in items:
                    if item.get("manga_id") == manga_id:
                        return item.get("id")
                return None
            else:
                return None

        except Exception as e:
            print(f"    ❌ Get library item error: {e}")
            return None

    async def get_chapters(self, client: httpx.AsyncClient, manga_id: str) -> list:
        """Get chapters for a manga."""
        try:
            response = await client.get(
                f"{self.base_url}/api/v1/manga/{manga_id}/chapters",
                headers=self.get_headers(),
            )

            if response.status_code == 200:
                chapters = response.json()
                print(f"    ✅ Found {len(chapters)} chapters in library")
                return chapters
            else:
                print(f"    ❌ Failed to get chapters: {response.status_code}")
                return []

        except Exception as e:
            print(f"    ❌ Get chapters error: {e}")
            return []

    async def download_chapter(
        self, client: httpx.AsyncClient, library_item_id: str, chapters: list
    ) -> Optional[str]:
        """Start downloading a chapter."""
        try:
            if not chapters:
                print("    ⚠️  No chapters available")
                return None

            # Download first chapter
            chapter = chapters[0]
            chapter_id = chapter.get("id")
            chapter_title = chapter.get("title", "Chapter 1")
            print(f"    📥 Starting download of '{chapter_title}'...")

            download_response = await client.post(
                f"{self.base_url}/api/v1/library/{library_item_id}/download-chapter",
                json={"chapter_id": chapter_id},
                headers=self.get_headers(),
            )

            if download_response.status_code == 200:
                data = download_response.json()
                task_id = data.get("task_id")
                print(f"    ✅ Download started (Task ID: {task_id})")
                return task_id
            else:
                print(f"    ❌ Download failed: {download_response.text}")
                return None

        except Exception as e:
            print(f"    ❌ Download error: {e}")
            return None

    async def monitor_download(
        self, client: httpx.AsyncClient, task_id: str, max_checks: int = 10
    ) -> bool:
        """Monitor download progress."""
        print("    ⏱️  Monitoring download progress...")

        for i in range(max_checks):
            await asyncio.sleep(2)

            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/library/downloads",
                    headers=self.get_headers(),
                )

                if response.status_code == 200:
                    downloads = response.json()
                    for download in downloads:
                        if download.get("task_id") == task_id:
                            status = download.get("status", "unknown")
                            progress = download.get("progress", 0)

                            if status == "completed":
                                print(f"    ✅ Download completed! (100%)")
                                return True
                            elif status == "failed":
                                error = download.get("error_message", "Unknown error")
                                print(f"    ❌ Download failed: {error}")
                                return False
                            else:
                                print(
                                    f"    Check {i+1}: Status = {status}, Progress = {progress}%"
                                )

            except Exception as e:
                print(f"    ⚠️  Monitor error: {e}")

        print("    ⏱️  Download still in progress after monitoring period")
        return False

    async def test_title(self, title: str) -> bool:
        """Test complete workflow for a single title."""
        print(f"\n{'='*70}")
        print(f"🧪 TESTING: {title}")
        print(f"{'='*70}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Search MangaUpdates
            print(f"  1️⃣  Searching MangaUpdates for '{title}'...")
            search_result = await self.search_mangaupdates(client, title)

            if not search_result:
                print(f"❌ {title}: SEARCH FAILED\n")
                return False

            mu_entry_id = search_result.get("id")
            result_title = search_result.get("title")
            print(f"    ✅ Found: {result_title} (ID: {mu_entry_id})")

            # Step 2: Select a provider match (if available)
            provider_matches = search_result.get("provider_matches", [])
            selected_provider = None
            if provider_matches:
                # Select the first provider match
                selected_provider = provider_matches[0]
                print(
                    f"    📍 Selected provider: {selected_provider.get('provider')} (confidence: {selected_provider.get('confidence', 0):.2f})"
                )
            else:
                print(f"    ⚠️  No provider matches found - chapters won't be fetched")

            # Step 3: Add to library with provider
            print(f"  2️⃣  Adding to library with provider...")
            manga_id = await self.add_to_library(
                client, mu_entry_id, result_title, selected_provider
            )

            if not manga_id:
                print(f"⚠️  {title}: LIBRARY ADD FAILED\n")
                return False

            # Step 4: Get library item ID
            print(f"  3️⃣  Getting library item...")
            library_item_id = await self.get_library_item_id(client, manga_id)

            if not library_item_id:
                print(f"    ❌ Failed to get library item ID")
                print(f"⚠️  {title}: LIBRARY ITEM NOT FOUND\n")
                return False

            print(f"    ✅ Library item ID: {library_item_id}")

            # Step 5: Get chapters (should be fetched from PROVIDER)
            print(f"  4️⃣  Getting chapters from library (fetched from provider)...")
            chapters = await self.get_chapters(client, manga_id)

            if not chapters:
                print(f"⚠️  {title}: NO CHAPTERS FOUND\n")
                return False

            # Step 5: Download chapter
            print(f"  5️⃣  Downloading chapter...")
            task_id = await self.download_chapter(client, library_item_id, chapters)

            if not task_id:
                print(f"⚠️  {title}: DOWNLOAD START FAILED\n")
                return False

            # Step 6: Monitor download
            print(f"  6️⃣  Monitoring download...")
            success = await self.monitor_download(client, task_id)

            if success:
                print(f"✅ {title}: COMPLETE SUCCESS!\n")
                return True
            else:
                print(f"⚠️  {title}: DOWNLOAD INCOMPLETE\n")
                return False

    async def run_tests(self):
        """Run tests for all titles."""
        print("🚀 STARTING MANGAUPDATES WORKFLOW TESTING")
        print("=" * 70)
        print("Testing proper workflow:")
        print("  1. Search MangaUpdates (tiered indexing) - Get manga metadata")
        print("  2. Select provider match for chapter source")
        print("  3. Add to library with MangaUpdates metadata + provider")
        print("  4. Verify chapters were fetched from PROVIDER")
        print("  5. Download chapter content from provider")
        print("  6. Monitor download progress")
        print("=" * 70)
        print(
            "NOTE: MangaUpdates = manga metadata, Providers = chapter lists + content"
        )
        print("=" * 70)

        # Authenticate
        if not await self.authenticate():
            print("❌ Authentication failed. Exiting.")
            return

        # Test each title
        results = {}
        for title in self.test_titles:
            success = await self.test_title(title)
            results[title] = success

        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)

        successful = sum(1 for v in results.values() if v)
        total = len(results)

        for title, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {status}: {title}")

        print(f"\n🎯 Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
        print("=" * 70)


async def main():
    """Main entry point."""
    tester = MangaUpdatesWorkflowTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
