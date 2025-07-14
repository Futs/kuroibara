from fastapi.testclient import TestClient


def test_api_docs(client: TestClient) -> None:
    """Test that the API docs are accessible."""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_api_redoc(client: TestClient) -> None:
    """Test that the API redoc is accessible."""
    response = client.get("/api/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()


def test_api_openapi(client: TestClient) -> None:
    """Test that the OpenAPI schema is accessible."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
    assert "paths" in response.json()
