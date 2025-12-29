#!/usr/bin/env python3
"""Test complete workflow: MangaUpdates metadata → Provider matching → Add to library → Fetch chapters."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.providers.registry import provider_registry
from app.core.services.enhanced_search import ProviderMatcher
from app.core.services.mangaupdates import MangaUpdatesService
from app.db.session import AsyncSessionLocal
from app.models.manga import Chapter, Manga
from app.models.mangaupdates import MangaUpdatesEntry
from app.schemas.manga import MangaStatus, MangaType


async def test_complete_workflow():
    """Test the complete workflow from search to chapter fetching."""
    print("🔍 Testing Complete Workflow: MangaUpdates → Providers → Library → Chapters")
    print("=" * 80)
    print()

    async with AsyncSessionLocal() as db:
        # Step 1: Search MangaUpdates for metadata
        print("1️⃣  STEP 1: Search MangaUpdates for 'One Piece'")
        print("-" * 80)

        mu_service = MangaUpdatesService()
        mu_result = await mu_service.search_and_create_entry(
            "One Piece", db, auto_select_best=True
        )

        if not mu_result:
            print("❌ No MangaUpdates results found")
            return

        print(f"✅ Found: {mu_result.title}")
        print(f"   MU Series ID: {mu_result.mu_series_id}")
        print(
            f"   Description: {mu_result.description[:100] if mu_result.description else 'N/A'}..."
        )
        print(f"   Year: {mu_result.year}")
        print(f"   Rating: {mu_result.rating}")
        print(f"   Genres: {', '.join(mu_result.genres or [])[:60]}...")
        print(
            f"   Authors: {', '.join([a.get('name', '') for a in (mu_result.authors or [])])}"
        )
        print()

        # Step 2: Find provider matches
        print("2️⃣  STEP 2: Find provider matches")
        print("-" * 80)

        matcher = ProviderMatcher()
        provider_matches = await matcher.find_provider_matches(
            mu_result, max_providers=5
        )

        if not provider_matches:
            print("❌ No provider matches found")
            return

        print(f"✅ Found {len(provider_matches)} provider matches:")
        for i, match in enumerate(provider_matches[:3], 1):
            print(
                f"   {i}. {match['provider']}: {match['title']} (confidence: {match['confidence']:.3f})"
            )
        print()

        # Step 3: Add to library (create Manga record)
        print("3️⃣  STEP 3: Add to library")
        print("-" * 80)

        # Check if already exists
        existing = await db.execute(
            select(Manga).filter(Manga.title == mu_result.title)
        )
        existing_manga = existing.scalar_one_or_none()

        if existing_manga:
            print(
                f"⚠️  Already in library: {existing_manga.title} (ID: {existing_manga.id})"
            )
            manga = existing_manga
        else:
            # Create new manga record
            manga = Manga(
                title=mu_result.title,
                alternative_titles=mu_result.alternative_titles or {},
                description=mu_result.description,
                cover_image=mu_result.cover_image_url,
                type=mu_result.type or MangaType.UNKNOWN,
                status=mu_result.status or MangaStatus.UNKNOWN,
                year=mu_result.year,
                is_nsfw=mu_result.is_nsfw,
            )
            db.add(manga)
            await db.commit()
            await db.refresh(manga)
            print(f"✅ Added to library: {manga.title} (ID: {manga.id})")
        print()

        # Step 4: Fetch chapters from best provider match
        print("4️⃣  STEP 4: Fetch chapters from provider")
        print("-" * 80)

        best_match = provider_matches[0]
        print(f"Using provider: {best_match['provider']}")
        print(f"External ID: {best_match['external_id']}")
        print()

        # Get provider instance
        provider = provider_registry.get_provider(best_match["provider"])
        if not provider:
            print(f"❌ Provider {best_match['provider']} not found")
            return

        # Fetch chapters
        try:
            chapters, total, has_more = await provider.get_chapters(
                best_match["external_id"]
            )
            print(
                f"✅ Found {len(chapters)} chapters (total: {total}, has_more: {has_more})"
            )

            # Show first 5 and last 5 chapters
            if chapters:
                print("\n   First 5 chapters:")
                for i, chapter in enumerate(chapters[:5], 1):
                    # Chapters are dicts, not objects
                    # MangaDex uses 'number' not 'chapter_number'
                    ch_num = chapter.get("number", "N/A")
                    ch_vol = chapter.get("volume", "")
                    ch_title = chapter.get("title", "No title")
                    vol_str = f"Vol.{ch_vol} " if ch_vol else ""
                    print(f"      {i}. {vol_str}Chapter {ch_num}: {ch_title}")

                if len(chapters) > 10:
                    print(f"\n   ... {len(chapters) - 10} more chapters ...")

                if len(chapters) > 5:
                    print("\n   Last 5 chapters:")
                    for i, chapter in enumerate(chapters[-5:], len(chapters) - 4):
                        ch_num = chapter.get("number", "N/A")
                        ch_vol = chapter.get("volume", "")
                        ch_title = chapter.get("title", "No title")
                        vol_str = f"Vol.{ch_vol} " if ch_vol else ""
                        print(f"      {i}. {vol_str}Chapter {ch_num}: {ch_title}")
            print()

            # Step 5: Store chapters in database
            print("5️⃣  STEP 5: Store chapters in database")
            print("-" * 80)

            # Check if chapters already exist
            existing_chapters = await db.execute(
                select(Chapter).filter(Chapter.manga_id == manga.id)
            )
            existing_count = len(existing_chapters.scalars().all())

            if existing_count > 0:
                print(f"⚠️  {existing_count} chapters already in database")
            else:
                # Store first 10 chapters as a test
                chapters_to_store = chapters[:10]
                for chapter_data in chapters_to_store:
                    # MangaDex uses 'number' not 'chapter_number', 'volume' not 'volume_number'
                    chapter = Chapter(
                        manga_id=manga.id,
                        number=str(chapter_data.get("number", "0")),
                        title=chapter_data.get("title", ""),
                        volume=(
                            str(chapter_data.get("volume", ""))
                            if chapter_data.get("volume")
                            else None
                        ),
                        source=best_match["provider"],
                        external_id=chapter_data.get("id", ""),
                    )
                    db.add(chapter)

                await db.commit()
                print(f"✅ Stored {len(chapters_to_store)} chapters in database")
            print()

            # Step 6: Summary
            print("6️⃣  SUMMARY")
            print("-" * 80)
            print(f"✅ Manga: {manga.title}")
            print(f"✅ MangaUpdates ID: {mu_result.mu_series_id}")
            print(f"✅ Provider: {best_match['provider']}")
            print(f"✅ Provider ID: {best_match['external_id']}")
            print(f"✅ Total Chapters: {len(chapters)}")
            print(f"✅ Database ID: {manga.id}")
            print()
            print("🎉 Complete workflow successful!")

        except Exception as e:
            print(f"❌ Error fetching chapters: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
