#!/usr/bin/env python3
"""Create test user for API testing."""

import asyncio
import sys

sys.path.insert(0, "/app")

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def create_test_user():
    """Create test user."""
    print("👤 Creating test user\n")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Check if user already exists
        from sqlalchemy import select

        result = await db.execute(
            select(User).where(User.username == "testuser_provider")
        )
        existing_user = result.scalars().first()

        if existing_user:
            print("✅ User 'testuser_provider' already exists")
            print(f"   ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            return

        # Create new user
        print("Creating new user 'testuser_provider'...")
        user = User(
            username="testuser_provider",
            email="testuser@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print("✅ User created successfully")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Password: password123")


if __name__ == "__main__":
    asyncio.run(create_test_user())
