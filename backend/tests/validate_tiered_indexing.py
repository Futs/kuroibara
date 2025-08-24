#!/usr/bin/env python3
"""Comprehensive validation script for the tiered indexing system."""

import sys
import subprocess
import os
from pathlib import Path


def run_core_tests():
    """Run the core working tests for tiered indexing."""
    
    print("🧪 Tiered Indexing Core Validation")
    print("=" * 60)
    
    # Core working tests
    core_tests = [
        # Basic functionality tests
        "tests/test_tiered_indexing.py::TestUniversalMetadata::test_universal_metadata_creation",
        "tests/test_tiered_indexing.py::TestUniversalMetadata::test_universal_metadata_nsfw_detection",
        
        # Indexer initialization tests
        "tests/test_tiered_indexing.py::TestMangaUpdatesIndexer::test_indexer_initialization",
        "tests/test_tiered_indexing.py::TestMadaraDexIndexer::test_indexer_initialization",
        "tests/test_tiered_indexing.py::TestMangaDexIndexer::test_indexer_initialization",
        
        # Service tests
        "tests/test_tiered_indexing.py::TestTieredSearchService::test_service_initialization",
        "tests/test_tiered_indexing.py::TestTieredSearchService::test_tiered_search_with_fallback",
        "tests/test_tiered_indexing.py::TestTieredSearchService::test_health_monitoring",
        "tests/test_tiered_indexing.py::TestTieredSearchService::test_deduplication_logic",
        "tests/test_tiered_indexing.py::TestTieredSearchService::test_result_sorting",
        
        # Enhanced service tests
        "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService::test_metadata_to_entry_conversion",
        "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService::test_data_completeness_calculation",
        "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService::test_entry_update_logic",
        "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService::test_search_result_conversion",
        "tests/test_enhanced_tiered_search.py::TestEnhancedTieredSearchService::test_confidence_scoring_logic",
        
        # Integration scenario tests
        "tests/test_tiered_indexing.py::TestIntegrationScenarios::test_nsfw_content_detection",
        "tests/test_tiered_indexing.py::TestIntegrationScenarios::test_confidence_scoring_scenarios",
        
        # Error handling tests
        "tests/test_enhanced_tiered_search.py::TestErrorHandling::test_invalid_metadata_handling",
    ]
    
    passed = 0
    failed = 0
    
    for test in core_tests:
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
                if result.stdout and "FAILED" in result.stdout:
                    # Extract failure reason
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "FAILED" in line or "AssertionError" in line or "AttributeError" in line:
                            print(f"     {line.strip()}")
                            break
                failed += 1
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {test.split('::')[-1]} (timeout)")
            failed += 1
        except Exception as e:
            print(f"  💥 {test.split('::')[-1]} (error: {e})")
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 Core Test Results")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "No tests run")
    
    return failed == 0


def run_live_connection_tests():
    """Run live connection tests (may fail if APIs are down)."""
    
    print("\n🌐 Live API Connection Tests")
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
                "--tb=line",
                "--disable-warnings"
            ], capture_output=True, text=True, timeout=30)
            
            test_name = test.split("::")[-1]
            if result.returncode == 0:
                print(f"  ✅ {test_name} - API is accessible")
            else:
                print(f"  ⚠️ {test_name} - API may be down (this is normal)")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {test.split('::')[-1]} - Connection timeout")
        except Exception as e:
            print(f"  💥 {test.split('::')[-1]} - Error: {e}")


def run_import_validation():
    """Validate that all required modules can be imported."""
    
    print("\n📦 Import Validation")
    print("=" * 30)
    
    imports_to_test = [
        ("app.core.services.tiered_indexing", "UniversalMetadata"),
        ("app.core.services.tiered_indexing", "TieredSearchService"),
        ("app.core.services.tiered_indexing", "MangaUpdatesIndexer"),
        ("app.core.services.tiered_indexing", "MadaraDexIndexer"),
        ("app.core.services.tiered_indexing", "MangaDexIndexer"),
        ("app.core.services.enhanced_tiered_search", "EnhancedTieredSearchService"),
        ("app.models.mangaupdates", "UniversalMangaEntry"),
        ("app.models.mangaupdates", "UniversalMangaMapping"),
        ("app.models.mangaupdates", "CrossIndexerReference"),
    ]
    
    passed = 0
    failed = 0
    
    for module, class_name in imports_to_test:
        try:
            result = subprocess.run([
                sys.executable, "-c", 
                f"from {module} import {class_name}; print('✅ {module}.{class_name}')"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"  ✅ {module}.{class_name}")
                passed += 1
            else:
                print(f"  ❌ {module}.{class_name}")
                if result.stderr:
                    print(f"     Error: {result.stderr.strip()}")
                failed += 1
                
        except Exception as e:
            print(f"  💥 {module}.{class_name} - Error: {e}")
            failed += 1
    
    print(f"\n📊 Import Results: {passed}/{passed + failed} successful")
    return failed == 0


def run_database_validation():
    """Validate database tables exist using Python."""

    print("\n🗄️ Database Validation")
    print("=" * 30)

    # Use Python to check database tables
    validation_script = '''
import asyncio
from app.models.mangaupdates import UniversalMangaEntry, UniversalMangaMapping, CrossIndexerReference
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check_tables():
    async with AsyncSessionLocal() as session:
        tables = ["universal_manga_entries", "universal_manga_mappings", "cross_indexer_references"]
        results = []

        for table in tables:
            try:
                result = await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                results.append((table, True))
                print(f"✅ Table '{table}' exists and accessible")
            except Exception as e:
                results.append((table, False))
                print(f"❌ Table '{table}' error: {str(e)[:50]}...")

        return results

if __name__ == "__main__":
    results = asyncio.run(check_tables())
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"📊 Database Results: {passed}/{total} tables accessible")
    exit(0 if passed == total else 1)
'''

    try:
        result = subprocess.run([
            sys.executable, "-c", validation_script
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(result.stdout.strip())
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"  💥 Error running database validation: {e}")
        return False


def main():
    """Main validation runner."""
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print("🚀 Comprehensive Tiered Indexing Validation")
    print("=" * 70)
    
    # Run all validation steps
    results = []
    
    # 1. Import validation
    import_success = run_import_validation()
    results.append(("Import Validation", import_success))
    
    # 2. Database validation
    db_success = run_database_validation()
    results.append(("Database Validation", db_success))
    
    # 3. Core tests
    core_success = run_core_tests()
    results.append(("Core Tests", core_success))
    
    # 4. Live connection tests (optional)
    run_live_connection_tests()
    results.append(("Live API Tests", "Optional"))
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 Final Validation Summary")
    print("=" * 70)
    
    for test_name, success in results:
        if success == "Optional":
            print(f"  ℹ️ {test_name}: Optional (may fail if APIs are down)")
        elif success:
            print(f"  ✅ {test_name}: PASSED")
        else:
            print(f"  ❌ {test_name}: FAILED")
    
    # Overall status
    critical_tests = [r for r in results if r[1] != "Optional"]
    all_critical_passed = all(result[1] for result in critical_tests)
    
    if all_critical_passed:
        print("\n🎉 All critical validations passed!")
        print("✅ Tiered indexing system is ready for use.")
        return True
    else:
        print("\n⚠️ Some critical validations failed.")
        print("❌ Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
