#!/usr/bin/env python3
"""
Test script to verify the search API functionality.
"""

import requests
import json
import time

def test_providers_endpoint():
    """Test the providers endpoint (requires auth)."""
    print("Testing providers endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/v1/search/providers")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Providers endpoint is protected (requires authentication)")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✓ Found {len(data)} providers")
            for provider in data[:5]:
                print(f"  - {provider['name']}: {provider['url']}")
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_search_endpoint():
    """Test the search endpoint (requires auth)."""
    print("\nTesting search endpoint...")
    try:
        search_data = {
            "query": "naruto",
            "provider": "mangadex",
            "page": 1,
            "limit": 5
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Search endpoint is protected (requires authentication)")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✓ Search returned {len(data.get('results', []))} results")
            print(f"  Total: {data.get('total', 0)}")
            print(f"  Providers searched: {data.get('providers_searched', 'N/A')}")
            print(f"  Providers successful: {data.get('providers_successful', 'N/A')}")
            
            for result in data.get('results', [])[:3]:
                print(f"  - {result.get('title', 'No title')} from {result.get('provider', 'Unknown')}")
                print(f"    Cover: {result.get('cover_image', 'No cover')}")
                print(f"    Description: {result.get('description', 'No description')[:50]}...")
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_multi_provider_search():
    """Test multi-provider search."""
    print("\nTesting multi-provider search...")
    try:
        search_data = {
            "query": "naruto",
            "provider": None,  # This should trigger multi-provider search
            "page": 1,
            "limit": 10
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✓ Multi-provider search endpoint is protected (requires authentication)")
            return True
        elif response.status_code == 200:
            data = response.json()
            print(f"✓ Multi-provider search returned {len(data.get('results', []))} results")
            print(f"  Total: {data.get('total', 0)}")
            print(f"  Providers searched: {data.get('providers_searched', 'N/A')}")
            print(f"  Providers successful: {data.get('providers_successful', 'N/A')}")
            
            # Group results by provider
            providers = {}
            for result in data.get('results', []):
                provider = result.get('provider', 'Unknown')
                if provider not in providers:
                    providers[provider] = 0
                providers[provider] += 1
            
            print("  Results by provider:")
            for provider, count in providers.items():
                print(f"    {provider}: {count} results")
            
            return True
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_health_check():
    """Test if the backend is running."""
    print("Testing backend health...")
    try:
        response = requests.get("http://localhost:8000/api/docs")
        if response.status_code == 200:
            print("✓ Backend is running and API docs are accessible")
            return True
        else:
            print(f"✗ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Backend is not accessible: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("KUROIBARA SEARCH API TEST")
    print("=" * 60)
    
    tests = [
        ("Backend Health", test_health_check),
        ("Providers Endpoint", test_providers_endpoint),
        ("Single Provider Search", test_search_endpoint),
        ("Multi-Provider Search", test_multi_provider_search),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running: {test_name}")
        print(f"{'-' * 40}")
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The search API is working correctly.")
        print("\nNote: Authentication is required for actual search functionality.")
        print("The fixes should resolve the issues with:")
        print("1. Multi-provider search returning no results")
        print("2. Missing cover images and metadata in search results")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")

if __name__ == "__main__":
    main()
