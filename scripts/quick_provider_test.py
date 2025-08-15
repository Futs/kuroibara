#!/usr/bin/env python3
"""
Quick Provider Test - Tests key providers quickly
"""

import asyncio
import sys
sys.path.append('/app')

from app.core.providers.registry import provider_registry

# Priority providers to test first
PRIORITY_PROVIDERS = [
    "MangaDex",
    "MangaPill",
    "MangaHub",
    "MangaReaderTo",
    "DynastyScans",
    "OmegaScans"
]

async def quick_test_provider(provider_name: str):
    """Quick test of a provider."""
    print(f"Testing {provider_name}...")
    
    try:
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            print(f"  ❌ Provider not found")
            return False
        
        # Test search
        try:
            results, total, has_next = await provider.search("naruto", page=1, limit=3)
            if not results or len(results) == 0:
                print(f"  ❌ No search results")
                return False
            
            print(f"  ✅ Search: {len(results)} results")
            
            # Test manga details
            manga = results[0]
            manga_id = manga.get('id')
            if not manga_id:
                print(f"  ❌ No manga ID")
                return False
            
            details = await provider.get_manga_details(manga_id)
            print(f"  ✅ Details: {manga.get('title', 'Unknown')}")
            
            # Test chapters
            chapters, total_chapters, has_next = await provider.get_chapters(manga_id, page=1, limit=3)
            if not chapters or len(chapters) == 0:
                print(f"  ⚠️  No chapters available")
                return True  # Still consider it working
            
            print(f"  ✅ Chapters: {len(chapters)} found")
            
            # Test pages
            chapter = chapters[0]
            chapter_id = chapter.get('id')
            if chapter_id:
                pages = await provider.get_pages(manga_id, chapter_id)
                if pages and len(pages) > 0:
                    print(f"  ✅ Pages: {len(pages)} pages")
                    return True
                else:
                    print(f"  ⚠️  No pages found")
                    return True
            else:
                print(f"  ⚠️  No chapter ID")
                return True
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Fatal error: {str(e)[:100]}")
        return False

async def main():
    print("🚀 Quick Provider Test")
    print("=" * 40)
    
    working = []
    broken = []
    
    # Test priority providers
    for provider_name in PRIORITY_PROVIDERS:
        success = await quick_test_provider(provider_name)
        if success:
            working.append(provider_name)
        else:
            broken.append(provider_name)
        print()
    
    # Test a few more random providers
    all_providers = provider_registry.get_provider_names()
    other_providers = [p for p in all_providers if p not in PRIORITY_PROVIDERS][:5]
    
    print("Testing additional providers...")
    for provider_name in other_providers:
        success = await quick_test_provider(provider_name)
        if success:
            working.append(provider_name)
        else:
            broken.append(provider_name)
        print()
    
    print("📊 SUMMARY")
    print("=" * 40)
    print(f"✅ Working: {len(working)}")
    for p in working:
        print(f"   • {p}")
    
    print(f"\n❌ Not Working: {len(broken)}")
    for p in broken:
        print(f"   • {p}")
    
    print(f"\n📈 Success Rate: {len(working)}/{len(working)+len(broken)} ({len(working)/(len(working)+len(broken))*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())
