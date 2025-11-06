#!/usr/bin/env python3
"""
Initialize database for CI/CD pipeline.
This script runs migrations and creates initial data.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.init_db import create_initial_data
from app.db.session import AsyncSessionLocal


async def init_data():
    """Initialize database with default data."""
    try:
        async with AsyncSessionLocal() as session:
            await create_initial_data(session)
            await session.commit()
            print("✅ Initial data created successfully")
            return 0
    except Exception as e:
        print(f"❌ Error creating initial data: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(init_data())
    sys.exit(exit_code)

