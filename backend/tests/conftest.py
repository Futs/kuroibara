# Disable provider monitoring and database initialization for tests - MUST be set before any imports
import os
os.environ["ENABLE_PROVIDER_MONITORING"] = "false"
os.environ["ENABLE_DB_INIT"] = "false"

import asyncio
import pytest
import asyncpg
from typing import AsyncGenerator, Generator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.db.session import get_db, Base

# Use test database configuration from environment variables or construct from settings
# For local testing (outside Docker), use localhost instead of postgres container name
db_host = "localhost" if settings.DB_HOST == "postgres" else settings.DB_HOST
test_db_name = f"test_{settings.DB_DATABASE}"
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{db_host}:{settings.DB_PORT}/{test_db_name}"
)


async def create_test_database_if_not_exists():
    """Create test database if it doesn't exist."""
    try:
        # Connect to postgres database to check/create test database
        admin_conn = await asyncpg.connect(
            host=db_host,
            port=int(settings.DB_PORT),
            user=settings.DB_USERNAME,
            password=settings.DB_PASSWORD,
            database="postgres"
        )
        
        # Check if test database exists
        result = await admin_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", test_db_name
        )
        
        if not result:
            # Create test database
            await admin_conn.execute(f"CREATE DATABASE {test_db_name}")
        
        await admin_conn.close()
    except Exception:
        # If we can't create the database, tests will fail anyway
        # This is a fallback attempt
        pass


# Create async engine and session for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Use NullPool to avoid connection pool issues in tests
    connect_args={"server_settings": {"jit": "off"}}  # Disable JIT for tests
)
TestingAsyncSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


# Override the get_db dependency
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Setup and teardown for each test
@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    # Ensure test database exists before trying to connect
    await create_test_database_if_not_exists()

    # Create tables in test database
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a new session for the test
    session = TestingAsyncSessionLocal()
    try:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()
    except Exception:
        # Rollback on any exception
        await session.rollback()
        raise
    finally:
        # Always close the session
        await session.close()

        # Clean up tables after test
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Override the get_db dependency for tests
async def get_test_db(session: AsyncSession):
    """Get test database session."""
    return session


# Database dependency override
async def override_get_db():
    """Override database dependency for tests."""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Test client
@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    # Override the dependencies to use test database
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Reset the dependencies
    app.dependency_overrides = {}


# Authentication fixtures
@pytest.fixture(scope="function")
def test_user(client: TestClient, db: AsyncSession) -> dict:
    """Create a test user via API."""
    import uuid

    # Use a unique email for each test to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "password123",
        "full_name": "Test User",
    }

    # Register the user via API
    response = client.post("/api/v1/auth/register", json=user_data)
    if response.status_code != 201:
        print(f"Registration failed with status {response.status_code}: {response.text}")
        print(f"Response headers: {response.headers}")
        # For debugging, let's also try a simple health check
        health_response = client.get("/health")
        print(f"Health check status: {health_response.status_code}")
    assert response.status_code in [200, 201]  # Accept both 200 and 201 for user creation

    # Return user data for use in other fixtures
    return user_data


@pytest.fixture(scope="function")
def token(client: TestClient, test_user: dict) -> str:
    """Get authentication token for test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user["username"],
            "password": test_user["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


# Test endpoint fixture for parameterized tests
@pytest.fixture(params=[
    "/api/v1/search/genres",
    "/api/v1/search/providers",
    "/api/v1/reading-lists",
    "/api/v1/library",
])
def endpoint(request):
    """Provide test endpoints."""
    return request.param
