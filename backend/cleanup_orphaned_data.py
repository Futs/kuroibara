#!/usr/bin/env python3
"""
Script to clean up orphaned data that might cause issues when re-adding manga to library.
"""
import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, "/app")

from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings


async def cleanup_orphaned_data():
    """Clean up orphaned data that might cause foreign key issues."""

    async for session in get_db():
        try:
            print("🧹 Starting orphaned data cleanup...")

            # 1. Clean up orphaned manga_user_library_category entries
            result = await session.execute(
                text(
                    """
                DELETE FROM manga_user_library_category 
                WHERE manga_user_library_id NOT IN (
                    SELECT id FROM manga_user_library
                )
            """
                )
            )
            print(
                f"✅ Cleaned up {result.rowcount} orphaned manga_user_library_category entries"
            )

            # 2. Clean up orphaned reading_progress entries
            result = await session.execute(
                text(
                    """
                DELETE FROM reading_progress 
                WHERE chapter_id NOT IN (
                    SELECT id FROM chapter
                )
            """
                )
            )
            print(f"✅ Cleaned up {result.rowcount} orphaned reading_progress entries")

            # 3. Clean up orphaned bookmark entries
            result = await session.execute(
                text(
                    """
                DELETE FROM bookmark 
                WHERE chapter_id NOT IN (
                    SELECT id FROM chapter
                )
            """
                )
            )
            print(f"✅ Cleaned up {result.rowcount} orphaned bookmark entries")

            # 4. Clean up orphaned page entries
            result = await session.execute(
                text(
                    """
                DELETE FROM page 
                WHERE chapter_id NOT IN (
                    SELECT id FROM chapter
                )
            """
                )
            )
            print(f"✅ Cleaned up {result.rowcount} orphaned page entries")

            # 5. Clean up orphaned chapter entries
            result = await session.execute(
                text(
                    """
                DELETE FROM chapter 
                WHERE manga_id NOT IN (
                    SELECT id FROM manga
                )
            """
                )
            )
            print(f"✅ Cleaned up {result.rowcount} orphaned chapter entries")

            # 6. Clean up orphaned manga_genre entries
            result = await session.execute(
                text(
                    """
                DELETE FROM manga_genre 
                WHERE manga_id NOT IN (
                    SELECT id FROM manga
                )
            """
                )
            )
            print(f"✅ Cleaned up {result.rowcount} orphaned manga_genre entries")

            # 7. Clean up orphaned manga_author entries
            result = await session.execute(
                text(
                    """
                DELETE FROM manga_author 
                WHERE manga_id NOT IN (
                    SELECT id FROM manga
                )
            """
                )
            )
            print(f"✅ Cleaned up {result.rowcount} orphaned manga_author entries")

            # 8. Clean up orphaned external_manga_mappings entries
            result = await session.execute(
                text(
                    """
                DELETE FROM external_manga_mappings 
                WHERE manga_id NOT IN (
                    SELECT id FROM manga
                )
            """
                )
            )
            print(
                f"✅ Cleaned up {result.rowcount} orphaned external_manga_mappings entries"
            )

            # 9. Clean up orphaned reading_list_manga entries
            result = await session.execute(
                text(
                    """
                DELETE FROM reading_list_manga 
                WHERE manga_id NOT IN (
                    SELECT id FROM manga
                )
            """
                )
            )
            print(
                f"✅ Cleaned up {result.rowcount} orphaned reading_list_manga entries"
            )

            # 10. Show any remaining potential issues
            print("\n🔍 Checking for potential issues...")

            # Check for manga without any library entries (might be safe to delete)
            result = await session.execute(
                text(
                    """
                SELECT m.id, m.title, m.provider, m.external_id
                FROM manga m
                WHERE m.id NOT IN (
                    SELECT DISTINCT manga_id FROM manga_user_library
                )
                LIMIT 10
            """
                )
            )
            orphaned_manga = result.fetchall()

            if orphaned_manga:
                print(
                    f"⚠️  Found {len(orphaned_manga)} manga not in any user's library:"
                )
                for manga in orphaned_manga:
                    print(
                        f"   - {manga.title} (ID: {manga.id}, Provider: {manga.provider})"
                    )
                print("   These might be safe to delete if they're not needed.")
            else:
                print("✅ No orphaned manga found")

            await session.commit()
            print("\n🎉 Cleanup completed successfully!")

        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_data())
