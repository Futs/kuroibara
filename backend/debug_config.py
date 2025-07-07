#!/usr/bin/env python3
"""Test script to verify database configuration"""

import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


def main():
    print(f"Database configuration:")
    print(f"DB_HOST: {settings.DB_HOST}")
    print(f"DB_PORT: {settings.DB_PORT}")
    print(f"DB_USERNAME: {settings.DB_USERNAME}")
    print(f"DB_DATABASE: {settings.DB_DATABASE}")

    # Test database URL construction
    db_host = "localhost" if settings.DB_HOST == "postgres" else settings.DB_HOST
    test_db_url = f"postgresql+asyncpg://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{db_host}:{settings.DB_PORT}/test_{settings.DB_DATABASE}"
    print(f"Test database URL: {test_db_url}")


if __name__ == "__main__":
    main()
