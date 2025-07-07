#!/usr/bin/env python3
"""
Test script to call the provider preferences API endpoint directly.
"""
import asyncio
import aiohttp
import json


async def test_provider_preferences_api():
    """Test the provider preferences API endpoint."""
    base_url = "http://localhost:8000"
    
    # First, we need to authenticate to get a token
    # Let's try to register/login a test user
    async with aiohttp.ClientSession() as session:
        # Try to register a new test user with a unique name
        import time
        unique_username = f"testuser_{int(time.time())}"
        register_data = {
            "username": unique_username,
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }

        print(f"Attempting to register test user: {unique_username}")
        async with session.post(f"{base_url}/api/v1/auth/register", json=register_data) as resp:
            if resp.status == 200:
                print("User registered successfully")
            else:
                print(f"Registration failed: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return

        # Login to get token
        login_data = {
            "username": unique_username,
            "password": "testpassword123"
        }

        print("Logging in...")
        async with session.post(f"{base_url}/api/v1/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return
            
            login_response = await resp.json()
            token = login_response["access_token"]
            print("Login successful!")
        
        # Set up headers with token
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test the bulk update endpoint
        print("\nTesting bulk update endpoint...")
        
        # Create test data - disable some providers
        test_data = {
            "preferences": [
                {
                    "provider_id": "anigliscans",
                    "is_enabled": False,  # Disable this provider
                    "is_favorite": False,
                    "priority_order": None
                },
                {
                    "provider_id": "anshscans", 
                    "is_enabled": True,
                    "is_favorite": True,
                    "priority_order": 1
                },
                {
                    "provider_id": "arcanescans",
                    "is_enabled": False,  # Disable this provider
                    "is_favorite": False,
                    "priority_order": None
                }
            ]
        }
        
        print(f"Sending bulk update request with {len(test_data['preferences'])} preferences...")
        for pref in test_data['preferences']:
            print(f"  {pref['provider_id']}: enabled={pref['is_enabled']}")
        
        async with session.post(
            f"{base_url}/api/v1/users/me/provider-preferences/bulk",
            json=test_data,
            headers=headers
        ) as resp:
            print(f"Response status: {resp.status}")
            response_text = await resp.text()
            print(f"Response: {response_text}")
            
            if resp.status == 200:
                print("✅ Bulk update successful!")

                # Test updating the same preferences again
                print("\nTesting update of existing preferences...")
                updated_data = {
                    "preferences": [
                        {
                            "provider_id": "anigliscans",
                            "is_enabled": True,  # Re-enable this provider
                            "is_favorite": True,
                            "priority_order": 1
                        },
                        {
                            "provider_id": "anshscans",
                            "is_enabled": False,  # Disable this one
                            "is_favorite": False,
                            "priority_order": None
                        },
                        {
                            "provider_id": "arcanescans",
                            "is_enabled": True,  # Re-enable this provider
                            "is_favorite": True,
                            "priority_order": 2
                        }
                    ]
                }

                print("Sending second bulk update request...")
                for pref in updated_data['preferences']:
                    print(f"  {pref['provider_id']}: enabled={pref['is_enabled']}")

                async with session.post(
                    f"{base_url}/api/v1/users/me/provider-preferences/bulk",
                    json=updated_data,
                    headers=headers
                ) as resp2:
                    print(f"Second response status: {resp2.status}")
                    response_text2 = await resp2.text()
                    print(f"Second response: {response_text2}")

                    if resp2.status == 200:
                        print("✅ Second bulk update successful!")
                    else:
                        print("❌ Second bulk update failed!")
            else:
                print("❌ Bulk update failed!")


if __name__ == "__main__":
    asyncio.run(test_provider_preferences_api())
