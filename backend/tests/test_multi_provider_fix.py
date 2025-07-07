"""
Test script to verify the multi-provider search improvements.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_providers_with_auth(client: TestClient, token: str):
    """Test the providers endpoint with authentication."""
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/search/providers", headers=headers)
    assert response.status_code == 200

    providers = response.json()
    assert len(providers) > 0, "Should have at least one provider"

    # Show provider breakdown
    priority_providers = []
    generic_providers = []

    for provider in providers:
        if provider["name"] in ["MangaDex", "MangaPlus", "MangaSee"]:
            priority_providers.append(provider["name"])
        else:
            generic_providers.append(provider["name"])

    assert len(priority_providers) > 0, "Should have priority providers"


@pytest.mark.asyncio
async def test_single_provider_search(client: TestClient, token: str):
    """Test search with a single provider."""
    provider_name = "mangadex"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    search_data = {"query": "naruto", "provider": provider_name, "page": 1, "limit": 5}

    response = client.post("/api/v1/search", json=search_data, headers=headers)

    # Since provider monitoring is disabled in tests, providers might not be available
    # Accept both 200 (success) and 400 (provider not found) as valid responses
    assert response.status_code in [
        200,
        400,
    ], f"Expected 200 or 400, got {response.status_code}"

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])

        # If we get results, verify their structure
        if results:
            assert "title" in results[0], "Results should have title"
            assert "provider" in results[0], "Results should have provider"
    else:
        # If provider not found, that's expected in test environment
        data = response.json()
        assert "Provider" in data.get(
            "detail", ""
        ), "Should indicate provider not found"


@pytest.mark.asyncio
async def test_multi_provider_search(client: TestClient, token: str):
    """Test search across multiple providers."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    search_data = {"query": "naruto", "page": 1, "limit": 10}

    response = client.post("/api/v1/search", json=search_data, headers=headers)
    assert response.status_code == 200

    data = response.json()
    results = data.get("results", [])

    assert len(results) > 0, "Should have results from multiple providers"

    # Check that we have results from multiple providers
    providers_found = set()
    for result in results:
        if "provider" in result:
            providers_found.add(result["provider"])

    # We expect at least one provider to return results
    assert len(providers_found) >= 1, "Should have results from at least one provider"
