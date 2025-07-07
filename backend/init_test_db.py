#!/usr/bin/env python3
"""
Database initialization script for testing environments.
This script initializes the database schema before running migrations.
"""

import asyncio
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.init_db import init_db


async def setup_test_db():
    """Initialize test database with base schema."""
    try:
        print("🔄 Initializing test database...")
        await init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_test_db())
    if not success:
        sys.exit(1)
