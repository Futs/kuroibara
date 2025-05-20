#!/usr/bin/env python3
"""
Script to initialize the database with tables and initial data.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.init_db import init_db


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Initializing database")
    await init_db()
    logger.info("Database initialized successfully")


if __name__ == "__main__":
    asyncio.run(main())
