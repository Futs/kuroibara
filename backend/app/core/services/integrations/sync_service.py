"""Sync service for external integrations."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.external_integration import (
    ExternalIntegration, 
    ExternalMangaMapping, 
    IntegrationType, 
    SyncStatus
)
from app.models.library import MangaUserLibrary, ReadingProgress
from app.models.manga import Manga
from app.models.user import User
from app.schemas.external_integration import ExternalMangaData
from .anilist_client import AnilistClient
from .myanimelist_client import MyAnimeListClient
from .kitsu_client import KitsuClient

logger = logging.getLogger(__name__)


class SyncService:
    """Service for syncing data between Kuroibara and external services."""

    def __init__(self):
        # Clients will be created with credentials when needed
        pass

    def _get_client(self, integration: ExternalIntegration):
        """Get client instance with integration credentials."""
        if integration.integration_type == IntegrationType.ANILIST:
            return AnilistClient(integration.client_id, integration.client_secret)
        elif integration.integration_type == IntegrationType.MYANIMELIST:
            return MyAnimeListClient(integration.client_id, integration.client_secret)
        elif integration.integration_type == IntegrationType.KITSU:
            return KitsuClient(integration.client_id, integration.client_secret)
        else:
            raise ValueError(f"Unsupported integration type: {integration.integration_type}")
    
    async def sync_integration(
        self, 
        integration_id: UUID, 
        force_full_sync: bool = False,
        sync_direction: str = "bidirectional"
    ) -> Dict[str, Any]:
        """
        Sync data for a specific integration.
        
        Args:
            integration_id: The integration ID to sync
            force_full_sync: Whether to force a full sync
            sync_direction: 'to_external', 'from_external', or 'bidirectional'
            
        Returns:
            Dict with sync results
        """
        async with AsyncSessionLocal() as db:
            # Get integration with related data
            result = await db.execute(
                select(ExternalIntegration)
                .options(
                    selectinload(ExternalIntegration.user),
                    selectinload(ExternalIntegration.manga_mappings)
                )
                .where(ExternalIntegration.id == integration_id)
            )
            integration = result.scalars().first()
            
            if not integration:
                raise ValueError(f"Integration {integration_id} not found")
            
            if not integration.sync_enabled:
                raise ValueError("Sync is disabled for this integration")
            
            # Update sync status
            integration.last_sync_status = SyncStatus.IN_PROGRESS
            await db.commit()
            
            try:
                client = self._get_client(integration)
                
                # Validate token
                if not await client.validate_token(integration.access_token):
                    # Try to refresh token if available
                    if integration.refresh_token:
                        try:
                            token_data = await client.refresh_token(integration.refresh_token)
                            integration.access_token = token_data['access_token']
                            integration.refresh_token = token_data.get('refresh_token')
                            integration.token_expires_at = token_data.get('expires_at')
                            await db.commit()
                        except Exception as e:
                            logger.error(f"Failed to refresh token for integration {integration_id}: {e}")
                            integration.last_sync_status = SyncStatus.FAILED
                            integration.last_sync_error = "Token refresh failed"
                            await db.commit()
                            raise
                    else:
                        integration.last_sync_status = SyncStatus.FAILED
                        integration.last_sync_error = "Invalid token and no refresh token available"
                        await db.commit()
                        raise ValueError("Invalid token")
                
                sync_results = {
                    'synced_manga_count': 0,
                    'errors': [],
                    'created_mappings': 0,
                    'updated_mappings': 0
                }
                
                # Sync from external to local
                if sync_direction in ['from_external', 'bidirectional']:
                    from_external_results = await self._sync_from_external(
                        db, integration, client, force_full_sync
                    )
                    sync_results['synced_manga_count'] += from_external_results['synced_count']
                    sync_results['errors'].extend(from_external_results['errors'])
                    sync_results['created_mappings'] += from_external_results['created_mappings']
                
                # Sync from local to external
                if sync_direction in ['to_external', 'bidirectional']:
                    to_external_results = await self._sync_to_external(
                        db, integration, client
                    )
                    sync_results['updated_mappings'] += to_external_results['updated_count']
                    sync_results['errors'].extend(to_external_results['errors'])
                
                # Update sync status
                integration.last_sync_at = datetime.utcnow()
                integration.last_sync_status = SyncStatus.SUCCESS
                integration.last_sync_error = None
                integration.sync_count += 1
                await db.commit()
                
                return sync_results
                
            except Exception as e:
                logger.error(f"Sync failed for integration {integration_id}: {e}")
                integration.last_sync_status = SyncStatus.FAILED
                integration.last_sync_error = str(e)
                await db.commit()
                raise
    
    async def _sync_from_external(
        self, 
        db: AsyncSession, 
        integration: ExternalIntegration, 
        client, 
        force_full_sync: bool
    ) -> Dict[str, Any]:
        """Sync manga list from external service to local."""
        results = {
            'synced_count': 0,
            'errors': [],
            'created_mappings': 0
        }
        
        try:
            # Get external manga list
            external_manga_list = await client.get_manga_list(
                integration.access_token,
                limit=1000  # Get all manga
            )
            
            for external_manga in external_manga_list.manga:
                try:
                    # Check if mapping already exists
                    result = await db.execute(
                        select(ExternalMangaMapping).where(
                            and_(
                                ExternalMangaMapping.integration_id == integration.id,
                                ExternalMangaMapping.external_manga_id == external_manga.id
                            )
                        )
                    )
                    mapping = result.scalars().first()
                    
                    if not mapping:
                        # Try to find matching manga by title
                        manga = await self._find_manga_by_title(db, external_manga.title)
                        
                        if manga:
                            # Create new mapping
                            mapping = ExternalMangaMapping(
                                integration_id=integration.id,
                                manga_id=manga.id,
                                external_manga_id=external_manga.id,
                                external_title=external_manga.title,
                                external_url=external_manga.url,
                                external_data=external_manga.model_dump(),
                                sync_status=SyncStatus.SUCCESS,
                                last_synced_at=datetime.utcnow()
                            )
                            db.add(mapping)
                            results['created_mappings'] += 1
                        else:
                            # Log that we couldn't find a matching manga
                            logger.info(f"No matching manga found for external title: {external_manga.title}")
                            continue
                    
                    if mapping and mapping.manga_id:
                        # Update local library entry if sync settings allow
                        if integration.sync_status or integration.sync_ratings or integration.sync_reading_progress:
                            await self._update_local_manga_status(
                                db, integration.user_id, mapping.manga_id, external_manga, integration
                            )
                        
                        # Update mapping data
                        mapping.external_data = external_manga.model_dump()
                        mapping.last_synced_at = datetime.utcnow()
                        mapping.sync_status = SyncStatus.SUCCESS
                        
                        results['synced_count'] += 1
                
                except Exception as e:
                    error_msg = f"Failed to sync manga {external_manga.title}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            await db.commit()
            
        except Exception as e:
            error_msg = f"Failed to fetch external manga list: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    async def _sync_to_external(
        self, 
        db: AsyncSession, 
        integration: ExternalIntegration, 
        client
    ) -> Dict[str, Any]:
        """Sync local manga status to external service."""
        results = {
            'updated_count': 0,
            'errors': []
        }
        
        try:
            # Get all mappings for this integration
            result = await db.execute(
                select(ExternalMangaMapping)
                .options(selectinload(ExternalMangaMapping.manga))
                .where(ExternalMangaMapping.integration_id == integration.id)
            )
            mappings = result.scalars().all()
            
            for mapping in mappings:
                try:
                    # Get local library entry
                    library_result = await db.execute(
                        select(MangaUserLibrary).where(
                            and_(
                                MangaUserLibrary.user_id == integration.user_id,
                                MangaUserLibrary.manga_id == mapping.manga_id
                            )
                        )
                    )
                    library_entry = library_result.scalars().first()
                    
                    if library_entry:
                        # Get reading progress
                        progress_result = await db.execute(
                            select(ReadingProgress).where(
                                and_(
                                    ReadingProgress.user_id == integration.user_id,
                                    ReadingProgress.manga_id == mapping.manga_id
                                )
                            )
                        )
                        progress_entries = progress_result.scalars().all()
                        chapters_read = len([p for p in progress_entries if p.is_completed])
                        
                        # Update external service
                        success = await client.update_manga_status(
                            integration.access_token,
                            mapping.external_manga_id,
                            library_entry.status or 'reading',
                            progress=chapters_read if integration.sync_reading_progress else None,
                            score=library_entry.rating if integration.sync_ratings else None,
                            notes=library_entry.notes
                        )
                        
                        if success:
                            mapping.last_synced_at = datetime.utcnow()
                            mapping.sync_status = SyncStatus.SUCCESS
                            results['updated_count'] += 1
                        else:
                            mapping.sync_status = SyncStatus.FAILED
                            mapping.sync_error = "Failed to update external service"
                
                except Exception as e:
                    error_msg = f"Failed to sync manga {mapping.external_title} to external: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    mapping.sync_status = SyncStatus.FAILED
                    mapping.sync_error = str(e)
            
            await db.commit()
            
        except Exception as e:
            error_msg = f"Failed to sync to external service: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    async def _find_manga_by_title(self, db: AsyncSession, title: str) -> Optional[Manga]:
        """Find manga by title (fuzzy matching)."""
        # Simple exact match for now - could be improved with fuzzy matching
        result = await db.execute(
            select(Manga).where(Manga.title.ilike(f"%{title}%"))
        )
        return result.scalars().first()
    
    async def _update_local_manga_status(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        manga_id: UUID, 
        external_manga: ExternalMangaData,
        integration: ExternalIntegration
    ):
        """Update local manga status from external data."""
        # Get or create library entry
        result = await db.execute(
            select(MangaUserLibrary).where(
                and_(
                    MangaUserLibrary.user_id == user_id,
                    MangaUserLibrary.manga_id == manga_id
                )
            )
        )
        library_entry = result.scalars().first()
        
        if not library_entry:
            library_entry = MangaUserLibrary(
                user_id=user_id,
                manga_id=manga_id,
                status='reading'
            )
            db.add(library_entry)
        
        # Update status if sync is enabled
        if integration.sync_status and external_manga.status:
            client = self._get_client(integration)
            library_entry.status = client.map_status_from_external(external_manga.status)
        
        # Update rating if sync is enabled
        if integration.sync_ratings and external_manga.score:
            library_entry.rating = external_manga.score
        
        # Update notes
        if external_manga.notes:
            library_entry.notes = external_manga.notes
