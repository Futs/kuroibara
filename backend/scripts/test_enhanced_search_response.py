#!/usr/bin/env python3
"""Test what the enhanced search endpoint returns."""

import asyncio
import httpx


async def test_enhanced_search():
    """Test enhanced search response."""
    print("🔍 Testing Enhanced Search Response\n")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=180.0) as client:
        # Login
        print("\n1️⃣  Logging in...")
        login_resp = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"username": "testuser_provider", "password": "password123"},
        )
        login_data = login_resp.json()
        token = login_data.get("access_token") or login_data.get("token")
        if not token:
            print(f"❌ No token in response: {login_data}")
            return
        print(f"✅ Logged in")

        # Search
        print("\n2️⃣  Searching for 'One Piece' with provider matching...")
        search_resp = await client.post(
            "http://localhost:8000/api/v1/search/enhanced",
            params={"query": "One Piece", "limit": 5, "include_provider_matches": True},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120.0,
        )

        if search_resp.status_code == 200:
            data = search_resp.json()
            results = data.get("results", [])
            print(f"✅ Got {len(results)} results\n")

            for i, result in enumerate(results, 1):
                print(f"Result #{i}:")
                print(f"  Title: {result.get('title')}")
                print(f"  Source: {result.get('source_indexer')}")
                print(f"  Source ID: {result.get('source_id')}")

                # Check extra field
                extra = result.get("extra", {})
                provider_matches = extra.get("provider_matches", [])
                print(f"  Provider Matches (from extra): {len(provider_matches)}")
                if provider_matches:
                    for j, match in enumerate(provider_matches, 1):
                        print(f"    Match #{j}:")
                        print(f"      Provider: {match.get('provider')}")
                        print(f"      Title: {match.get('title')}")
                        print(f"      Confidence: {match.get('confidence'):.3f}")
                else:
                    print(f"    ⚠️  No provider matches")
                print()
        else:
            print(f"❌ Search failed: {search_resp.status_code}")
            print(f"Error: {search_resp.text[:500]}")


if __name__ == "__main__":
    asyncio.run(test_enhanced_search())

