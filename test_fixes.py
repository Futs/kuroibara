#!/usr/bin/env python3
"""
Test script to verify the fixes for Kurobara issues.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_endpoint(endpoint, method="GET", data=None, headers=None, expected_status=None):
    """Test an API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        print(f"{method} {endpoint}: {response.status_code}")
        
        if expected_status and response.status_code != expected_status:
            print(f"  Expected {expected_status}, got {response.status_code}")
            if response.text:
                print(f"  Response: {response.text[:200]}")
        
        return response
    
    except Exception as e:
        print(f"{method} {endpoint}: ERROR - {e}")
        return None

def main():
    """Test the main fixes."""
    print("Testing Kurobara API fixes...")
    print("=" * 50)
    
    # Test 1: Check if genres endpoint exists (was missing)
    print("\n1. Testing genres endpoint (was returning 404):")
    test_endpoint("/v1/search/genres", expected_status=401)  # Should require auth
    
    # Test 2: Check if docs are accessible
    print("\n2. Testing API docs:")
    response = test_endpoint("/docs", expected_status=200)
    
    # Test 3: Check if providers endpoint works
    print("\n3. Testing providers endpoint:")
    test_endpoint("/v1/search/providers", expected_status=401)  # Should require auth
    
    # Test 4: Check if reading lists endpoint exists
    print("\n4. Testing reading lists endpoint:")
    test_endpoint("/v1/reading-lists", expected_status=401)  # Should require auth
    
    # Test 5: Check if library endpoint exists
    print("\n5. Testing library endpoint:")
    test_endpoint("/v1/library", expected_status=401)  # Should require auth
    
    # Test 6: Check if manga from external endpoint exists
    print("\n6. Testing manga from external endpoint:")
    test_endpoint("/v1/manga/from-external", method="POST", expected_status=401)  # Should require auth
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- All endpoints should return 401 (Unauthorized) when not authenticated")
    print("- This indicates the endpoints exist and are properly protected")
    print("- The frontend should handle authentication and make these calls work")
    print("\nTo test with authentication, you need to:")
    print("1. Register/login through the frontend")
    print("2. Use the JWT token in the Authorization header")

if __name__ == "__main__":
    main()
