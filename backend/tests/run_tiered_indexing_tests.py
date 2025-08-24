#!/usr/bin/env python3
"""Test runner for tiered indexing system tests."""

import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run all tiered indexing tests with proper configuration."""
    
    # Get the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("🧪 Running Tiered Indexing Test Suite")
    print("=" * 60)
    
    # Test files to run
    test_files = [
        "tests/test_tiered_indexing.py",
        "tests/test_enhanced_tiered_search.py"
    ]
    
    # Test categories
    test_categories = {
        "Unit Tests": [
            "tests/test_tiered_indexing.py::TestUniversalMetadata",
            "tests/test_tiered_indexing.py::TestMangaUpdatesIndexer",
            "tests/test_tiered_indexing.py::TestMadaraDexIndexer", 
            "tests/test_tiered_indexing.py::TestMangaDexIndexer",
            "tests/test_tiered_indexing.py::TestTieredSearchService",
        ],
        "Integration Tests": [
            "tests/test_tiered_indexing.py::TestIntegrationScenarios",
            "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService",
            "tests/test_enhanced_tiered_search.py::TestDatabaseIntegration",
        ],
        "Live API Tests": [
            "tests/test_tiered_indexing.py::TestLiveIndexerConnections",
        ],
        "Error Handling Tests": [
            "tests/test_enhanced_tiered_search.py::TestErrorHandling",
        ]
    }
    
    # Run tests by category
    total_passed = 0
    total_failed = 0
    
    for category, tests in test_categories.items():
        print(f"\n📋 Running {category}")
        print("-" * 40)
        
        for test in tests:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    test, 
                    "-v", 
                    "--tb=short",
                    "--disable-warnings"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"  ✅ {test.split('::')[-1]}")
                    total_passed += 1
                else:
                    print(f"  ❌ {test.split('::')[-1]}")
                    if result.stdout:
                        print(f"     Output: {result.stdout.strip()}")
                    if result.stderr:
                        print(f"     Error: {result.stderr.strip()}")
                    total_failed += 1
                    
            except subprocess.TimeoutExpired:
                print(f"  ⏰ {test.split('::')[-1]} (timeout)")
                total_failed += 1
            except Exception as e:
                print(f"  💥 {test.split('::')[-1]} (exception: {e})")
                total_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📈 Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%" if (total_passed + total_failed) > 0 else "No tests run")
    
    if total_failed == 0:
        print("\n🎉 All tests passed! Tiered indexing system is ready.")
        return True
    else:
        print(f"\n⚠️ {total_failed} tests failed. Review the output above.")
        return False


def run_quick_validation():
    """Run a quick validation of the tiered indexing system."""
    
    print("🚀 Quick Tiered Indexing Validation")
    print("=" * 50)
    
    # Quick tests to validate the system is working
    quick_tests = [
        "tests/test_tiered_indexing.py::TestUniversalMetadata::test_universal_metadata_creation",
        "tests/test_tiered_indexing.py::TestMangaDexIndexer::test_indexer_initialization",
        "tests/test_tiered_indexing.py::TestTieredSearchService::test_service_initialization",
        "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService::test_metadata_to_entry_conversion",
    ]
    
    passed = 0
    failed = 0
    
    for test in quick_tests:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test, 
                "-v", 
                "--tb=line",
                "--disable-warnings"
            ], capture_output=True, text=True, timeout=30)
            
            test_name = test.split("::")[-1]
            if result.returncode == 0:
                print(f"  ✅ {test_name}")
                passed += 1
            else:
                print(f"  ❌ {test_name}")
                failed += 1
                
        except Exception as e:
            print(f"  💥 {test.split('::')[-1]} (error: {e})")
            failed += 1
    
    print(f"\n📊 Quick Validation: {passed}/{passed + failed} tests passed")
    
    if failed == 0:
        print("✅ Basic validation successful!")
        return True
    else:
        print("❌ Basic validation failed. Run full tests for details.")
        return False


def run_live_api_tests():
    """Run tests that connect to live APIs."""
    
    print("🌐 Running Live API Tests")
    print("=" * 40)
    print("⚠️ These tests connect to real APIs and may fail if services are down.")
    
    live_tests = [
        "tests/test_tiered_indexing.py::TestLiveIndexerConnections::test_mangadx_live_connection",
        "tests/test_tiered_indexing.py::TestLiveIndexerConnections::test_madaradx_live_connection",
    ]
    
    for test in live_tests:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test, 
                "-v", 
                "--tb=short",
                "-s"  # Don't capture output for live tests
            ], timeout=60)
            
            test_name = test.split("::")[-1]
            if result.returncode == 0:
                print(f"✅ {test_name} - API is accessible")
            else:
                print(f"⚠️ {test_name} - API may be down (this is normal)")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test.split('::')[-1]} - Connection timeout")
        except Exception as e:
            print(f"💥 {test.split('::')[-1]} - Error: {e}")


def main():
    """Main test runner."""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            success = run_quick_validation()
        elif command == "live":
            run_live_api_tests()
            success = True
        elif command == "full":
            success = run_tests()
        else:
            print("Usage: python run_tiered_indexing_tests.py [quick|live|full]")
            print("  quick - Run basic validation tests")
            print("  live  - Run live API connection tests")
            print("  full  - Run complete test suite")
            return
    else:
        # Default to quick validation
        success = run_quick_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
