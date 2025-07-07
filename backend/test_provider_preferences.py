#!/usr/bin/env python3
"""
Test script to reproduce the provider preferences issue.
"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.user_provider_preference import UserProviderPreference
from app.schemas.user_provider_preference import UserProviderPreferenceBulkUpdate, UserProviderPreferenceBase
from app.api.api_v1.endpoints.user_provider_preferences import bulk_update_provider_preferences
from app.core.providers.registry import provider_registry


async def test_bulk_update():
    """Test the bulk update functionality."""
    print("Testing provider preferences bulk update...")
    
    # Get available providers
    providers = provider_registry.get_provider_info()
    print(f"Found {len(providers)} providers")
    
    # Create test data - disable a few providers
    test_preferences = []
    for i, provider in enumerate(providers[:5]):  # Test with first 5 providers
        is_enabled = i % 2 == 0  # Alternate enabled/disabled
        test_preferences.append(UserProviderPreferenceBase(
            provider_id=provider["id"],
            is_enabled=is_enabled,
            is_favorite=False,
            priority_order=None
        ))
        print(f"  {provider['id']}: enabled={is_enabled}")
    
    bulk_update = UserProviderPreferenceBulkUpdate(preferences=test_preferences)
    
    # Create a test user (we'll need to get an existing user from the database)
    async with AsyncSessionLocal() as db:
        # Get the first user from the database
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("No users found in database. Please create a user first.")
            return
        
        print(f"Testing with user: {user.username}")
        
        try:
            # Test the bulk update function (first time - should create)
            result = await bulk_update_provider_preferences(bulk_update, user, db)
            print("First bulk update successful!")
            print(f"Result: {result}")

            # Test again with different values (should update existing)
            print("\nTesting update of existing preferences...")
            updated_preferences = []
            for i, provider in enumerate(providers[:5]):
                is_enabled = i % 2 == 1  # Flip the enabled state
                updated_preferences.append(UserProviderPreferenceBase(
                    provider_id=provider["id"],
                    is_enabled=is_enabled,
                    is_favorite=True,  # Make them favorites this time
                    priority_order=i + 1
                ))
                print(f"  {provider['id']}: enabled={is_enabled}, favorite=True, priority={i+1}")

            bulk_update2 = UserProviderPreferenceBulkUpdate(preferences=updated_preferences)
            result2 = await bulk_update_provider_preferences(bulk_update2, user, db)
            print("Second bulk update successful!")
            print(f"Result: {result2}")

        except Exception as e:
            print(f"Bulk update failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bulk_update())
