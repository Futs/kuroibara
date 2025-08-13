#!/usr/bin/env python3
"""
Provider Testing Script
Tests all 32 providers by searching, adding manga, and downloading chapters.
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List

# Add the backend directory to the path
sys.path.append("/app")
sys.path.append("/app/backend")

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.providers.registry import provider_registry
from app.db.session import get_db
from app.models.library import MangaUserLibrary
from app.models.manga import Chapter, Manga
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test queries for different types of content
TEST_QUERIES = ["naruto", "one piece", "attack on titan", "demon slayer", "dragon ball"]

# Providers known to have Cloudflare protection or be unhealthy
SKIP_PROVIDERS = {
    "AllPornComic",  # Cloudflare protected
    "AnshScans",  # Slow/unreliable
    "HentaiNexus",  # Often down
    "HentaiRead",  # Cloudflare protected
    "HentaiWebtoon",  # Cloudflare protected
    "Manga18FX",  # Adult content + protection
    "MangaFoxFull",  # Often blocked
    "MangaFreak",  # Unreliable
    "MangaHere",  # Often down
    "MangaTown",  # Cloudflare protected
    "ReadAllComics",  # Cloudflare protected
    "TAADD",  # Often unreliable
    "Tsumino",  # Adult content + protection
}

# Priority providers to test first (known to be more reliable)
PRIORITY_PROVIDERS = [
    "MangaDex",
    "MangaFire",
    "MangaPill",
    "MangaHub",
    "MangaReaderTo",
    "DynastyScans",
    "ReaperScans",
    "OmegaScans",
    "ArcaneScans",
    "MangaGG",
]


class ProviderTestResult:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.search_success = False
        self.search_results_count = 0
        self.search_error = ""
        self.manga_details_success = False
        self.manga_details_error = ""
        self.chapters_success = False
        self.chapters_count = 0
        self.chapters_error = ""
        self.add_to_library_success = False
        self.add_to_library_error = ""
        self.download_success = False
        self.download_error = ""
        self.test_manga_title = ""
        self.test_manga_id = ""


async def test_provider(
    provider_name: str, db: AsyncSession, user_id: uuid.UUID
) -> ProviderTestResult:
    """Test a single provider comprehensively."""
    result = ProviderTestResult(provider_name)

    try:
        # Skip problematic providers
        if provider_name in SKIP_PROVIDERS:
            result.search_error = f"Skipped - {provider_name} is known to be problematic (Cloudflare/unreliable)"
            return result

        # Get provider instance
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            result.search_error = "Provider not found in registry"
            return result

        logger.info(f"Testing provider: {provider_name}")

        # Test 1: Search for manga (with timeout)
        search_results = None
        for query in TEST_QUERIES:
            try:
                # Add timeout to prevent hanging
                search_task = asyncio.create_task(
                    provider.search(query, page=1, limit=3)
                )
                search_results, total, has_next = await asyncio.wait_for(
                    search_task, timeout=15.0
                )

                if search_results and len(search_results) > 0:
                    result.search_success = True
                    result.search_results_count = len(search_results)
                    break
            except asyncio.TimeoutError:
                logger.warning(
                    f"Search timeout for {provider_name} with query '{query}'"
                )
                continue
            except Exception as e:
                # Check for Cloudflare protection
                error_str = str(e).lower()
                if (
                    "cloudflare" in error_str
                    or "403" in error_str
                    or "forbidden" in error_str
                ):
                    result.search_error = f"Cloudflare protection detected"
                    return result
                continue

        if not result.search_success:
            result.search_error = "No search results found for any test query"
            return result

        # Get first manga from search results
        test_manga = search_results[0]

        # Handle both dict and Pydantic model objects
        if hasattr(test_manga, "title"):
            result.test_manga_title = test_manga.title or "Unknown"
            result.test_manga_id = test_manga.id
        else:
            result.test_manga_title = test_manga.get("title", "Unknown")
            result.test_manga_id = test_manga.get("id")

        if not result.test_manga_id:
            result.search_error = "No manga ID in search results"
            return result

        # Test 2: Get manga details
        try:
            details_task = asyncio.create_task(
                provider.get_manga_details(result.test_manga_id)
            )
            manga_details = await asyncio.wait_for(details_task, timeout=10.0)
            result.manga_details_success = True
        except asyncio.TimeoutError:
            result.manga_details_error = "Timeout getting manga details"
            return result
        except Exception as e:
            result.manga_details_error = str(e)
            return result

        # Test 3: Get chapters
        try:
            chapters_task = asyncio.create_task(
                provider.get_chapters(result.test_manga_id, page=1, limit=5)
            )
            chapters, total_chapters, has_next = await asyncio.wait_for(
                chapters_task, timeout=15.0
            )
            result.chapters_success = True
            result.chapters_count = len(chapters)

            if result.chapters_count == 0:
                result.chapters_error = "No chapters found"
                return result

        except asyncio.TimeoutError:
            result.chapters_error = "Timeout getting chapters"
            return result
        except Exception as e:
            result.chapters_error = str(e)
            return result

        # Test 4: Add manga to library (simulate)
        try:
            # Create manga record
            manga_data = {
                "title": result.test_manga_title,
                "provider": provider_name,
                "external_id": result.test_manga_id,
                "description": manga_details.get("description", ""),
                "status": "ongoing",
                "type": "manga",
            }

            # Check if manga already exists
            existing_manga = await db.execute(
                select(Manga).where(
                    Manga.provider == provider_name,
                    Manga.external_id == result.test_manga_id,
                )
            )
            manga = existing_manga.scalar_one_or_none()

            if not manga:
                manga = Manga(**manga_data)
                db.add(manga)
                await db.flush()

            # Check if already in user's library
            existing_library = await db.execute(
                select(MangaUserLibrary).where(
                    MangaUserLibrary.manga_id == manga.id,
                    MangaUserLibrary.user_id == user_id,
                )
            )
            library_item = existing_library.scalar_one_or_none()

            if not library_item:
                library_item = MangaUserLibrary(
                    manga_id=manga.id, user_id=user_id, status="reading"
                )
                db.add(library_item)
                await db.flush()

            result.add_to_library_success = True

        except Exception as e:
            result.add_to_library_error = str(e)
            return result

        # Test 5: Test chapter download (get pages)
        try:
            if chapters and len(chapters) > 0:
                test_chapter = chapters[0]

                # Handle both dict and Pydantic model objects
                if hasattr(test_chapter, "id"):
                    chapter_id = test_chapter.id
                else:
                    chapter_id = test_chapter.get("id")

                if chapter_id:
                    pages_task = asyncio.create_task(
                        provider.get_pages(result.test_manga_id, chapter_id)
                    )
                    pages = await asyncio.wait_for(pages_task, timeout=10.0)
                    if pages and len(pages) > 0:
                        result.download_success = True
                    else:
                        result.download_error = "No pages found for chapter"
                else:
                    result.download_error = "No chapter ID found"
            else:
                result.download_error = "No chapters available for download test"

        except asyncio.TimeoutError:
            result.download_error = "Timeout getting pages"
        except Exception as e:
            result.download_error = str(e)

        await db.commit()

    except Exception as e:
        result.search_error = f"Unexpected error: {str(e)}"
        logger.error(f"Error testing {provider_name}: {e}")
        traceback.print_exc()

    return result


async def main():
    """Main test function."""
    print("🧪 Starting Provider Testing Suite")
    print("=" * 60)

    # Get test user
    async for db in get_db():
        # Get first user for testing
        user_result = await db.execute(select(User).limit(1))
        user = user_result.scalar_one_or_none()

        if not user:
            print("❌ No users found in database. Please create a user first.")
            return

        print(f"📝 Testing with user: {user.email}")
        print()

        # Get all providers and filter out problematic ones
        all_provider_names = provider_registry.get_provider_names()

        # Prioritize testing: test priority providers first, then others
        priority_to_test = [p for p in PRIORITY_PROVIDERS if p in all_provider_names]
        other_to_test = [
            p
            for p in all_provider_names
            if p not in PRIORITY_PROVIDERS and p not in SKIP_PROVIDERS
        ]

        # Combine lists
        provider_names = (
            priority_to_test + other_to_test[:10]
        )  # Limit to avoid too many tests

        results: List[ProviderTestResult] = []

        print(
            f"🔍 Testing {len(provider_names)} providers (skipping {len(SKIP_PROVIDERS)} problematic ones)..."
        )
        print(f"📋 Skipped providers: {', '.join(sorted(SKIP_PROVIDERS))}")
        print()

        # Test each provider
        for i, provider_name in enumerate(provider_names, 1):
            print(f"[{i:2d}/{len(provider_names)}] Testing {provider_name}...")

            try:
                result = await test_provider(provider_name, db, user.id)
                results.append(result)

                # Quick status
                status = "✅" if result.search_success else "❌"
                print(f"    {status} Search: {result.search_results_count} results")

                if result.chapters_success:
                    print(f"    ✅ Chapters: {result.chapters_count} found")
                else:
                    print(f"    ❌ Chapters: {result.chapters_error or 'Failed'}")

                if result.download_success:
                    print(f"    ✅ Download: Pages available")
                else:
                    print(f"    ❌ Download: {result.download_error or 'Failed'}")

            except Exception as e:
                print(f"    ❌ Fatal error: {e}")
                result = ProviderTestResult(provider_name)
                result.search_error = f"Fatal error: {e}"
                results.append(result)

            print()

        # Generate summary report
        print("📊 PROVIDER TEST SUMMARY")
        print("=" * 60)

        working_providers = []
        partial_providers = []
        broken_providers = []

        for result in results:
            if (
                result.search_success
                and result.chapters_success
                and result.download_success
            ):
                working_providers.append(result)
            elif result.search_success:
                partial_providers.append(result)
            else:
                broken_providers.append(result)

        print(f"✅ Fully Working: {len(working_providers)}/{len(results)}")
        for result in working_providers:
            print(f"   • {result.provider_name} - {result.test_manga_title}")

        print(f"\n⚠️  Partially Working: {len(partial_providers)}/{len(results)}")
        for result in partial_providers:
            issues = []
            if not result.chapters_success:
                issues.append("no chapters")
            if not result.download_success:
                issues.append("download failed")
            print(f"   • {result.provider_name} - {', '.join(issues)}")

        print(f"\n❌ Not Working: {len(broken_providers)}/{len(results)}")
        for result in broken_providers:
            error = result.search_error or "Unknown error"
            print(f"   • {result.provider_name} - {error}")

        print(
            f"\n📈 Success Rate: {len(working_providers)}/{len(results)} ({len(working_providers)/len(results)*100:.1f}%)"
        )

        break


if __name__ == "__main__":
    asyncio.run(main())
