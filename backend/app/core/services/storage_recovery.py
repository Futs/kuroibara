"""
Storage recovery service for disaster recovery scenarios.

This module provides functionality to recover manga from existing storage
when the database is lost or corrupted.
"""

import json
import logging
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import get_manga_storage_path, is_image_file
from app.models.library import MangaUserLibrary
from app.models.manga import Chapter, Manga, MangaStatus, MangaType
from app.models.organization import ChapterMetadata, MangaMetadata

logger = logging.getLogger(__name__)


class StorageRecoveryService:
    """Service to recover manga from existing storage without database."""
    
    def __init__(self):
        """Initialize the storage recovery service."""
        self.storage_path = settings.STORAGE_PATH
        self.manga_storage_path = os.path.join(self.storage_path, "manga")
    
    async def scan_storage_for_manga(self, user_id: UUID, db: AsyncSession) -> List[Dict]:
        """
        Scan storage directory for organized manga and attempt to recover metadata.
        
        Args:
            user_id: User ID for recovery
            db: Database session
            
        Returns:
            List of recoverable manga with extracted metadata
        """
        if not os.path.exists(self.manga_storage_path):
            logger.warning(f"Manga storage path does not exist: {self.manga_storage_path}")
            return []
        
        recovered_manga = []
        
        # Get existing manga UUIDs from database to avoid duplicates
        result = await db.execute(
            select(Manga.id).join(MangaUserLibrary).where(MangaUserLibrary.user_id == user_id)
        )
        existing_uuids = {str(uuid) for uuid in result.scalars().all()}
        
        try:
            for item in os.listdir(self.manga_storage_path):
                manga_dir = os.path.join(self.manga_storage_path, item)
                
                # Skip if not a directory or if it's already in database
                if not os.path.isdir(manga_dir) or item in existing_uuids:
                    continue
                
                # Check if this looks like a manga UUID directory
                if not self._is_valid_uuid_format(item):
                    continue
                
                organized_path = os.path.join(manga_dir, "organized")
                
                if os.path.exists(organized_path) and os.listdir(organized_path):
                    try:
                        manga_info = await self._extract_manga_info_from_structure(organized_path)
                        
                        if manga_info:
                            manga_info.update({
                                "storage_uuid": item,
                                "organized_path": organized_path,
                                "storage_size": self._calculate_directory_size(organized_path)
                            })
                            recovered_manga.append(manga_info)
                            
                    except Exception as e:
                        logger.error(f"Error processing manga directory {item}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error scanning storage for manga: {e}")
        
        return recovered_manga
    
    def _is_valid_uuid_format(self, uuid_string: str) -> bool:
        """Check if string looks like a UUID."""
        try:
            UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def _calculate_directory_size(self, directory_path: str) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
        except Exception as e:
            logger.error(f"Error calculating directory size for {directory_path}: {e}")
        
        return total_size
    
    async def _extract_manga_info_from_structure(self, organized_path: str) -> Optional[Dict]:
        """
        Extract manga metadata from organized folder structure.
        
        Args:
            organized_path: Path to organized manga directory
            
        Returns:
            Dictionary with extracted manga information
        """
        try:
            # Get the first level directory (should be manga title)
            manga_dirs = [d for d in os.listdir(organized_path) 
                         if os.path.isdir(os.path.join(organized_path, d))]
            
            if not manga_dirs:
                return None
            
            # Use the first directory as manga title (there should only be one)
            manga_title = manga_dirs[0]
            manga_path = os.path.join(organized_path, manga_title)
            
            # Scan for volumes and chapters
            volumes = {}
            total_chapters = 0
            
            for item in os.listdir(manga_path):
                item_path = os.path.join(manga_path, item)
                
                if os.path.isdir(item_path):
                    # This is a volume directory
                    volume_name = item
                    chapters = self._scan_volume_for_chapters(item_path)
                    
                    if chapters:
                        volumes[volume_name] = chapters
                        total_chapters += len(chapters)
                
                elif item.endswith('.cbz'):
                    # Direct chapter file (no volume structure)
                    if "Direct" not in volumes:
                        volumes["Direct"] = []
                    
                    chapter_info = self._extract_chapter_info_from_filename(item)
                    if chapter_info:
                        chapter_info["file_path"] = item_path
                        volumes["Direct"].append(chapter_info)
                        total_chapters += 1
            
            # Try to extract additional metadata from CBZ files
            additional_metadata = await self._extract_metadata_from_cbz_files(volumes)
            
            return {
                "extracted_title": manga_title,
                "chapter_count": total_chapters,
                "volume_count": len(volumes),
                "volumes": volumes,
                "metadata": additional_metadata,
                "has_volume_structure": len([v for v in volumes.keys() if v != "Direct"]) > 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting manga info from {organized_path}: {e}")
            return None
    
    def _scan_volume_for_chapters(self, volume_path: str) -> List[Dict]:
        """Scan a volume directory for chapter files."""
        chapters = []
        
        try:
            for item in os.listdir(volume_path):
                if item.endswith('.cbz'):
                    chapter_info = self._extract_chapter_info_from_filename(item)
                    if chapter_info:
                        chapter_info["file_path"] = os.path.join(volume_path, item)
                        chapters.append(chapter_info)
        
        except Exception as e:
            logger.error(f"Error scanning volume {volume_path}: {e}")
        
        return sorted(chapters, key=lambda x: self._natural_sort_key(x.get("number", "0")))
    
    def _extract_chapter_info_from_filename(self, filename: str) -> Optional[Dict]:
        """Extract chapter information from filename."""
        try:
            # Remove .cbz extension
            name = filename.replace('.cbz', '')
            
            # Try to match pattern: "number - title"
            match = re.match(r'^([0-9.]+)\s*-\s*(.+)$', name)
            
            if match:
                number = match.group(1)
                title = match.group(2)
            else:
                # Fallback: try to extract just the number
                number_match = re.search(r'([0-9.]+)', name)
                number = number_match.group(1) if number_match else "0"
                title = name
            
            return {
                "number": number,
                "title": title,
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error extracting chapter info from {filename}: {e}")
            return None
    
    def _natural_sort_key(self, text: str):
        """Natural sorting key for chapter numbers."""
        try:
            return float(text)
        except ValueError:
            return float('inf')
    
    async def _extract_metadata_from_cbz_files(self, volumes: Dict) -> Dict:
        """Extract metadata from CBZ files if available."""
        metadata = {
            "description": None,
            "year": None,
            "status": None,
            "type": None,
            "provider": None,
            "external_id": None,
        }
        
        # Try to find metadata in the first CBZ file
        for volume_chapters in volumes.values():
            if volume_chapters:
                first_chapter = volume_chapters[0]
                cbz_metadata = self._read_cbz_metadata(first_chapter.get("file_path"))
                
                if cbz_metadata:
                    manga_meta = cbz_metadata.get("manga", {})
                    metadata.update({
                        "description": manga_meta.get("description"),
                        "year": manga_meta.get("year"),
                        "status": manga_meta.get("status"),
                        "type": manga_meta.get("type"),
                        "provider": manga_meta.get("provider"),
                        "external_id": manga_meta.get("external_id"),
                    })
                    break
        
        return metadata
    
    def _read_cbz_metadata(self, cbz_path: str) -> Optional[Dict]:
        """Read metadata from a CBZ file."""
        try:
            with zipfile.ZipFile(cbz_path, 'r') as cbz:
                if 'metadata.json' in cbz.namelist():
                    metadata_content = cbz.read('metadata.json')
                    return json.loads(metadata_content.decode('utf-8'))
        except Exception as e:
            logger.debug(f"Could not read metadata from {cbz_path}: {e}")
        
        return None
    
    async def recover_manga_to_database(
        self,
        storage_uuid: str,
        manga_title: str,
        user_id: UUID,
        db: AsyncSession,
        metadata: Optional[Dict] = None
    ) -> Manga:
        """
        Create database entries for recovered manga from storage.
        
        Args:
            storage_uuid: Original storage UUID
            manga_title: Manga title
            user_id: User ID
            db: Database session
            metadata: Additional metadata from CBZ files
            
        Returns:
            Created manga object
        """
        try:
            # Create manga entry
            manga = Manga(
                title=manga_title,
                description=metadata.get("description") if metadata else None,
                year=metadata.get("year") if metadata else None,
                status=MangaStatus(metadata.get("status")) if metadata and metadata.get("status") else MangaStatus.UNKNOWN,
                type=MangaType(metadata.get("type")) if metadata and metadata.get("type") else MangaType.MANGA,
                provider=metadata.get("provider") if metadata else "recovered",
                external_id=metadata.get("external_id") if metadata else None,
            )
            
            db.add(manga)
            await db.flush()
            
            # Move organized files from old UUID to new UUID
            old_storage_path = os.path.join(self.manga_storage_path, storage_uuid)
            new_storage_path = get_manga_storage_path(manga.id)
            
            # Ensure new storage directory doesn't exist
            if os.path.exists(new_storage_path):
                shutil.rmtree(new_storage_path)
            
            # Move the entire directory
            shutil.move(old_storage_path, new_storage_path)
            
            # Create library association
            library_item = MangaUserLibrary(
                user_id=user_id,
                manga_id=manga.id,
                is_favorite=False,  # Default to not favorite for recovered manga
                is_downloaded=True,  # Mark as downloaded since we're recovering from storage
            )
            db.add(library_item)
            
            # Scan and create chapter entries from organized files
            await self._create_chapters_from_organized_files(manga, user_id, db)
            
            # Create manga metadata
            manga_metadata = MangaMetadata(
                manga_id=manga.id,
                user_id=user_id,
                is_organized=True,
                organization_format="recovered",
                reading_status="reading",
            )
            db.add(manga_metadata)
            
            await db.commit()
            await db.refresh(manga)
            
            logger.info(f"Successfully recovered manga '{manga_title}' with ID {manga.id}")
            return manga
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error recovering manga '{manga_title}': {e}")
            raise
    
    async def _create_chapters_from_organized_files(
        self,
        manga: Manga,
        user_id: UUID,
        db: AsyncSession
    ) -> None:
        """Create chapter database entries from organized files."""
        try:
            organized_path = os.path.join(get_manga_storage_path(manga.id), "organized", manga.title)
            
            if not os.path.exists(organized_path):
                logger.warning(f"Organized path not found: {organized_path}")
                return
            
            for item in os.listdir(organized_path):
                item_path = os.path.join(organized_path, item)
                
                if os.path.isdir(item_path):
                    # Volume directory
                    volume_name = item.replace("Volume ", "").strip()
                    await self._create_chapters_from_volume(manga, volume_name, item_path, user_id, db)
                
                elif item.endswith('.cbz'):
                    # Direct chapter file
                    await self._create_chapter_from_file(manga, None, item_path, user_id, db)
        
        except Exception as e:
            logger.error(f"Error creating chapters for manga {manga.id}: {e}")
    
    async def _create_chapters_from_volume(
        self,
        manga: Manga,
        volume: str,
        volume_path: str,
        user_id: UUID,
        db: AsyncSession
    ) -> None:
        """Create chapters from a volume directory."""
        try:
            for item in os.listdir(volume_path):
                if item.endswith('.cbz'):
                    chapter_path = os.path.join(volume_path, item)
                    await self._create_chapter_from_file(manga, volume, chapter_path, user_id, db)
        
        except Exception as e:
            logger.error(f"Error creating chapters from volume {volume_path}: {e}")
    
    async def _create_chapter_from_file(
        self,
        manga: Manga,
        volume: Optional[str],
        file_path: str,
        user_id: UUID,
        db: AsyncSession
    ) -> None:
        """Create a chapter entry from a CBZ file."""
        try:
            filename = os.path.basename(file_path)
            chapter_info = self._extract_chapter_info_from_filename(filename)
            
            if not chapter_info:
                logger.warning(f"Could not extract chapter info from {filename}")
                return
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Try to count pages in CBZ
            pages_count = self._count_pages_in_cbz(file_path)
            
            chapter = Chapter(
                manga_id=manga.id,
                title=chapter_info["title"],
                number=chapter_info["number"],
                volume=volume,
                language="en",  # Default language
                pages_count=pages_count,
                file_path=file_path,
                file_size=file_size,
                source="recovered",
            )
            
            db.add(chapter)
            await db.flush()
            
            # Create chapter metadata
            chapter_metadata = ChapterMetadata(
                chapter_id=chapter.id,
                user_id=user_id,
                is_organized=True,
                organized_path=file_path,
                cbz_path=file_path,
                total_pages=pages_count,
            )
            db.add(chapter_metadata)
            
        except Exception as e:
            logger.error(f"Error creating chapter from file {file_path}: {e}")
    
    def _count_pages_in_cbz(self, cbz_path: str) -> Optional[int]:
        """Count pages in a CBZ file."""
        try:
            with zipfile.ZipFile(cbz_path, 'r') as cbz:
                image_files = [f for f in cbz.namelist() 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
                return len(image_files)
        except Exception as e:
            logger.debug(f"Could not count pages in {cbz_path}: {e}")
            return None


# Global instance
storage_recovery_service = StorageRecoveryService()
