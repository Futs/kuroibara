import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.models.manga import Manga, Genre, Author
from app.models.library import Category


@pytest.mark.asyncio
async def test_register_user(client: TestClient, db: AsyncSession):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_login(client: TestClient, db: AsyncSession):
    """Test user login."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
    )
    db.add(user)
    await db.commit()
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_create_category(client: TestClient, db: AsyncSession):
    """Test category creation."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
    )
    db.add(user)
    await db.commit()
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]
    
    # Create a category
    response = client.post(
        "/api/v1/categories",
        json={
            "name": "Test Category",
            "description": "Test description",
            "color": "#FF0000",
            "icon": "test-icon",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Category"
    assert data["description"] == "Test description"
    assert data["color"] == "#FF0000"
    assert data["icon"] == "test-icon"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_manga(client: TestClient, db: AsyncSession):
    """Test manga creation."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_superuser=True,  # Make the user a superuser
    )
    db.add(user)
    await db.commit()
    
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]
    
    # Create a manga
    response = client.post(
        "/api/v1/manga",
        json={
            "title": "Test Manga",
            "description": "Test description",
            "type": "manga",
            "status": "ongoing",
            "year": 2020,
            "is_nsfw": False,
            "genres": ["Action", "Adventure"],
            "authors": ["Test Author"],
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Manga"
    assert data["description"] == "Test description"
    assert data["type"] == "manga"
    assert data["status"] == "ongoing"
    assert data["year"] == 2020
    assert data["is_nsfw"] is False
    assert len(data["genres"]) == 2
    assert data["genres"][0]["name"] == "Action"
    assert data["genres"][1]["name"] == "Adventure"
    assert len(data["authors"]) == 1
    assert data["authors"][0]["name"] == "Test Author"
    assert "id" in data
