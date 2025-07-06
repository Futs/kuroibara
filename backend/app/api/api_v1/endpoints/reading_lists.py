from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.manga import Manga
from app.models.library import ReadingList
from app.schemas.library import (
    ReadingList as ReadingListSchema,
    ReadingListCreate,
    ReadingListUpdate,
)

router = APIRouter()


@router.get("", response_model=List[ReadingListSchema])
async def read_reading_lists(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve user's reading lists.
    """
    result = await db.execute(
        select(ReadingList)
        .options(selectinload(ReadingList.manga))
        .where(ReadingList.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    reading_lists = result.scalars().all()

    return reading_lists


@router.post("", response_model=ReadingListSchema)
async def create_reading_list(
    reading_list_data: ReadingListCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new reading list.
    """
    # Check if reading list with same name already exists for this user
    result = await db.execute(
        select(ReadingList).where(
            (ReadingList.name == reading_list_data.name) & (ReadingList.user_id == current_user.id)
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reading list with this name already exists",
        )

    # Create reading list
    reading_list = ReadingList(
        **reading_list_data.model_dump(exclude={"manga_ids"}),
        user_id=current_user.id,
    )

    # Add manga to reading list using direct SQL to avoid greenlet issues
    if reading_list_data.manga_ids:
        from app.models.library import reading_list_manga

        for manga_id in reading_list_data.manga_ids:
            manga = await db.get(Manga, manga_id)
            if manga:
                # Check if relationship already exists before inserting
                existing_rel = await db.execute(
                    select(reading_list_manga).where(
                        (reading_list_manga.c.reading_list_id == reading_list.id) &
                        (reading_list_manga.c.manga_id == manga.id)
                    )
                )
                if not existing_rel.first():
                    # Insert into association table directly only if it doesn't exist
                    await db.execute(
                        insert(reading_list_manga).values(
                            reading_list_id=reading_list.id,
                            manga_id=manga.id
                        )
                    )

    db.add(reading_list)
    await db.commit()
    await db.refresh(reading_list)

    # Load relationships explicitly to avoid greenlet issues during response serialization
    result = await db.execute(
        select(ReadingList)
        .options(
            selectinload(ReadingList.manga).selectinload(Manga.genres),
            selectinload(ReadingList.manga).selectinload(Manga.authors),
            selectinload(ReadingList.manga).selectinload(Manga.chapters)
        )
        .where(ReadingList.id == reading_list.id)
    )
    reading_list_with_relationships = result.scalars().first()

    return reading_list_with_relationships


@router.get("/{reading_list_id}", response_model=ReadingListSchema)
async def read_reading_list(
    reading_list_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a reading list by ID.
    """
    result = await db.execute(
        select(ReadingList)
        .options(selectinload(ReadingList.manga))
        .where(ReadingList.id == uuid.UUID(reading_list_id))
    )
    reading_list = result.scalars().first()

    if not reading_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list not found",
        )

    # Check if reading list belongs to user or is public
    if reading_list.user_id != current_user.id and not reading_list.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return reading_list


@router.put("/{reading_list_id}", response_model=ReadingListSchema)
async def update_reading_list(
    reading_list_id: str,
    reading_list_update: ReadingListUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a reading list.
    """
    reading_list = await db.get(ReadingList, uuid.UUID(reading_list_id))

    if not reading_list or reading_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list not found",
        )

    # Check if name is being updated and if it's already taken
    if reading_list_update.name and reading_list_update.name != reading_list.name:
        result = await db.execute(
            select(ReadingList).where(
                (ReadingList.name == reading_list_update.name) & (ReadingList.user_id == current_user.id)
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reading list with this name already exists",
            )

    # Update reading list fields
    update_data = reading_list_update.model_dump(exclude={"manga_ids"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(reading_list, field, value)

    # Update manga in reading list
    if reading_list_update.manga_ids is not None:
        # Clear existing manga
        reading_list.manga = []

        # Add new manga
        for manga_id in reading_list_update.manga_ids:
            manga = await db.get(Manga, manga_id)
            if manga:
                reading_list.manga.append(manga)

    await db.commit()
    await db.refresh(reading_list)

    return reading_list


@router.delete("/{reading_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading_list(
    reading_list_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a reading list.
    """
    reading_list = await db.get(ReadingList, uuid.UUID(reading_list_id))

    if not reading_list or reading_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list not found",
        )

    # Delete reading list
    await db.delete(reading_list)
    await db.commit()


@router.post("/{reading_list_id}/manga/{manga_id}", response_model=ReadingListSchema)
async def add_manga_to_reading_list(
    reading_list_id: str,
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Add a manga to a reading list.
    """
    reading_list = await db.get(ReadingList, uuid.UUID(reading_list_id))

    if not reading_list or reading_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list not found",
        )

    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if manga is already in reading list using direct SQL
    from app.models.library import reading_list_manga
    existing_rel = await db.execute(
        select(reading_list_manga).where(
            (reading_list_manga.c.reading_list_id == reading_list.id) &
            (reading_list_manga.c.manga_id == manga.id)
        )
    )
    if existing_rel.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manga already in reading list",
        )

    # Add manga to reading list using direct SQL to avoid greenlet issues
    await db.execute(
        insert(reading_list_manga).values(
            reading_list_id=reading_list.id,
            manga_id=manga.id
        )
    )

    await db.commit()

    # Load relationships explicitly to avoid greenlet issues during response serialization
    result = await db.execute(
        select(ReadingList)
        .options(
            selectinload(ReadingList.manga).selectinload(Manga.genres),
            selectinload(ReadingList.manga).selectinload(Manga.authors),
            selectinload(ReadingList.manga).selectinload(Manga.chapters)
        )
        .where(ReadingList.id == reading_list.id)
    )
    reading_list_with_relationships = result.scalars().first()

    return reading_list_with_relationships


@router.delete("/{reading_list_id}/manga/{manga_id}", response_model=ReadingListSchema)
async def remove_manga_from_reading_list(
    reading_list_id: str,
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Remove a manga from a reading list.
    """
    reading_list = await db.get(ReadingList, uuid.UUID(reading_list_id))

    if not reading_list or reading_list.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading list not found",
        )

    manga = await db.get(Manga, uuid.UUID(manga_id))

    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )

    # Check if manga is in reading list
    if manga not in reading_list.manga:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manga not in reading list",
        )

    # Remove manga from reading list
    reading_list.manga.remove(manga)

    await db.commit()
    await db.refresh(reading_list)

    return reading_list
