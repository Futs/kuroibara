#!/usr/bin/env python3
"""
Test script for external integrations functionality.
This script tests the basic functionality without requiring real API credentials.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core.services.integrations import AnilistClient, MyAnimeListClient
from app.models.external_integration import IntegrationType


async def test_client_initialization():
    """Test that the integration clients can be initialized."""
    print("Testing client initialization...")

    try:
        anilist_client = AnilistClient()
        mal_client = MyAnimeListClient()

        assert anilist_client.integration_type == IntegrationType.ANILIST
        assert mal_client.integration_type == IntegrationType.MYANIMELIST

        print("✓ Clients initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False


async def test_status_mapping():
    """Test status mapping functions."""
    print("Testing status mapping...")

    try:
        anilist_client = AnilistClient()
        mal_client = MyAnimeListClient()

        # Test Anilist status mapping
        assert anilist_client.map_status_to_external("reading") == "CURRENT"
        assert anilist_client.map_status_to_external("completed") == "COMPLETED"
        assert anilist_client.map_status_from_external("CURRENT") == "reading"
        assert anilist_client.map_status_from_external("COMPLETED") == "completed"

        # Test MyAnimeList status mapping
        assert mal_client.map_status_to_mal("reading") == "reading"
        assert mal_client.map_status_to_mal("completed") == "completed"
        assert mal_client.map_status_from_mal("reading") == "reading"
        assert mal_client.map_status_from_mal("completed") == "completed"

        print("✓ Status mapping works correctly")
        return True
    except Exception as e:
        print(f"✗ Status mapping failed: {e}")
        return False


async def test_api_endpoints_import():
    """Test that API endpoints can be imported."""
    print("Testing API endpoints import...")

    try:
        from app.api.api_v1.endpoints.integrations import router
        from app.schemas.external_integration import (
            IntegrationSettings,
            AnilistAuthRequest,
            MyAnimeListAuthRequest,
            SyncRequest,
        )

        print("✓ API endpoints and schemas imported successfully")
        return True
    except Exception as e:
        print(f"✗ API endpoints import failed: {e}")
        return False


async def test_models_import():
    """Test that models can be imported."""
    print("Testing models import...")

    try:
        from app.models.external_integration import (
            ExternalIntegration,
            ExternalMangaMapping,
            IntegrationType,
            SyncStatus,
        )

        # Test enum values
        assert IntegrationType.ANILIST == "anilist"
        assert IntegrationType.MYANIMELIST == "myanimelist"
        assert SyncStatus.PENDING == "pending"
        assert SyncStatus.SUCCESS == "success"

        print("✓ Models and enums imported successfully")
        return True
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False


async def test_sync_service_import():
    """Test that sync service can be imported."""
    print("Testing sync service import...")

    try:
        from app.core.services.integrations.sync_service import SyncService

        sync_service = SyncService()
        assert sync_service.clients is not None
        assert IntegrationType.ANILIST in sync_service.clients
        assert IntegrationType.MYANIMELIST in sync_service.clients

        print("✓ Sync service imported and initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Sync service import failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing External Integrations Implementation")
    print("=" * 50)

    tests = [
        test_client_initialization,
        test_status_mapping,
        test_api_endpoints_import,
        test_models_import,
        test_sync_service_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if await test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Integration implementation is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
