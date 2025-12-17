#!/usr/bin/env python3
"""Quick test to verify downloads work with new error handling."""
import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"
TEST_USER = {"username": "admin", "password": "admin"}


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
        print("🔐 Logging in...")
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=TEST_USER
        )
        login_data = response.json()
        token = login_data.get("access_token") or login_data.get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Search for a unique manga
        print("🔍 Searching for manga...")
        response = await client.get(
            f"{BASE_URL}/api/v1/providers/MangaPill/search",
            params={"query": "Zombie"},
            headers=headers
        )
        data = response.json()
        print(f"   Response type: {type(data)}, data: {data}")

        # Handle different response formats
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("results", [])
        else:
            results = []

        print(f"   Found {len(results)} results")

        if not results:
            print("❌ No results found")
            return

        # Try to add first result
        manga = results[0]
        print(f"📚 Adding '{manga['title']}' to library...")
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/library",
                json={"manga_id": manga["id"], "provider": "MangaPill"},
                headers=headers
            )
            if response.status_code == 200:
                library_item = response.json()
                print(f"   ✅ Added to library (ID: {library_item['id']})")
                
                # Start download
                print("⬇️  Starting download...")
                response = await client.post(
                    f"{BASE_URL}/api/v1/library/{library_item['id']}/download",
                    headers=headers
                )
                print(f"   ✅ Download queued: {response.json()}")
                
                # Monitor for 30 seconds
                print("⏱️  Monitoring download for 30 seconds...")
                for i in range(6):
                    await asyncio.sleep(5)
                    response = await client.get(
                        f"{BASE_URL}/api/v1/library/downloads",
                        headers=headers
                    )
                    downloads = response.json()
                    if downloads:
                        dl = downloads[0]
                        print(f"   Check {i+1}: {dl.get('status', 'unknown')} - "
                              f"{dl.get('downloaded_chapters', 0)}/{dl.get('total_chapters', 0)} chapters")
                    else:
                        print(f"   Check {i+1}: No active downloads")
                        
            else:
                error = response.json()
                if "already in your library" in str(error):
                    print(f"   ⚠️  Already in library, skipping...")
                else:
                    print(f"   ❌ Failed: {error}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Check backend logs for referer errors
        print("\n📋 Checking for referer errors in backend logs...")
        import subprocess
        result = subprocess.run(
            ["docker", "logs", "kuroibara-backend-1", "--tail", "50"],
            capture_output=True,
            text=True
        )
        referer_errors = [line for line in result.stderr.split('\n') if 'referer' in line.lower()]
        if referer_errors:
            print(f"   ❌ Found {len(referer_errors)} referer errors!")
            for err in referer_errors[:5]:
                print(f"      {err}")
        else:
            print("   ✅ No referer errors found!")


if __name__ == "__main__":
    asyncio.run(main())

