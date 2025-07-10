"""
CBZ conversion service for manga chapters.

This module handles the conversion of various manga formats (directories, archives)
into standardized CBZ files with proper organization and metadata.
"""

import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pyunpack import Archive

from app.core.services.naming import naming_engine
from app.core.utils import get_image_dimensions, is_image_file
from app.models.manga import Chapter, Manga
from app.models.user import User

logger = logging.getLogger(__name__)


class CBZConverter:
    """
    Service for converting manga chapters to CBZ format with proper organization.
    """
    
    def __init__(self):
        """Initialize the CBZ converter."""
        self.naming_engine = naming_engine
    
    def get_image_files_from_directory(self, directory_path: str) -> List[str]:
        """
        Get all image files from a directory, sorted naturally.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            List of image file paths, sorted
        """
        image_files = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if is_image_file(file_path):
                    image_files.append(file_path)
        
        # Sort files naturally (1, 2, 10 instead of 1, 10, 2)
        def natural_sort_key(path):
            import re
            filename = os.path.basename(path)
            # Extract numbers from filename for natural sorting
            numbers = re.findall(r'\d+', filename)
            return [int(num) if num.isdigit() else num for num in numbers] + [filename]
        
        image_files.sort(key=natural_sort_key)
        return image_files
    
    def extract_archive_to_temp(self, archive_path: str) -> Tuple[str, List[str]]:
        """
        Extract an archive to a temporary directory and return image files.
        
        Args:
            archive_path: Path to the archive file
            
        Returns:
            Tuple of (temp_directory_path, list_of_image_files)
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Get file extension
            file_ext = os.path.splitext(archive_path)[1].lower()
            
            # Extract based on file type
            if file_ext in [".zip", ".cbz"]:
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
            elif file_ext in [".rar", ".cbr", ".7z"]:
                Archive(archive_path).extractall(temp_dir)
            else:
                raise ValueError(f"Unsupported archive format: {file_ext}")
            
            # Get image files from extracted content
            image_files = self.get_image_files_from_directory(temp_dir)
            
            return temp_dir, image_files
            
        except Exception as e:
            # Clean up temp directory on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    
    def create_cbz_metadata(
        self, 
        manga: Manga, 
        chapter: Chapter, 
        image_files: List[str]
    ) -> Dict:
        """
        Create metadata for the CBZ file.
        
        Args:
            manga: The manga object
            chapter: The chapter object
            image_files: List of image file paths
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "manga": {
                "title": manga.title,
                "id": str(manga.id),
                "year": manga.year,
                "status": manga.status.value if manga.status else None,
                "type": manga.type.value if manga.type else None,
                "provider": manga.provider,
                "external_id": manga.external_id,
            },
            "chapter": {
                "title": chapter.title,
                "number": chapter.number,
                "volume": chapter.volume,
                "language": chapter.language,
                "id": str(chapter.id),
                "pages_count": len(image_files),
                "source": chapter.source,
            },
            "pages": [],
            "created_by": "Kuroibara CBZ Converter",
            "created_at": None,  # Will be set when creating CBZ
        }
        
        # Add page information
        for i, image_file in enumerate(image_files):
            try:
                width, height = get_image_dimensions(image_file)
                page_info = {
                    "number": i + 1,
                    "filename": os.path.basename(image_file),
                    "width": width,
                    "height": height,
                }
                metadata["pages"].append(page_info)
            except Exception as e:
                logger.warning(f"Could not get dimensions for {image_file}: {e}")
                metadata["pages"].append({
                    "number": i + 1,
                    "filename": os.path.basename(image_file),
                    "width": None,
                    "height": None,
                })
        
        return metadata
    
    def create_cbz_from_images(
        self,
        image_files: List[str],
        output_path: str,
        manga: Manga,
        chapter: Chapter,
        include_metadata: bool = True
    ) -> bool:
        """
        Create a CBZ file from a list of image files.
        
        Args:
            image_files: List of image file paths
            output_path: Output CBZ file path
            manga: The manga object
            chapter: The chapter object
            include_metadata: Whether to include metadata in the CBZ
            
        Returns:
            True if CBZ was created successfully
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as cbz_file:
                # Add image files
                for i, image_file in enumerate(image_files):
                    if not os.path.exists(image_file):
                        logger.warning(f"Image file not found: {image_file}")
                        continue
                    
                    # Generate a standardized filename for the image in the CBZ
                    file_ext = os.path.splitext(image_file)[1]
                    cbz_filename = f"{i+1:04d}{file_ext}"
                    
                    cbz_file.write(image_file, cbz_filename)
                
                # Add metadata if requested
                if include_metadata:
                    metadata = self.create_cbz_metadata(manga, chapter, image_files)
                    metadata["created_at"] = None  # Could add timestamp here
                    
                    metadata_json = json.dumps(metadata, indent=2)
                    cbz_file.writestr("metadata.json", metadata_json)
            
            logger.info(f"Created CBZ file: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create CBZ file {output_path}: {e}")
            return False
    
    def convert_directory_to_cbz(
        self,
        directory_path: str,
        output_path: str,
        manga: Manga,
        chapter: Chapter,
        include_metadata: bool = True
    ) -> bool:
        """
        Convert a directory of images to a CBZ file.
        
        Args:
            directory_path: Path to directory containing images
            output_path: Output CBZ file path
            manga: The manga object
            chapter: The chapter object
            include_metadata: Whether to include metadata
            
        Returns:
            True if conversion was successful
        """
        try:
            image_files = self.get_image_files_from_directory(directory_path)
            
            if not image_files:
                logger.error(f"No image files found in directory: {directory_path}")
                return False
            
            return self.create_cbz_from_images(
                image_files, output_path, manga, chapter, include_metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to convert directory {directory_path} to CBZ: {e}")
            return False
    
    def convert_archive_to_cbz(
        self,
        archive_path: str,
        output_path: str,
        manga: Manga,
        chapter: Chapter,
        include_metadata: bool = True
    ) -> bool:
        """
        Convert an archive file to a standardized CBZ file.
        
        Args:
            archive_path: Path to source archive
            output_path: Output CBZ file path
            manga: The manga object
            chapter: The chapter object
            include_metadata: Whether to include metadata
            
        Returns:
            True if conversion was successful
        """
        temp_dir = None
        
        try:
            # If source is already a CBZ and we don't need metadata, just copy
            if (archive_path.lower().endswith('.cbz') and 
                not include_metadata and 
                archive_path != output_path):
                shutil.copy2(archive_path, output_path)
                return True
            
            # Extract archive to temporary directory
            temp_dir, image_files = self.extract_archive_to_temp(archive_path)
            
            if not image_files:
                logger.error(f"No image files found in archive: {archive_path}")
                return False
            
            # Create CBZ from extracted images
            success = self.create_cbz_from_images(
                image_files, output_path, manga, chapter, include_metadata
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to convert archive {archive_path} to CBZ: {e}")
            return False
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def convert_chapter_to_cbz(
        self,
        chapter: Chapter,
        manga: Manga,
        output_path: str,
        include_metadata: bool = True
    ) -> bool:
        """
        Convert a chapter to CBZ format based on its current file type.
        
        Args:
            chapter: The chapter object
            manga: The manga object
            output_path: Output CBZ file path
            include_metadata: Whether to include metadata
            
        Returns:
            True if conversion was successful
        """
        if not chapter.file_path or not os.path.exists(chapter.file_path):
            logger.error(f"Chapter file not found: {chapter.file_path}")
            return False
        
        try:
            if os.path.isdir(chapter.file_path):
                # Source is a directory
                return self.convert_directory_to_cbz(
                    chapter.file_path, output_path, manga, chapter, include_metadata
                )
            else:
                # Source is an archive file
                return self.convert_archive_to_cbz(
                    chapter.file_path, output_path, manga, chapter, include_metadata
                )
                
        except Exception as e:
            logger.error(f"Failed to convert chapter {chapter.id} to CBZ: {e}")
            return False


# Global instance
cbz_converter = CBZConverter()
