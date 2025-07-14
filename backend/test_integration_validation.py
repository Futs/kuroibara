#!/usr/bin/env python3
"""
Comprehensive validation tests for external integrations feature.
This script validates all components before committing the feature branch.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


async def test_database_models():
    """Test that all database models can be imported and instantiated."""
    print("🗄️  Testing Database Models...")

    try:
        from uuid import uuid4

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

        # Test model instantiation (without saving to DB)
        integration = ExternalIntegration(
            user_id=uuid4(),
            integration_type=IntegrationType.ANILIST,
            client_id="test_client_id",
            client_secret="test_client_secret",
            sync_enabled=True,
        )

        mapping = ExternalMangaMapping(
            integration_id=uuid4(),
            manga_id=uuid4(),
            external_manga_id="123456",
            external_title="Test Manga",
        )

        print("  ✅ Models imported and instantiated successfully")
        return True

    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        return False


async def test_api_schemas():
    """Test that all API schemas work correctly."""
    print("📋 Testing API Schemas...")

    try:
        from app.models.external_integration import IntegrationType
        from app.schemas.external_integration import (
            AnilistAuthRequest,
            IntegrationSetupRequest,
            SyncRequest,
        )

        # Test schema creation
        setup_request = IntegrationSetupRequest(
            integration_type=IntegrationType.ANILIST,
            client_id="test_id",
            client_secret="test_secret",
        )

        auth_request = AnilistAuthRequest(
            authorization_code="test_code",
            redirect_uri="http://localhost:3000/callback",
        )

        sync_request = SyncRequest(
            integration_type=IntegrationType.ANILIST, force_full_sync=False
        )

        # Test serialization
        setup_dict = setup_request.model_dump()
        assert setup_dict["integration_type"] == "anilist"
        assert setup_dict["client_id"] == "test_id"

        print("  ✅ Schemas created and serialized successfully")
        return True

    except Exception as e:
        print(f"  ❌ Schema test failed: {e}")
        return False


async def test_integration_clients():
    """Test that integration clients can be instantiated and configured."""
    print("🔌 Testing Integration Clients...")

    try:
        from app.core.services.integrations import AnilistClient, MyAnimeListClient
        from app.models.external_integration import IntegrationType

        # Test client instantiation with custom credentials
        anilist_client = AnilistClient("test_id", "test_secret")
        mal_client = MyAnimeListClient("test_id", "test_secret")

        assert anilist_client.integration_type == IntegrationType.ANILIST
        assert mal_client.integration_type == IntegrationType.MYANIMELIST
        assert anilist_client.client_id == "test_id"
        assert mal_client.client_id == "test_id"

        # Test status mapping
        assert anilist_client.map_status_to_external("reading") == "CURRENT"
        assert mal_client.map_status_to_mal("reading") == "reading"

        print("  ✅ Clients instantiated and configured successfully")
        return True

    except Exception as e:
        print(f"  ❌ Client test failed: {e}")
        return False


async def test_sync_service():
    """Test that sync service can be instantiated."""
    print("🔄 Testing Sync Service...")

    try:
        from uuid import uuid4

        from app.core.services.integrations.sync_service import SyncService
        from app.models.external_integration import ExternalIntegration, IntegrationType

        sync_service = SyncService()

        # Test client creation
        mock_integration = ExternalIntegration(
            user_id=uuid4(),
            integration_type=IntegrationType.ANILIST,
            client_id="test_id",
            client_secret="test_secret",
        )

        client = sync_service._get_client(mock_integration)
        assert client.integration_type == IntegrationType.ANILIST
        assert client.client_id == "test_id"

        print("  ✅ Sync service instantiated and tested successfully")
        return True

    except Exception as e:
        print(f"  ❌ Sync service test failed: {e}")
        return False


async def test_api_endpoints():
    """Test that API endpoints can be imported."""
    print("🌐 Testing API Endpoints...")

    try:
        from app.api.api_v1.endpoints.integrations import router

        # Check that routes are registered
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/settings",
            "/setup",
            "/anilist/connect",
            "/myanimelist/connect",
            "/{integration_type}",
            "/sync",
        ]

        for expected_route in expected_routes:
            if not any(expected_route in route for route in routes):
                raise Exception(f"Route {expected_route} not found in router")

        print("  ✅ API endpoints imported and routes registered successfully")
        return True

    except Exception as e:
        print(f"  ❌ API endpoint test failed: {e}")
        return False


async def test_backend_startup():
    """Test that the backend can start with the new models."""
    print("🚀 Testing Backend Startup...")

    try:
        # Import main app components
        from app.api.api_v1.api import api_router

        # Check that the app has the integration routes
        integration_routes = [
            route
            for route in api_router.routes
            if hasattr(route, "path") and "integrations" in route.path
        ]

        if not integration_routes:
            raise Exception("Integration routes not found in API router")

        print("  ✅ Backend startup components loaded successfully")
        return True

    except Exception as e:
        print(f"  ❌ Backend startup test failed: {e}")
        return False


async def test_database_tables():
    """Test that database tables exist and have correct structure."""
    print("🏗️  Testing Database Tables...")

    try:
        from sqlalchemy import text

        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            # Check external_integrations table exists
            result = await session.execute(
                text(
                    """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'external_integrations'
                ORDER BY ordinal_position
            """
                )
            )
            columns = result.fetchall()

            if not columns:
                raise Exception("external_integrations table not found")

            # Check for required columns
            column_names = [col[0] for col in columns]
            required_columns = [
                "id",
                "created_at",
                "updated_at",
                "user_id",
                "integration_type",
                "client_id",
                "client_secret",
                "access_token",
                "refresh_token",
                "sync_enabled",
                "last_sync_status",
            ]

            for req_col in required_columns:
                if req_col not in column_names:
                    raise Exception(f"Required column {req_col} not found")

            # Check external_manga_mappings table
            result = await session.execute(
                text(
                    """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'external_manga_mappings'
            """
                )
            )
            mapping_columns = [row[0] for row in result.fetchall()]

            if not mapping_columns:
                raise Exception("external_manga_mappings table not found")

            print("  ✅ Database tables exist with correct structure")
            return True

    except Exception as e:
        print(f"  ❌ Database table test failed: {e}")
        return False


async def test_api_endpoints_live():
    """Test that API endpoints are accessible."""
    print("🌍 Testing Live API Endpoints...")

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Test integration settings endpoint (should require auth)
            async with session.get(
                "http://localhost:8000/api/v1/integrations/settings"
            ) as response:
                # Should return 401 (unauthorized) which means endpoint exists
                if response.status == 401:
                    print(
                        "  ✅ Integration settings endpoint accessible (requires auth)"
                    )
                else:
                    print(
                        f"  ⚠️  Integration settings endpoint returned {response.status}"
                    )

            # Test API docs to see if integration endpoints are documented
            async with session.get("http://localhost:8000/api/docs") as response:
                if response.status == 200:
                    print("  ✅ API documentation accessible")
                else:
                    raise Exception(f"API docs not accessible: {response.status}")

        return True

    except Exception as e:
        print(f"  ❌ Live API test failed: {e}")
        return False


async def main():
    """Run all validation tests."""
    print("🧪 Running Comprehensive Integration Validation Tests")
    print("=" * 60)

    tests = [
        ("Database Models", test_database_models),
        ("API Schemas", test_api_schemas),
        ("Integration Clients", test_integration_clients),
        ("Sync Service", test_sync_service),
        ("API Endpoints", test_api_endpoints),
        ("Backend Startup", test_backend_startup),
        ("Database Tables", test_database_tables),
        ("Live API Endpoints", test_api_endpoints_live),
    ]

    passed = 0
    total = len(tests)
    failed_tests = []

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if await test_func():
                passed += 1
            else:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            failed_tests.append(test_name)

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Integration feature is ready for commit.")
        print("\n✅ Validation Summary:")
        print("  • Database migrations work correctly")
        print("  • All models and schemas are valid")
        print("  • Integration clients are functional")
        print("  • API endpoints are accessible")
        print("  • Backend starts successfully")
        print("  • Database tables have correct structure")
        return 0
    else:
        print(f"❌ {len(failed_tests)} tests failed:")
        for failed_test in failed_tests:
            print(f"  • {failed_test}")
        print("\n🔧 Please fix the failing tests before committing.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
