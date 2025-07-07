#!/usr/bin/env python3
"""
Test script to verify the multi-provider search improvements.
"""

import requests
import json
import time

def create_test_user_and_login():
    """Create a test user and get auth token."""
    print("Setting up test user...")
    
    # Try to register a test user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ Test user created successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✓ Test user already exists")
        else:
            print(f"Registration response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Registration error: {e}")
    
    # Login to get token
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✓ Successfully logged in")
            return access_token
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_providers_with_auth(token):
    """Test the providers endpoint with authentication."""
    print("\nTesting providers endpoint with auth...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("http://localhost:8000/api/v1/search/providers", headers=headers)
        if response.status_code == 200:
            providers = response.json()
            print(f"✓ Found {len(providers)} providers")
            
            # Show provider breakdown
            priority_providers = []
            generic_providers = []
            
            for provider in providers:
                if provider['name'] in ['MangaDex', 'MangaPlus', 'MangaSee']:
                    priority_providers.append(provider['name'])
                else:
                    generic_providers.append(provider['name'])
            
            print(f"  Priority providers: {len(priority_providers)} - {priority_providers}")
            print(f"  Generic providers: {len(generic_providers)} (showing first 5: {generic_providers[:5]})")
            return True
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_single_provider_search(token, provider_name="mangadex"):
    """Test search with a single provider."""
    print(f"\nTesting single provider search ({provider_name})...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    search_data = {
        "query": "naruto",
        "provider": provider_name,
        "page": 1,
        "limit": 5
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/search", json=search_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✓ {provider_name} returned {len(results)} results")
            
            if results:
                first_result = results[0]
                print(f"  First result: {first_result.get('title', 'No title')}")
                print(f"  Cover image: {'Yes' if first_result.get('cover_image') else 'No'}")
                print(f"  Description: {'Yes' if first_result.get('description') else 'No'}")
                print(f"  Genres: {len(first_result.get('genres', []))} genres")
                print(f"  Authors: {len(first_result.get('authors', []))} authors")
            
            return len(results) > 0
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_multi_provider_search(token):
    """Test multi-provider search."""
    print(f"\nTesting multi-provider search...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    search_data = {
        "query": "naruto",
        "provider": None,  # This triggers multi-provider search
        "page": 1,
        "limit": 20
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/search", json=search_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            providers_searched = data.get('providers_searched', 0)
            providers_successful = data.get('providers_successful', 0)
            
            print(f"✓ Multi-provider search completed")
            print(f"  Total results: {len(results)}")
            print(f"  Providers searched: {providers_searched}")
            print(f"  Providers successful: {providers_successful}")
            print(f"  Success rate: {providers_successful}/{providers_searched} ({100*providers_successful/providers_searched if providers_searched > 0 else 0:.1f}%)")
            
            # Group results by provider
            provider_results = {}
            for result in results:
                provider = result.get('provider', 'Unknown')
                if provider not in provider_results:
                    provider_results[provider] = 0
                provider_results[provider] += 1
            
            print(f"  Results by provider:")
            for provider, count in sorted(provider_results.items()):
                print(f"    {provider}: {count} results")
            
            # Check metadata quality
            results_with_covers = sum(1 for r in results if r.get('cover_image'))
            results_with_descriptions = sum(1 for r in results if r.get('description'))
            results_with_genres = sum(1 for r in results if r.get('genres'))
            
            print(f"  Metadata quality:")
            print(f"    Cover images: {results_with_covers}/{len(results)} ({100*results_with_covers/len(results) if results else 0:.1f}%)")
            print(f"    Descriptions: {results_with_descriptions}/{len(results)} ({100*results_with_descriptions/len(results) if results else 0:.1f}%)")
            print(f"    Genres: {results_with_genres}/{len(results)} ({100*results_with_genres/len(results) if results else 0:.1f}%)")
            
            return len(results) > 1  # We expect multiple results from multiple providers
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("MULTI-PROVIDER SEARCH FIX TEST")
    print("=" * 60)
    
    # Get authentication token
    token = create_test_user_and_login()
    if not token:
        print("✗ Failed to get authentication token. Cannot proceed with tests.")
        return
    
    tests = [
        ("Providers List", lambda: test_providers_with_auth(token)),
        ("Single Provider (MangaDex)", lambda: test_single_provider_search(token, "mangadex")),
        ("Multi-Provider Search", lambda: test_multi_provider_search(token)),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'-' * 50}")
        print(f"Running: {test_name}")
        print(f"{'-' * 50}")
        
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
        print("\n🎉 All tests passed! Multi-provider search improvements are working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. The fixes may need further adjustment.")

if __name__ == "__main__":
    main()
