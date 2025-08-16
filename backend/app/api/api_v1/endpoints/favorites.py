import logging
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.library import MangaUserLibrary as MangaUserLibraryModel
from app.models.manga import Chapter, Manga
from app.models.user import User
from app.schemas.library import MangaUserLibrary as MangaUserLibrarySchema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[MangaUserLibrarySchema])
async def get_user_favorites(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search favorites by title"),
    sort_by: str = Query(
        "updated_at", description="Sort by: updated_at, created_at, title, rating"
    ),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user's favorite manga list with search and sorting.
    """
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build base query
        query = (
            select(MangaUserLibraryModel)
            .options(
                selectinload(MangaUserLibraryModel.manga).selectinload(Manga.genres),
                selectinload(MangaUserLibraryModel.manga).selectinload(Manga.authors),
                selectinload(MangaUserLibraryModel.manga)
                .selectinload(Manga.chapters)
                .selectinload(Chapter.pages),
            )
            .where(
                and_(
                    MangaUserLibraryModel.user_id == current_user.id,
                    MangaUserLibraryModel.is_favorite is True,
                )
            )
        )

        # Add search filter if provided
        if search:
            query = query.join(Manga).where(Manga.title.ilike(f"%{search}%"))

        # Add sorting
        sort_column = getattr(MangaUserLibraryModel, sort_by, None)
        if sort_by == "title":
            # Sort by manga title
            query = query.join(Manga) if not search else query
            sort_column = Manga.title
        elif sort_column is None:
            # Default to updated_at if invalid sort_by
            sort_column = MangaUserLibraryModel.updated_at

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        favorites = result.scalars().all()

        logger.info(
            f"Retrieved {len(favorites)} favorites for user {current_user.username} "
            f"(search: '{search}', sort: {sort_by} {sort_order})"
        )
        return favorites

    except Exception as e:
        logger.error(f"Error getting user favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get favorites",
        )


@router.post("/{manga_id}", response_model=dict)
async def add_to_favorites(
    manga_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a manga to user's favorites.
    """
    try:
        # Check if manga exists
        result = await db.execute(select(Manga).where(Manga.id == manga_id))
        manga = result.scalar_one_or_none()

        if not manga:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Manga not found"
            )

        # Check if manga is already in user's library
        result = await db.execute(
            select(MangaUserLibraryModel).where(
                and_(
                    MangaUserLibraryModel.user_id == current_user.id,
                    MangaUserLibraryModel.manga_id == manga_id,
                )
            )
        )
        library_entry = result.scalar_one_or_none()

        if library_entry:
            # Update existing entry to favorite
            if library_entry.is_favorite:
                return {"message": "Manga is already in favorites", "is_favorite": True}
            else:
                library_entry.is_favorite = True
                await db.commit()
                logger.info(
                    f"Added manga {manga_id} to favorites for user {current_user.username}"
                )
                return {"message": "Manga added to favorites", "is_favorite": True}
        else:
            # Create new library entry as favorite
            new_entry = MangaUserLibraryModel(
                user_id=current_user.id, manga_id=manga_id, is_favorite=True
            )
            db.add(new_entry)
            await db.commit()

            logger.info(
                f"Created new favorite entry for manga {manga_id} for user {current_user.username}"
            )
            return {"message": "Manga added to favorites", "is_favorite": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding manga to favorites: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add manga to favorites",
        )


@router.delete("/{manga_id}", response_model=dict)
async def remove_from_favorites(
    manga_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a manga from user's favorites.
    """
    try:
        # Find the library entry
        result = await db.execute(
            select(MangaUserLibraryModel).where(
                and_(
                    MangaUserLibraryModel.user_id == current_user.id,
                    MangaUserLibraryModel.manga_id == manga_id,
                )
            )
        )
        library_entry = result.scalar_one_or_none()

        if not library_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manga not found in user's library",
            )

        if not library_entry.is_favorite:
            return {"message": "Manga is not in favorites", "is_favorite": False}

        # Remove from favorites
        library_entry.is_favorite = False
        await db.commit()

        logger.info(
            f"Removed manga {manga_id} from favorites for user {current_user.username}"
        )
        return {"message": "Manga removed from favorites", "is_favorite": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing manga from favorites: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove manga from favorites",
        )


@router.get("/{manga_id}/status", response_model=dict)
async def get_favorite_status(
    manga_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Check if a manga is in user's favorites.
    """
    try:
        result = await db.execute(
            select(MangaUserLibraryModel.is_favorite).where(
                and_(
                    MangaUserLibraryModel.user_id == current_user.id,
                    MangaUserLibraryModel.manga_id == manga_id,
                )
            )
        )
        is_favorite = result.scalar_one_or_none()

        return {
            "manga_id": str(manga_id),
            "is_favorite": bool(is_favorite) if is_favorite is not None else False,
        }

    except Exception as e:
        logger.error(f"Error checking favorite status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check favorite status",
        )


@router.get("/count", response_model=dict)
async def get_favorites_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the count of user's favorite manga.
    """
    try:
        result = await db.execute(
            select(MangaUserLibraryModel).where(
                and_(
                    MangaUserLibraryModel.user_id == current_user.id,
                    MangaUserLibraryModel.is_favorite is True,
                )
            )
        )
        favorites = result.scalars().all()
        count = len(favorites)

        return {"count": count}

    except Exception as e:
        logger.error(f"Error getting favorites count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get favorites count",
        )


@router.patch("/bulk", response_model=dict)
async def bulk_update_favorites(
    manga_ids: List[UUID],
    is_favorite: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Bulk update favorite status for multiple manga.
    """
    try:
        updated_count = 0

        for manga_id in manga_ids:
            # Check if manga exists in library
            result = await db.execute(
                select(MangaUserLibraryModel).where(
                    and_(
                        MangaUserLibraryModel.user_id == current_user.id,
                        MangaUserLibraryModel.manga_id == manga_id,
                    )
                )
            )
            library_entry = result.scalar_one_or_none()

            if library_entry:
                if library_entry.is_favorite != is_favorite:
                    library_entry.is_favorite = is_favorite
                    updated_count += 1
            elif is_favorite:
                # Create new entry if adding to favorites
                new_entry = MangaUserLibraryModel(
                    user_id=current_user.id, manga_id=manga_id, is_favorite=True
                )
                db.add(new_entry)
                updated_count += 1

        await db.commit()

        action = "added to" if is_favorite else "removed from"
        logger.info(
            f"Bulk {action} favorites: {updated_count} manga for user {current_user.username}"
        )

        return {
            "message": f"Successfully {action} favorites",
            "updated_count": updated_count,
            "total_requested": len(manga_ids),
        }

    except Exception as e:
        logger.error(f"Error bulk updating favorites: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk update favorites",
        )


@router.get("/export", response_model=dict)
async def export_favorites(
    format: str = Query("json", description="Export format: json, csv"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Export user's favorites list in various formats.
    """
    try:
        # Get all user favorites
        result = await db.execute(
            select(MangaUserLibraryModel)
            .options(
                selectinload(MangaUserLibraryModel.manga).selectinload(Manga.genres),
                selectinload(MangaUserLibraryModel.manga).selectinload(Manga.authors),
                selectinload(MangaUserLibraryModel.manga)
                .selectinload(Manga.chapters)
                .selectinload(Chapter.pages),
            )
            .where(
                and_(
                    MangaUserLibraryModel.user_id == current_user.id,
                    MangaUserLibraryModel.is_favorite is True,
                )
            )
            .order_by(MangaUserLibraryModel.updated_at.desc())
        )
        favorites = result.scalars().all()

        if format.lower() == "csv":
            # CSV format
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "Title",
                    "Description",
                    "Type",
                    "Status",
                    "Year",
                    "Rating",
                    "Notes",
                    "Added Date",
                    "Updated Date",
                ]
            )

            # Write data
            for fav in favorites:
                manga = fav.manga
                writer.writerow(
                    [
                        manga.title if manga else "Unknown",
                        (
                            manga.description[:100] + "..."
                            if manga
                            and manga.description
                            and len(manga.description) > 100
                            else manga.description if manga else ""
                        ),
                        manga.type.value if manga and manga.type else "",
                        manga.status.value if manga and manga.status else "",
                        manga.year if manga else "",
                        fav.rating or "",
                        fav.notes or "",
                        fav.created_at.isoformat(),
                        fav.updated_at.isoformat(),
                    ]
                )

            csv_content = output.getvalue()
            output.close()

            return {
                "format": "csv",
                "content": csv_content,
                "filename": f"favorites_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "count": len(favorites),
            }

        else:
            # JSON format (default)
            favorites_data = []
            for fav in favorites:
                manga = fav.manga
                favorites_data.append(
                    {
                        "id": str(fav.id),
                        "manga_id": str(fav.manga_id),
                        "title": manga.title if manga else "Unknown",
                        "description": manga.description if manga else None,
                        "type": manga.type.value if manga and manga.type else None,
                        "status": (
                            manga.status.value if manga and manga.status else None
                        ),
                        "year": manga.year if manga else None,
                        "rating": fav.rating,
                        "notes": fav.notes,
                        "custom_title": fav.custom_title,
                        "added_date": fav.created_at.isoformat(),
                        "updated_date": fav.updated_at.isoformat(),
                    }
                )

            return {
                "format": "json",
                "content": favorites_data,
                "filename": f"favorites_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "count": len(favorites),
            }

    except Exception as e:
        logger.error(f"Error exporting favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export favorites",
        )
