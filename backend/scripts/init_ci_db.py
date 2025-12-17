#!/usr/bin/env python3
"""
Database initialization script for CI/CD pipeline.
This script only creates initial data, not tables (tables are created by Alembic).

This script should be run from the backend directory:
    cd backend
    python scripts/init_ci_db.py
"""
import asyncio
import os
import sys

# Add the backend directory to the Python path
# Get the directory containing this script (backend/scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the backend directory (parent of scripts)
backend_dir = os.path.dirname(script_dir)
# Add backend directory to path for imports
sys.path.insert(0, backend_dir)

from app.db.init_db import create_initial_data
from app.db.session import AsyncSessionLocal


async def setup_ci_db():
    """Initialize CI database with initial data only (tables created by Alembic)."""
    try:
        print("🔄 Initializing CI database with initial data...")

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
    success = asyncio.run(setup_ci_db())
    if not success:
        sys.exit(1)
