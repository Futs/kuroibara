from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.manga import Manga, Chapter, Page, Genre, Author
from app.schemas.manga import (
    Manga as MangaSchema,
    MangaCreate,
    MangaUpdate,
    Chapter as ChapterSchema,
    ChapterCreate,
    ChapterUpdate,
)

router = APIRouter()


@router.get("", response_model=List[MangaSchema])
async def read_manga(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Retrieve manga.
    """
    result = await db.execute(select(Manga).offset(skip).limit(limit))
    manga_list = result.scalars().all()
    return manga_list


@router.post("", response_model=MangaSchema)
async def create_manga(
    manga_data: MangaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new manga.
    """
    # Create manga
    manga = Manga(**manga_data.model_dump(exclude={"genres", "authors"}))
    
    # Add genres
    if manga_data.genres:
        for genre_name in manga_data.genres:
            # Check if genre exists
            result = await db.execute(select(Genre).where(Genre.name == genre_name))
            genre = result.scalars().first()
            
            # Create genre if it doesn't exist
            if not genre:
                genre = Genre(name=genre_name)
                db.add(genre)
                await db.flush()
            
            manga.genres.append(genre)
    
    # Add authors
    if manga_data.authors:
        for author_name in manga_data.authors:
            # Check if author exists
            result = await db.execute(select(Author).where(Author.name == author_name))
            author = result.scalars().first()
            
            # Create author if it doesn't exist
            if not author:
                author = Author(name=author_name)
                db.add(author)
                await db.flush()
            
            manga.authors.append(author)
    
    db.add(manga)
    await db.commit()
    await db.refresh(manga)
    
    return manga


@router.get("/{manga_id}", response_model=MangaSchema)
async def read_manga_by_id(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get manga by ID.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    return manga


@router.put("/{manga_id}", response_model=MangaSchema)
async def update_manga(
    manga_id: str,
    manga_update: MangaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    # Update manga fields
    update_data = manga_update.model_dump(exclude={"genres", "authors"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(manga, field, value)
    
    # Update genres
    if manga_update.genres is not None:
        # Clear existing genres
        manga.genres = []
        
        # Add new genres
        for genre_name in manga_update.genres:
            # Check if genre exists
            result = await db.execute(select(Genre).where(Genre.name == genre_name))
            genre = result.scalars().first()
            
            # Create genre if it doesn't exist
            if not genre:
                genre = Genre(name=genre_name)
                db.add(genre)
                await db.flush()
            
            manga.genres.append(genre)
    
    # Update authors
    if manga_update.authors is not None:
        # Clear existing authors
        manga.authors = []
        
        # Add new authors
        for author_name in manga_update.authors:
            # Check if author exists
            result = await db.execute(select(Author).where(Author.name == author_name))
            author = result.scalars().first()
            
            # Create author if it doesn't exist
            if not author:
                author = Author(name=author_name)
                db.add(author)
                await db.flush()
            
            manga.authors.append(author)
    
    await db.commit()
    await db.refresh(manga)
    
    return manga


@router.delete("/{manga_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manga(
    manga_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    # Delete manga
    await db.delete(manga)
    await db.commit()


@router.post("/{manga_id}/cover", response_model=MangaSchema)
async def upload_manga_cover(
    manga_id: str,
    cover: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Upload a cover image for a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    # In a real implementation, this would save the cover image to a storage system
    # and update the manga's cover_image field with the path to the image
    
    # For now, just update the manga with a placeholder path
    manga.cover_image = f"/covers/{manga_id}.jpg"
    
    await db.commit()
    await db.refresh(manga)
    
    return manga


@router.get("/{manga_id}/chapters", response_model=List[ChapterSchema])
async def read_manga_chapters(
    manga_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get chapters for a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    result = await db.execute(
        select(Chapter)
        .where(Chapter.manga_id == uuid.UUID(manga_id))
        .order_by(Chapter.number)
        .offset(skip)
        .limit(limit)
    )
    chapters = result.scalars().all()
    
    return chapters


@router.post("/{manga_id}/chapters", response_model=ChapterSchema)
async def create_manga_chapter(
    manga_id: str,
    chapter_data: ChapterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a new chapter for a manga.
    """
    manga = await db.get(Manga, uuid.UUID(manga_id))
    
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    # Create chapter
    chapter = Chapter(**chapter_data.model_dump())
    
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    
    return chapter
