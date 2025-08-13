#!/usr/bin/env python3
"""
Working Providers Test Script
Tests the 7 fully working providers and 2 partially working providers.
"""

import asyncio
import logging
import sys
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the backend directory to the path
sys.path.append('/app')
sys.path.append('/app/backend')

from app.core.providers.registry import provider_registry
from app.db.session import AsyncSessionLocal
from app.models.manga import Manga, Chapter
from app.models.library import MangaUserLibrary
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Working providers configuration
WORKING_PROVIDERS = {
    # Fully working providers
    "MangaDex": {
        "status": "fully_working",
        "test_queries": ["naruto", "one piece"],
        "expected_chapters": 50,
        "expected_pages": 10,
        "content_type": "Japanese Manga"
    },
    "MangaTown": {
        "status": "fully_working", 
        "test_queries": ["naruto", "bleach"],
        "expected_chapters": 20,
        "expected_pages": 15,
        "content_type": "Japanese Manga"
    },
    "Toonily": {
        "status": "fully_working",
        "test_queries": ["solo leveling", "tower of god"],
        "expected_chapters": 30,
        "expected_pages": 50,
        "content_type": "Korean Manhwa"
    },
    "MangaDNA": {
        "status": "fully_working",
        "test_queries": ["demon slayer", "attack on titan"],
        "expected_chapters": 90,
        "expected_pages": 100,
        "content_type": "Mixed Content"
    },
    "MangaSail": {
        "status": "fully_working",
        "test_queries": ["solo leveling ragnarok", "tower of god"],
        "expected_chapters": 150,
        "expected_pages": 15,
        "content_type": "Korean Manhwa"
    },
    "MangaKakalotFun": {
        "status": "fully_working",
        "test_queries": ["naruto", "one piece"],
        "expected_chapters": 500,
        "expected_pages": 15,
        "content_type": "Mixed Content"
    },
    "ManhuaFast": {
        "status": "fully_working",
        "test_queries": ["solo leveling", "martial peak"],
        "expected_chapters": 15,
        "expected_pages": 10,
        "content_type": "Chinese Manhua"
    },
    # Partially working providers
    "FreeManga": {
        "status": "partially_working",
        "test_queries": ["naruto", "one piece"],
        "expected_chapters": 0,  # Chapters don't work
        "expected_pages": 0,     # Pages don't work
        "content_type": "Mixed Content",
        "notes": "Search works, chapters need JS"
    },
    "OmegaScans": {
        "status": "partially_working",
        "test_queries": ["teacher's efforts", "revenge"],
        "expected_chapters": 0,  # Discovery doesn't work
        "expected_pages": 10,    # Direct access works
        "content_type": "NSFW Content",
        "notes": "Direct access works, discovery needs JS"
    }
}

class ProviderTestResult:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.status = WORKING_PROVIDERS.get(provider_name, {}).get("status", "unknown")
        self.search_success = False
        self.search_results_count = 0
        self.search_error = ""
        self.details_success = False
        self.details_error = ""
        self.chapters_success = False
        self.chapters_count = 0
        self.chapters_error = ""
        self.pages_success = False
        self.pages_count = 0
        self.pages_error = ""
        self.test_manga_title = ""
        self.test_manga_id = ""
        self.test_duration = 0.0
        self.overall_status = "NOT_WORKING"

async def get_test_user() -> Optional[User]:
    """Get or create a test user."""
    async with AsyncSessionLocal() as db:
        # Try to find existing test user
        result = await db.execute(
            select(User).where(User.email == "futs69@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Test user found: {user.email}")
            return user
        else:
            print("❌ Test user not found")
            return None

async def test_provider(provider_name: str) -> ProviderTestResult:
    """Test a single provider comprehensively."""
    start_time = datetime.now()
    result = ProviderTestResult(provider_name)
    
    try:
        print(f"\n🧪 Testing Provider: {provider_name}")
        print("=" * 60)
        
        # Get provider instance
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            result.search_error = f"Provider {provider_name} not found in registry"
            print(f"❌ Provider not found: {provider_name}")
            return result
        
        print(f"✅ Provider found: {provider.name}")
        print(f"📍 Provider URL: {getattr(provider, 'base_url', 'N/A')}")
        print()
        
        # Get provider config
        config = WORKING_PROVIDERS.get(provider_name, {})
        test_queries = config.get("test_queries", ["naruto"])
        expected_chapters = config.get("expected_chapters", 10)
        expected_pages = config.get("expected_pages", 10)
        
        # Test 1: Search
        print("🔍 Step 1: Testing Search Functionality")
        print("-" * 40)
        
        search_results = None
        for i, query in enumerate(test_queries, 1):
            print(f"  [{i}/{len(test_queries)}] Searching for: '{query}'")
            try:
                search_task = asyncio.create_task(provider.search(query, page=1, limit=3))
                search_results, total, has_next = await asyncio.wait_for(search_task, timeout=15.0)
                
                if search_results and len(search_results) > 0:
                    result.search_success = True
                    result.search_results_count = len(search_results)
                    print(f"    ✅ Success: {len(search_results)} results found")
                    print(f"    📊 Total available: {total}")
                    print(f"    📄 Has more pages: {has_next}")
                    break
                else:
                    print(f"    ❌ No results for '{query}'")
                    
            except asyncio.TimeoutError:
                result.search_error = f"Search timeout for query: {query}"
                print(f"    ⏰ Timeout for '{query}'")
            except Exception as e:
                result.search_error = f"Search error: {str(e)}"
                print(f"    ❌ Error for '{query}': {e}")
        
        if not search_results:
            print("❌ All search queries failed")
            return result
        
        # Select test manga
        test_manga = search_results[0]
        result.test_manga_title = test_manga.title
        result.test_manga_id = test_manga.id
        print(f"📚 Selected test manga: '{test_manga.title}'")
        print(f"🆔 Manga ID: {test_manga.id}")
        
        # Test 2: Get manga details
        print(f"\n📖 Step 2: Testing Manga Details Retrieval")
        print("-" * 40)
        print(f"  Fetching details for manga ID: {test_manga.id}")
        
        try:
            details_task = asyncio.create_task(provider.get_manga_details(test_manga.id))
            details = await asyncio.wait_for(details_task, timeout=10.0)
            
            if details:
                result.details_success = True
                print(f"  ✅ Details retrieved successfully")
                print(f"  📝 Title: {details.get('title', 'N/A')}")
                print(f"  📄 Description: {details.get('description', 'N/A')[:50]}...")
                tags = details.get('tags', [])
                print(f"  🏷️  Tags: {len(tags)} tags")
            else:
                result.details_error = "No details returned"
                print(f"  ❌ No details returned")
                
        except asyncio.TimeoutError:
            result.details_error = "Details timeout"
            print(f"  ⏰ Details timeout")
        except Exception as e:
            result.details_error = f"Details error: {str(e)}"
            print(f"  ❌ Details error: {e}")
        
        # Test 3: Get chapters
        print(f"\n📚 Step 3: Testing Chapter Listing")
        print("-" * 40)
        print(f"  Fetching chapters for manga ID: {test_manga.id}")
        
        try:
            chapters_task = asyncio.create_task(provider.get_chapters(test_manga.id, limit=10))
            chapters, total_chapters, has_next_chapters = await asyncio.wait_for(chapters_task, timeout=15.0)
            
            if chapters and len(chapters) > 0:
                result.chapters_success = True
                result.chapters_count = len(chapters)
                print(f"  ✅ Chapters retrieved successfully")
                print(f"  📊 Chapters found: {len(chapters)}")
                print(f"  📈 Total available: {total_chapters}")
                print(f"  📄 Has more pages: {has_next_chapters}")
                
                # Show first few chapters
                for i, chapter in enumerate(chapters[:3]):
                    title = chapter.get('title', 'N/A')
                    chapter_id = chapter.get('id', 'N/A')
                    print(f"    [{i+1}] {title} (ID: {chapter_id})")
                
            else:
                result.chapters_error = "No chapters returned"
                print(f"  ❌ No chapters returned")
                
        except asyncio.TimeoutError:
            result.chapters_error = "Chapters timeout"
            print(f"  ⏰ Chapters timeout")
        except Exception as e:
            result.chapters_error = f"Chapters error: {str(e)}"
            print(f"  ❌ Chapters error: {e}")
        
        # Test 4: Get pages (only if chapters work)
        if result.chapters_success and chapters:
            print(f"\n📄 Step 4: Testing Page Extraction")
            print("-" * 40)
            
            test_chapter = chapters[0]
            print(f"  Testing chapter: '{test_chapter.get('title', 'N/A')}'")
            print(f"  Chapter ID: {test_chapter.get('id', 'N/A')}")
            print(f"  Manga ID: {test_manga.id}")
            print(f"  Fetching pages...")
            
            try:
                pages_task = asyncio.create_task(provider.get_pages(test_manga.id, test_chapter.get('id')))
                pages = await asyncio.wait_for(pages_task, timeout=10.0)
                
                if pages and len(pages) > 0:
                    result.pages_success = True
                    result.pages_count = len(pages)
                    print(f"  ✅ Pages extracted successfully")
                    print(f"  📊 Pages found: {len(pages)}")
                    print(f"  🔗 First page: {pages[0][:80]}...")
                    if len(pages) > 1:
                        print(f"  🔗 Last page: {pages[-1][:80]}...")
                else:
                    result.pages_error = "No pages returned"
                    print(f"  ❌ No pages returned")
                    
            except asyncio.TimeoutError:
                result.pages_error = "Pages timeout"
                print(f"  ⏰ Pages timeout")
            except Exception as e:
                result.pages_error = f"Pages error: {str(e)}"
                print(f"  ❌ Pages error: {e}")
        
        # Determine overall status
        if result.search_success and result.details_success and result.chapters_success and result.pages_success:
            result.overall_status = "FULLY_WORKING"
        elif result.search_success and (result.details_success or result.chapters_success or result.pages_success):
            result.overall_status = "PARTIALLY_WORKING"
        else:
            result.overall_status = "NOT_WORKING"
        
    except Exception as e:
        result.search_error = f"Provider test failed: {str(e)}"
        print(f"❌ Provider test failed: {e}")
        traceback.print_exc()
    
    finally:
        end_time = datetime.now()
        result.test_duration = (end_time - start_time).total_seconds()
    
    return result

async def main():
    """Main test function."""
    print("🧪 Working Providers Test Suite")
    print("⏰ Started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    # Get test user
    user = await get_test_user()
    if not user:
        print("❌ Cannot proceed without test user")
        return
    
    print()
    
    # Test all working providers
    results = []
    total_providers = len(WORKING_PROVIDERS)
    
    for i, provider_name in enumerate(WORKING_PROVIDERS.keys(), 1):
        print(f"\n[{i}/{total_providers}] Testing {provider_name}")
        print("=" * 80)
        
        result = await test_provider(provider_name)
        results.append(result)
        
        # Show result summary
        config = WORKING_PROVIDERS[provider_name]
        expected_status = config["status"]
        content_type = config["content_type"]
        
        print(f"\n📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Provider: {provider_name}")
        print(f"Expected Status: {expected_status}")
        print(f"Content Type: {content_type}")
        print(f"Duration: {result.test_duration:.1f}s")
        print(f"Search: {'✅' if result.search_success else '❌'} {'Success' if result.search_success else 'Failed'} ({result.search_results_count} results)")
        print(f"Details: {'✅' if result.details_success else '❌'} {'Success' if result.details_success else 'Failed'}")
        print(f"Chapters: {'✅' if result.chapters_success else '❌'} {'Success' if result.chapters_success else 'Failed'} ({result.chapters_count} chapters)")
        print(f"Pages: {'✅' if result.pages_success else '❌'} {'Success' if result.pages_success else 'Failed'} ({result.pages_count} pages)")
        print(f"🎉 OVERALL: {result.overall_status}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if config.get("notes"):
            print(f"📝 Notes: {config['notes']}")
    
    # Final summary
    print(f"\n🎉 FINAL SUMMARY")
    print("=" * 80)
    
    fully_working = [r for r in results if r.overall_status == "FULLY_WORKING"]
    partially_working = [r for r in results if r.overall_status == "PARTIALLY_WORKING"]
    not_working = [r for r in results if r.overall_status == "NOT_WORKING"]
    
    print(f"✅ Fully Working: {len(fully_working)}/{total_providers}")
    for r in fully_working:
        print(f"   - {r.provider_name}")
    
    print(f"⚠️ Partially Working: {len(partially_working)}/{total_providers}")
    for r in partially_working:
        print(f"   - {r.provider_name}")
    
    print(f"❌ Not Working: {len(not_working)}/{total_providers}")
    for r in not_working:
        print(f"   - {r.provider_name}")
    
    success_rate = (len(fully_working) / total_providers) * 100
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    print(f"⏰ Total Duration: {sum(r.test_duration for r in results):.1f}s")
    print(f"🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
