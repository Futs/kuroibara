"""
Test script to verify the fixes for Kuroibara issues.
"""

import pytest
from fastapi.testclient import TestClient


def call_endpoint(endpoint, client: TestClient, method="GET", data=None, headers=None, expected_status=None):
    """Call an API endpoint and return the response."""
    try:
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, json=data, headers=headers)

        if expected_status:
            assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"

        return response

    except Exception as e:
        pytest.fail(f"{method} {endpoint}: ERROR - {e}")
        return None

@pytest.mark.asyncio
async def test_genres_endpoint_requires_auth(client: TestClient):
    """Test that genres endpoint exists and requires authentication."""
    response = call_endpoint("/api/v1/search/genres", client, expected_status=401)
    assert response is not None


@pytest.mark.asyncio
async def test_api_docs_accessible(client: TestClient):
    """Test that API docs are accessible."""
    response = call_endpoint("/api/docs", client, expected_status=200)
    assert response is not None


@pytest.mark.asyncio
async def test_providers_endpoint_requires_auth(client: TestClient):
    """Test that providers endpoint exists and requires authentication."""
    response = call_endpoint("/api/v1/search/providers", client, expected_status=401)
    assert response is not None


@pytest.mark.asyncio
async def test_reading_lists_endpoint_requires_auth(client: TestClient):
    """Test that reading lists endpoint exists and requires authentication."""
    response = call_endpoint("/api/v1/reading-lists", client, expected_status=401)
    assert response is not None


@pytest.mark.asyncio
async def test_library_endpoint_requires_auth(client: TestClient):
    """Test that library endpoint exists and requires authentication."""
    response = call_endpoint("/api/v1/library", client, expected_status=401)
    assert response is not None


@pytest.mark.asyncio
async def test_manga_from_external_endpoint_requires_auth(client: TestClient):
    """Test that manga from external endpoint exists and requires authentication."""
    response = call_endpoint("/api/v1/manga/from-external", client, method="POST", expected_status=401)
    assert response is not None
