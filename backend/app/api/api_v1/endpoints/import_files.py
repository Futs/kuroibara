import os
import tempfile
import shutil
from typing import Any, List, Optional, Dict
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.manga import Manga, MangaType, MangaStatus
from app.models.library import MangaUserLibrary
from app.schemas.manga import Manga as MangaSchema, Chapter as ChapterSchema
from app.core.services.import_file import (
    import_archive,
    import_directory,
    create_manga_from_import,
)

router = APIRouter()


@router.post("/manga", response_model=MangaSchema)
async def import_new_manga(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    manga_type: MangaType = Form(MangaType.MANGA),
    status: MangaStatus = Form(MangaStatus.UNKNOWN),
    year: Optional[int] = Form(None),
    is_nsfw: bool = Form(False),
    genres: Optional[str] = Form(None),  # Comma-separated list
    authors: Optional[str] = Form(None),  # Comma-separated list
    cover: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Import a new manga.
    
    Args:
        title: Manga title
        description: Manga description (optional)
        manga_type: Manga type (default: MANGA)
        status: Manga status (default: UNKNOWN)
        year: Publication year (optional)
        is_nsfw: Whether the manga is NSFW (default: False)
        genres: Comma-separated list of genre names (optional)
        authors: Comma-separated list of author names (optional)
        cover: Cover image file (optional)
    """
    # Parse genres and authors
    genre_list = genres.split(",") if genres else []
    author_list = authors.split(",") if authors else []
    
    # Save cover image to temporary file if provided
    cover_path = None
    if cover:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            cover_path = temp_file.name
            shutil.copyfileobj(cover.file, temp_file)
    
    try:
        # Create manga
        manga, library_item = await create_manga_from_import(
            title=title,
            user_id=current_user.id,
            db=db,
            description=description,
            cover_path=cover_path,
            manga_type=manga_type,
            status=status,
            year=year,
            is_nsfw=is_nsfw,
            genres=genre_list,
            authors=author_list,
        )
        
        return manga
    finally:
        # Clean up temporary file
        if cover_path and os.path.exists(cover_path):
            os.unlink(cover_path)


@router.post("/chapter/{manga_id}", response_model=ChapterSchema)
async def import_chapter(
    manga_id: str,
    chapter_number: str = Form(...),
    title: Optional[str] = Form(None),
    volume: Optional[str] = Form(None),
    language: str = Form("en"),
    chapter_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Import a chapter from a CBZ/CBR/7Z file.
    
    Args:
        manga_id: ID of the manga
        chapter_number: Chapter number
        title: Chapter title (optional)
        volume: Volume number (optional)
        language: Language code (default: "en")
        chapter_file: Chapter file (CBZ/CBR/7Z)
    """
    # Check if manga exists and belongs to user
    manga = await db.get(Manga, uuid.UUID(manga_id))
    if not manga:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manga not found",
        )
    
    # Check if user has access to manga
    result = await db.execute(
        select(MangaUserLibrary).where(
            (MangaUserLibrary.user_id == current_user.id) &
            (MangaUserLibrary.manga_id == uuid.UUID(manga_id))
        )
    )
    library_item = result.scalars().first()
    if not library_item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check file extension
    file_ext = os.path.splitext(chapter_file.filename)[1].lower()
    if file_ext not in [".zip", ".cbz", ".rar", ".cbr", ".7z"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only CBZ, CBR, and 7Z files are supported.",
        )
    
    # Save file to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name
        shutil.copyfileobj(chapter_file.file, temp_file)
    
    try:
        # Import chapter
        chapter = await import_archive(
            file_path=file_path,
            manga_id=uuid.UUID(manga_id),
            chapter_number=chapter_number,
            user_id=current_user.id,
            db=db,
            title=title,
            volume=volume,
            language=language,
        )
        
        return chapter
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)
