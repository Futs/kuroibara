#!/usr/bin/env python3
"""Clean the test library before running tests."""
import asyncio
import httpx


async def main():
    base_url = "http://localhost:8000"
    
    # Login as test user
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🔐 Logging in as test user...")
        response = await client.post(
            f"{base_url}/api/v1/auth/login",
            json={"username": "testuser_provider", "password": "password123"},
        )
        
        if response.status_code != 200:
            print("❌ Login failed - test user may not exist yet")
            return
            
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all library items
        print("📚 Fetching library items...")
        response = await client.get(
            f"{base_url}/api/v1/library",
            headers=headers
        )

        data = response.json()
        # Handle different response formats
        if isinstance(data, dict):
            library_items = data.get("items", data.get("results", []))
        else:
            library_items = data

        print(f"   Found {len(library_items)} items in library")
        print(f"   Response type: {type(data)}, sample: {str(data)[:200]}")

        if not library_items:
            print("✅ Library is already empty!")
            return

        # Delete each item
        deleted = 0
        for item in library_items:
            try:
                # Handle different item formats
                item_id = item if isinstance(item, str) else item.get('id')
                item_title = item.get('title', 'Unknown') if isinstance(item, dict) else 'Unknown'

                response = await client.delete(
                    f"{base_url}/api/v1/library/{item_id}",
                    headers=headers
                )
                if response.status_code == 204:
                    deleted += 1
                    print(f"   ✅ Deleted: {item_title}")
            except Exception as e:
                print(f"   ❌ Failed to delete item: {e}")
                
        print(f"\n🎉 Cleaned library: {deleted}/{len(library_items)} items deleted")
        
        # Also clear download history
        print("\n🧹 Clearing download history...")
        try:
            response = await client.delete(
                f"{base_url}/api/v1/library/downloads/history",
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Cleared {result.get('cleared_count', 0)} download history items")
        except Exception as e:
            print(f"   ⚠️  Failed to clear download history: {e}")


if __name__ == "__main__":
    asyncio.run(main())

