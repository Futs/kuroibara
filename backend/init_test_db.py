#!/usr/bin/env python3
"""
Database initialization script for testing environments.
This script only creates initial data, not tables (tables are created by Alembic).
"""

import asyncio
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from app.db.init_db import create_initial_data
from app.db.session import AsyncSessionLocal


async def setup_test_db():
    """Initialize test database with initial data only (tables created by Alembic)."""
    try:
        print("🔄 Initializing test database with initial data...")

        # Only create initial data, not tables (Alembic handles table creation)
        async with AsyncSessionLocal() as session:
            await create_initial_data(session)
            await session.commit()

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
