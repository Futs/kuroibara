import os
import shutil
import uuid
import zipfile
import rarfile
import py7zr
import magic
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException, status
from PIL import Image

from app.core.config import settings


def get_file_mime_type(file_path: str) -> str:
    """Get the MIME type of a file."""
    return magic.from_file(file_path, mime=True)


def is_image_file(file_path: str) -> bool:
    """Check if a file is an image."""
    mime_type = get_file_mime_type(file_path)
    return mime_type.startswith("image/")


def get_image_dimensions(file_path: str) -> Tuple[int, int]:
    """Get the dimensions of an image."""
    with Image.open(file_path) as img:
        return img.size


async def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Save an uploaded file to the specified destination."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    # Save file
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return destination


async def extract_archive(archive_path: str, extract_to: str) -> List[str]:
    """Extract an archive file (zip, rar, 7z) to the specified directory."""
    # Create extraction directory
    os.makedirs(extract_to, exist_ok=True)
    
    # Get file extension
    file_ext = os.path.splitext(archive_path)[1].lower()
    
    # Extract based on file type
    if file_ext == ".zip" or file_ext == ".cbz":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
            return [os.path.join(extract_to, name) for name in zip_ref.namelist()]
    
    elif file_ext == ".rar" or file_ext == ".cbr":
        with rarfile.RarFile(archive_path, "r") as rar_ref:
            rar_ref.extractall(extract_to)
            return [os.path.join(extract_to, name) for name in rar_ref.namelist()]
    
    elif file_ext == ".7z":
        with py7zr.SevenZipFile(archive_path, "r") as sz_ref:
            sz_ref.extractall(extract_to)
            return [os.path.join(extract_to, name) for name in sz_ref.getnames()]
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported archive format: {file_ext}",
        )


def get_manga_storage_path(manga_id: uuid.UUID) -> str:
    """Get the storage path for a manga."""
    return os.path.join(settings.STORAGE_PATH, "manga", str(manga_id))


def get_chapter_storage_path(manga_id: uuid.UUID, chapter_id: uuid.UUID) -> str:
    """Get the storage path for a chapter."""
    return os.path.join(get_manga_storage_path(manga_id), "chapters", str(chapter_id))


def get_cover_storage_path(manga_id: uuid.UUID) -> str:
    """Get the storage path for a manga cover."""
    return os.path.join(get_manga_storage_path(manga_id), "cover.jpg")


def get_page_storage_path(manga_id: uuid.UUID, chapter_id: uuid.UUID, page_number: int, file_ext: str = ".jpg") -> str:
    """Get the storage path for a page."""
    return os.path.join(get_chapter_storage_path(manga_id, chapter_id), f"{page_number:04d}{file_ext}")


def create_cbz_from_directory(directory_path: str, output_path: str) -> str:
    """Create a CBZ file from a directory of images."""
    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get list of image files
    image_files = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            if is_image_file(file_path):
                image_files.append(file_path)
    
    # Sort image files by name
    image_files.sort()
    
    # Create CBZ file
    with zipfile.ZipFile(output_path, "w") as zip_ref:
        for image_file in image_files:
            # Add image to zip with relative path
            rel_path = os.path.relpath(image_file, directory_path)
            zip_ref.write(image_file, rel_path)
    
    return output_path


def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable size string."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"
