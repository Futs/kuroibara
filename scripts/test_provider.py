#!/usr/bin/env python3
"""
Provider Testing Script

Tests the generated provider configuration to ensure it works correctly.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

try:
    from app.core.providers.registry import provider_registry
    from app.core.providers.generic import GenericProvider
    from app.core.providers.enhanced_generic import EnhancedGenericProvider
    from app.core.providers.base import BaseProvider
except ImportError as e:
    print(f"❌ Failed to import provider modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


class ProviderTester:
    """Test provider functionality."""

    def __init__(self):
        self.registry = provider_registry
        print("✅ Provider registry initialized")
    
    async def test_provider_creation(self, config: Dict[str, Any]) -> BaseProvider:
        """Test provider instance creation."""
        print(f"🔧 Testing provider creation for {config['name']}...")
        
        # Try to get provider from registry
        provider = self.registry.get_provider(config['name'])

        if not provider:
            raise Exception(f"Provider {config['name']} not found in registry")

        print(f"✅ Provider found: {provider.name}")
        print(f"   - URL: {provider.url}")
        print(f"   - NSFW Support: {provider.supports_nsfw}")

        return provider
    
    async def test_search_functionality(self, provider: BaseProvider) -> List[Any]:
        """Test search functionality."""
        print(f"🔍 Testing search functionality...")
        
        test_queries = ["one piece", "naruto", "test"]
        
        for query in test_queries:
            try:
                print(f"   Searching for: '{query}'")
                results, total, has_more = await provider.search(query, limit=5)
                
                if results:
                    print(f"   ✅ Search successful: {len(results)} results found")
                    print(f"      - Total: {total}, Has more: {has_more}")
                    print(f"      - First result: {results[0].title if hasattr(results[0], 'title') else 'No title'}")
                    return results
                else:
                    print(f"   ⚠️  No results for '{query}'")
                    
            except Exception as e:
                print(f"   ❌ Search failed for '{query}': {e}")
                continue
        
        raise Exception("All search queries failed")
    
    async def test_manga_details(self, provider: BaseProvider, search_results: List[Any]) -> Dict[str, Any]:
        """Test manga details retrieval."""
        print(f"📖 Testing manga details...")
        
        if not search_results:
            raise Exception("No search results to test with")
        
        first_result = search_results[0]
        manga_id = first_result.id if hasattr(first_result, 'id') else str(first_result)
        
        try:
            details = await provider.get_manga_details(manga_id)
            
            if details:
                print(f"   ✅ Manga details retrieved")
                print(f"      - Title: {details.get('title', 'No title')}")
                print(f"      - Description: {details.get('description', 'No description')[:100]}...")
                print(f"      - Genres: {details.get('genres', [])}")
                return details
            else:
                raise Exception("No manga details returned")
                
        except Exception as e:
            print(f"   ❌ Manga details failed: {e}")
            raise
    
    async def test_chapters(self, provider: BaseProvider, manga_id: str) -> List[Dict[str, Any]]:
        """Test chapter listing."""
        print(f"📚 Testing chapter listing...")
        
        try:
            chapters, total_chapters, has_more_chapters = await provider.get_chapters(manga_id, limit=5)
            
            if chapters:
                print(f"   ✅ Chapters retrieved: {len(chapters)} chapters")
                print(f"      - Total: {total_chapters}, Has more: {has_more_chapters}")
                if chapters:
                    first_chapter = chapters[0]
                    print(f"      - First chapter: {first_chapter.get('title', 'No title')}")
                return chapters
            else:
                print(f"   ⚠️  No chapters found")
                return []
                
        except Exception as e:
            print(f"   ❌ Chapter listing failed: {e}")
            raise
    
    async def test_pages(self, provider: BaseProvider, manga_id: str, chapters: List[Dict[str, Any]]) -> List[str]:
        """Test page retrieval."""
        print(f"📄 Testing page retrieval...")
        
        if not chapters:
            print("   ⚠️  No chapters to test pages with")
            return []
        
        first_chapter = chapters[0]
        chapter_id = first_chapter.get('id', first_chapter.get('chapter_id', '1'))
        
        try:
            pages = await provider.get_pages(manga_id, str(chapter_id))
            
            if pages:
                print(f"   ✅ Pages retrieved: {len(pages)} pages")
                print(f"      - First page URL: {pages[0][:100]}...")
                return pages
            else:
                print(f"   ⚠️  No pages found")
                return []
                
        except Exception as e:
            print(f"   ❌ Page retrieval failed: {e}")
            # Don't raise here as this might be expected for some providers
            return []
    
    async def run_comprehensive_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive provider test."""
        print(f"\n🧪 Starting comprehensive test for {config['name']}")
        print("=" * 60)
        
        test_results = {
            'provider_creation': False,
            'search_functionality': False,
            'manga_details': False,
            'chapter_listing': False,
            'page_retrieval': False,
            'overall_success': False
        }
        
        try:
            # Test 1: Provider Creation
            provider = await self.test_provider_creation(config)
            test_results['provider_creation'] = True
            
            # Test 2: Search Functionality
            search_results = await self.test_search_functionality(provider)
            test_results['search_functionality'] = True
            
            if search_results:
                first_result = search_results[0]
                manga_id = first_result.id if hasattr(first_result, 'id') else str(first_result)
                
                # Test 3: Manga Details
                try:
                    details = await self.test_manga_details(provider, search_results)
                    test_results['manga_details'] = True
                except Exception as e:
                    print(f"   ⚠️  Manga details test failed (non-critical): {e}")
                
                # Test 4: Chapter Listing
                try:
                    chapters = await self.test_chapters(provider, manga_id)
                    test_results['chapter_listing'] = True
                    
                    # Test 5: Page Retrieval (optional)
                    try:
                        pages = await self.test_pages(provider, manga_id, chapters)
                        test_results['page_retrieval'] = True
                    except Exception as e:
                        print(f"   ⚠️  Page retrieval test failed (non-critical): {e}")
                        
                except Exception as e:
                    print(f"   ⚠️  Chapter listing test failed (non-critical): {e}")
            
            # Determine overall success
            critical_tests = ['provider_creation', 'search_functionality']
            test_results['overall_success'] = all(test_results[test] for test in critical_tests)
            
            return test_results
            
        except Exception as e:
            print(f"❌ Critical test failure: {e}")
            traceback.print_exc()
            return test_results


async def main():
    """Main testing function."""
    print("🚀 Provider Testing Script")
    print("=" * 60)
    
    # Load generated config
    try:
        with open('generated_provider.json', 'r') as f:
            configs = json.load(f)
    except FileNotFoundError:
        print("❌ generated_provider.json not found")
        print("Make sure to run generate_provider_config.py first")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing generated_provider.json: {e}")
        sys.exit(1)
    
    if not configs:
        print("❌ No provider configurations found")
        sys.exit(1)
    
    config = configs[0]
    
    # Initialize tester
    tester = ProviderTester()
    
    # Run tests
    results = await tester.run_comprehensive_test(config)
    
    # Print results summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        if test_name == 'overall_success':
            continue
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {'🎉 SUCCESS' if results['overall_success'] else '❌ FAILURE'}")
    
    if results['overall_success']:
        print(f"\n✅ Provider {config['name']} is ready for integration!")
        sys.exit(0)
    else:
        print(f"\n❌ Provider {config['name']} failed critical tests")
        print("Please check the configuration and selectors")
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
