#!/usr/bin/env python3
"""
Script to create/drop test database for running tests.
This creates a test database in the same PostgreSQL instance.
"""

import asyncio
import asyncpg
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


async def create_test_database():
    """Create test database if it doesn't exist."""
    # Use localhost when running locally (outside Docker)
    db_host = "localhost" if settings.DB_HOST == "postgres" else settings.DB_HOST
    
    # Connect to postgres database to create our test database
    admin_connection = await asyncpg.connect(
        host=db_host,
        port=int(settings.DB_PORT),
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        database="postgres"  # Connect to default postgres database
    )
    
    test_db_name = f"test_{settings.DB_DATABASE}"
    
    try:
        # Check if test database exists
        result = await admin_connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", test_db_name
        )
        
        if not result:
            # Create test database
            await admin_connection.execute(f"CREATE DATABASE {test_db_name}")
            print(f"Created test database: {test_db_name}")
        else:
            print(f"Test database {test_db_name} already exists")
            
    except Exception as e:
        print(f"Error creating test database: {e}")
        raise
    finally:
        await admin_connection.close()


async def drop_test_database():
    """Drop test database."""
    # Use localhost when running locally (outside Docker)
    db_host = "localhost" if settings.DB_HOST == "postgres" else settings.DB_HOST
    
    # Connect to postgres database to drop our test database
    admin_connection = await asyncpg.connect(
        host=db_host,
        port=int(settings.DB_PORT),
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        database="postgres"  # Connect to default postgres database
    )
    
    test_db_name = f"test_{settings.DB_DATABASE}"
    
    try:
        # Drop test database if it exists
        await admin_connection.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        print(f"Dropped test database: {test_db_name}")
            
    except Exception as e:
        print(f"Error dropping test database: {e}")
        raise
    finally:
        await admin_connection.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        asyncio.run(drop_test_database())
    else:
        asyncio.run(create_test_database())
