#!/usr/bin/env python3
"""
Complete the Phase 4 test scripts by adding the missing test functions.
"""

import os
from pathlib import Path

# Test function template to append to incomplete scripts
TEST_FUNCTIONS = '''
async def test_provider_detailed(provider_name: str, db: AsyncSession, user_id: uuid.UUID) -> ProviderTestResult:
    """Test a single provider with detailed debugging output."""
    result = ProviderTestResult(provider_name)
    
    print(f"🧪 Testing Provider: {provider_name}")
    print("=" * 60)
    
    try:
        # Get provider instance
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            result.search_error = "Provider not found in registry"
            print(f"❌ Provider '{provider_name}' not found in registry")
            return result
        
        print(f"✅ Provider found: {provider.name}")
        print(f"📍 Provider URL: {getattr(provider, 'base_url', 'N/A')}")
        print()
        
        # Test 1: Search for manga (with timeout and detailed output)
        print("🔍 Step 1: Testing Search Functionality")
        print("-" * 40)
        
        search_results = None
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"  [{i}/{len(TEST_QUERIES)}] Searching for: '{query}'")
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
                    print(f"    ⚠️  No results for '{query}'")
            except asyncio.TimeoutError:
                print(f"    ⏰ Timeout for query: '{query}'")
                result.search_error = f"Search timeout for query: {query}"
                continue
            except Exception as e:
                print(f"    ❌ Error for '{query}': {str(e)}")
                result.search_error = f"Search error for query {query}: {str(e)}"
                continue
        
        if not result.search_success:
            print(f"❌ Search failed for all queries")
            return result
        
        # Show search results
        test_manga = search_results[0]
        result.test_manga_title = test_manga.title
        result.test_manga_id = test_manga.id
        
        print(f"📚 Selected test manga: '{test_manga.title}'")
        print(f"🆔 Manga ID: {test_manga.id}")
        print()
        
        # Test 2: Get manga details
        print("📖 Step 2: Testing Manga Details Retrieval")
        print("-" * 40)
        
        try:
            print(f"  Fetching details for manga ID: {test_manga.id}")
            details_task = asyncio.create_task(provider.get_manga_details(test_manga.id))
            manga_details = await asyncio.wait_for(details_task, timeout=10.0)
            
            result.manga_details_success = True
            print(f"  ✅ Details retrieved successfully")
            print(f"  📝 Title: {manga_details.get('title', 'N/A')}")
            print(f"  📄 Description: {manga_details.get('description', 'N/A')[:100]}...")
            print(f"  🏷️  Tags: {len(manga_details.get('tags', []))} tags")
            
        except asyncio.TimeoutError:
            result.manga_details_error = "Details timeout"
            print(f"  ⏰ Timeout while fetching details")
        except Exception as e:
            result.manga_details_error = f"Details error: {str(e)}"
            print(f"  ❌ Error fetching details: {str(e)}")
        
        print()
        
        # Test 3: Get chapters
        print("📚 Step 3: Testing Chapter Listing")
        print("-" * 40)
        
        try:
            print(f"  Fetching chapters for manga ID: {test_manga.id}")
            chapters_task = asyncio.create_task(provider.get_chapters(test_manga.id, page=1, limit=5))
            chapters, total_chapters, has_next_chapters = await asyncio.wait_for(chapters_task, timeout=15.0)
            
            if chapters and len(chapters) > 0:
                result.chapters_success = True
                result.chapters_count = len(chapters)
                print(f"  ✅ Chapters retrieved successfully")
                print(f"  📊 Chapters found: {len(chapters)}")
                print(f"  📈 Total available: {total_chapters}")
                print(f"  📄 Has more pages: {has_next_chapters}")
                
                # Show first few chapters
                for i, chapter in enumerate(chapters[:3], 1):
                    chapter_title = chapter.get('title', 'Untitled') if isinstance(chapter, dict) else getattr(chapter, 'title', 'Untitled')
                    chapter_id = chapter.get('id') if isinstance(chapter, dict) else getattr(chapter, 'id', 'N/A')
                    print(f"    [{i}] {chapter_title} (ID: {chapter_id})")
            else:
                result.chapters_error = "No chapters found"
                print(f"  ❌ No chapters found")
                
        except asyncio.TimeoutError:
            result.chapters_error = "Chapters timeout"
            print(f"  ⏰ Timeout while fetching chapters")
        except Exception as e:
            result.chapters_error = f"Chapters error: {str(e)}"
            print(f"  ❌ Error fetching chapters: {str(e)}")
        
        print()
        
        # Test 4: Download test (get pages)
        print("📄 Step 4: Testing Page Extraction")
        print("-" * 40)
        
        if result.chapters_success and chapters:
            try:
                test_chapter = chapters[0]
                
                # Extract chapter ID
                if hasattr(test_chapter, 'id'):
                    chapter_id = test_chapter.id
                    chapter_title = getattr(test_chapter, 'title', 'Untitled')
                else:
                    chapter_id = test_chapter.get('id')
                    chapter_title = test_chapter.get('title', 'Untitled')
                
                print(f"  Testing chapter: '{chapter_title}'")
                print(f"  Chapter ID: {chapter_id}")
                print(f"  Manga ID: {result.test_manga_id}")
                
                if chapter_id:
                    print(f"  Fetching pages...")
                    pages_task = asyncio.create_task(provider.get_pages(result.test_manga_id, chapter_id))
                    pages = await asyncio.wait_for(pages_task, timeout=10.0)
                    
                    if pages and len(pages) > 0:
                        result.download_success = True
                        result.pages_count = len(pages)
                        print(f"  ✅ Pages extracted successfully")
                        print(f"  📊 Pages found: {len(pages)}")
                        print(f"  🔗 First page: {pages[0][:80]}...")
                        if len(pages) > 1:
                            print(f"  🔗 Last page: {pages[-1][:80]}...")
                    else:
                        result.download_error = "No pages found for chapter"
                        print(f"  ❌ No pages returned")
                        print(f"  📊 Pages object: {pages}")
                        print(f"  🔍 Pages type: {type(pages)}")
                else:
                    result.download_error = "No chapter ID found"
                    print(f"  ❌ No chapter ID available")
                    
            except asyncio.TimeoutError:
                result.download_error = "Pages timeout"
                print(f"  ⏰ Timeout while fetching pages")
            except Exception as e:
                result.download_error = f"Pages error: {str(e)}"
                print(f"  ❌ Error fetching pages: {str(e)}")
                traceback.print_exc()
        else:
            result.download_error = "No chapters available for download test"
            print(f"  ❌ Cannot test pages - no chapters available")
    
    except Exception as e:
        result.search_error = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected error testing {provider_name}: {e}")
        traceback.print_exc()
    
    finally:
        result.finish_test()
    
    return result

async def main():
    """Main test function."""
    print(f"🧪 Individual Provider Test: {PROVIDER_NAME}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        # Get test user
        result = await db.execute(select(User).where(User.email == "futs69@gmail.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Test user 'futs69@gmail.com' not found")
            print("Please ensure the test user exists in the database")
            return
        
        print(f"✅ Test user found: {user.email}")
        print()
        
        # Test the provider
        result = await test_provider_detailed(PROVIDER_NAME, db, user.id)
        
        # Print summary
        print()
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Provider: {result.provider_name}")
        print(f"Duration: {result.test_duration:.1f}s")
        print(f"Search: {'✅ Success' if result.search_success else '❌ Failed'} ({result.search_results_count} results)")
        print(f"Details: {'✅ Success' if result.manga_details_success else '❌ Failed'}")
        print(f"Chapters: {'✅ Success' if result.chapters_success else '❌ Failed'} ({result.chapters_count} chapters)")
        print(f"Pages: {'✅ Success' if result.download_success else '❌ Failed'} ({result.pages_count} pages)")
        
        # Show errors if any
        if result.search_error:
            print(f"Search Error: {result.search_error}")
        if result.manga_details_error:
            print(f"Details Error: {result.manga_details_error}")
        if result.chapters_error:
            print(f"Chapters Error: {result.chapters_error}")
        if result.download_error:
            print(f"Download Error: {result.download_error}")
        
        # Overall status
        status = result.get_overall_status()
        if status == "FULLY_WORKING":
            print("🎉 OVERALL: FULLY WORKING")
        elif status == "PARTIALLY_WORKING_NO_PAGES":
            print("⚠️  OVERALL: PARTIALLY WORKING (no pages)")
        elif status == "PARTIALLY_WORKING_SEARCH_ONLY":
            print("⚠️  OVERALL: PARTIALLY WORKING (search only)")
        else:
            print("❌ OVERALL: NOT WORKING")
        
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Save results
        print("💾 Saving test results...")
        save_test_result(result)
        save_summary_result(result)
        generate_markdown_report()
        print("✅ Results saved successfully!")

if __name__ == "__main__":
    asyncio.run(main())
'''

def complete_test_scripts():
    """Complete incomplete test scripts by adding missing functions."""
    test_dir = Path(__file__).parent / 'individual_provider_tests'
    
    # Files that need completion (generated by template but missing test functions)
    incomplete_files = [
        'test_truemanga.py',
        'test_readcomicsonlineli.py', 
        'test_mangafoxfun.py',
        'test_mangaherefun.py'
    ]
    
    print("🔧 Completing Phase 4 test scripts...")
    print("=" * 50)
    
    for filename in incomplete_files:
        filepath = test_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  Skipping {filename} - file not found")
            continue
        
        # Read current content
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check if already complete (has main function)
        if 'async def main():' in content:
            print(f"✅ {filename} - already complete")
            continue
        
        # Append test functions
        complete_content = content + TEST_FUNCTIONS
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(complete_content)
        
        print(f"✅ Completed {filename}")
    
    print()
    print("📋 All Phase 4 test scripts are now complete!")

if __name__ == "__main__":
    complete_test_scripts()
