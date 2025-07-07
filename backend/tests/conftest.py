import asyncio
import os
import pytest
import asyncpg
from typing import AsyncGenerator, Generator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

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
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0
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
    
    # Use the session
    async with TestingAsyncSessionLocal() as session:
        yield session
    
    # Clean up tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Test client
@pytest.fixture(scope="function")
def client(db: AsyncSession) -> Generator[TestClient, None, None]:
    # Override the dependencies
    app.dependency_overrides[get_db] = lambda: db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Reset the dependencies
    app.dependency_overrides = {}
