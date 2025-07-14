"""External integration endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.services.integrations import AnilistClient, MyAnimeListClient
from app.core.services.integrations.sync_service import SyncService
from app.models.external_integration import (
    ExternalIntegration,
    IntegrationType,
    SyncStatus,
)
from app.models.user import User
from app.schemas.external_integration import (
    AnilistAuthRequest,
)
from app.schemas.external_integration import (
    ExternalIntegration as ExternalIntegrationSchema,
)
from app.schemas.external_integration import (
    ExternalIntegrationUpdate,
    IntegrationSettings,
    IntegrationSetupRequest,
    IntegrationStatus,
    KitsuAuthRequest,
    MyAnimeListAuthRequest,
    SyncRequest,
    SyncResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/settings", response_model=IntegrationSettings)
async def get_integration_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get user's integration settings and status."""
    # Get all user integrations
    result = await db.execute(
        select(ExternalIntegration)
        .options(selectinload(ExternalIntegration.manga_mappings))
        .where(ExternalIntegration.user_id == current_user.id)
    )
    integrations = result.scalars().all()

    settings = IntegrationSettings()

    for integration in integrations:
        manga_count = len(integration.manga_mappings)

        integration_status = IntegrationStatus(
            integration_type=integration.integration_type,
            is_connected=True,
            external_username=integration.external_username,
            last_sync_at=integration.last_sync_at,
            last_sync_status=integration.last_sync_status,
            sync_enabled=integration.sync_enabled,
            auto_sync=integration.auto_sync,
            manga_count=manga_count,
        )

        if integration.integration_type == IntegrationType.ANILIST:
            settings.anilist = integration_status
        elif integration.integration_type == IntegrationType.MYANIMELIST:
            settings.myanimelist = integration_status

    # Set default status for unconnected integrations
    if not settings.anilist:
        settings.anilist = IntegrationStatus(
            integration_type=IntegrationType.ANILIST,
            is_connected=False,
            last_sync_status=SyncStatus.DISABLED,
            sync_enabled=False,
            auto_sync=False,
        )

    if not settings.myanimelist:
        settings.myanimelist = IntegrationStatus(
            integration_type=IntegrationType.MYANIMELIST,
            is_connected=False,
            last_sync_status=SyncStatus.DISABLED,
            sync_enabled=False,
            auto_sync=False,
        )

    return settings


@router.post("/setup", response_model=ExternalIntegrationSchema)
async def setup_integration(
    setup_request: IntegrationSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Set up integration with API credentials."""
    try:
        # Check if integration already exists
        result = await db.execute(
            select(ExternalIntegration).where(
                (ExternalIntegration.user_id == current_user.id)
                & (
                    ExternalIntegration.integration_type
                    == setup_request.integration_type
                )
            )
        )
        integration = result.scalars().first()

        if integration:
            # Update existing integration
            integration.client_id = setup_request.client_id
            integration.client_secret = (
                setup_request.client_secret
            )  # TODO: Encrypt this
            integration.last_sync_status = SyncStatus.PENDING
        else:
            # Create new integration
            integration = ExternalIntegration(
                user_id=current_user.id,
                integration_type=setup_request.integration_type,
                client_id=setup_request.client_id,
                client_secret=setup_request.client_secret,  # TODO: Encrypt this
                sync_enabled=True,
                auto_sync=True,
                last_sync_status=SyncStatus.PENDING,
            )
            db.add(integration)

        await db.commit()
        await db.refresh(integration)

        return integration

    except Exception as e:
        logger.error(
            f"Failed to setup {setup_request.integration_type} integration: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup {setup_request.integration_type} integration: {str(e)}",
        )


@router.post("/anilist/connect", response_model=ExternalIntegrationSchema)
async def connect_anilist(
    auth_request: AnilistAuthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Connect user's Anilist account."""
    try:
        # Get existing integration for credentials or use provided ones
        result = await db.execute(
            select(ExternalIntegration).where(
                (ExternalIntegration.user_id == current_user.id)
                & (ExternalIntegration.integration_type == IntegrationType.ANILIST)
            )
        )
        existing_integration = result.scalars().first()

        # Use provided credentials or get from existing integration
        client_id = auth_request.client_id
        client_secret = auth_request.client_secret

        if not client_id and existing_integration:
            client_id = existing_integration.client_id
            client_secret = existing_integration.client_secret

        client = AnilistClient(client_id, client_secret)

        # Authenticate with Anilist
        auth_data = await client.authenticate(
            {
                "authorization_code": auth_request.authorization_code,
                "redirect_uri": auth_request.redirect_uri,
            }
        )

        if existing_integration:
            # Update existing integration
            integration = existing_integration
            integration.access_token = auth_data["access_token"]
            integration.refresh_token = auth_data.get("refresh_token")
            integration.token_expires_at = auth_data.get("expires_at")
            integration.external_user_id = auth_data["user_info"]["user_id"]
            integration.external_username = auth_data["user_info"]["username"]
            integration.last_sync_status = SyncStatus.PENDING

            # Update credentials if provided
            if client_id:
                integration.client_id = client_id
            if client_secret:
                integration.client_secret = client_secret
        else:
            # Create new integration
            integration = ExternalIntegration(
                user_id=current_user.id,
                integration_type=IntegrationType.ANILIST,
                client_id=client_id,
                client_secret=client_secret,
                access_token=auth_data["access_token"],
                refresh_token=auth_data.get("refresh_token"),
                token_expires_at=auth_data.get("expires_at"),
                external_user_id=auth_data["user_info"]["user_id"],
                external_username=auth_data["user_info"]["username"],
                sync_enabled=True,
                auto_sync=True,
                last_sync_status=SyncStatus.PENDING,
            )
            db.add(integration)

        await db.commit()
        await db.refresh(integration)

        return integration

    except Exception as e:
        logger.error(f"Failed to connect Anilist account: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Anilist account: {str(e)}",
        )


@router.post("/myanimelist/connect", response_model=ExternalIntegrationSchema)
async def connect_myanimelist(
    auth_request: MyAnimeListAuthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Connect user's MyAnimeList account."""
    try:
        # Get existing integration for credentials or use provided ones
        result = await db.execute(
            select(ExternalIntegration).where(
                (ExternalIntegration.user_id == current_user.id)
                & (ExternalIntegration.integration_type == IntegrationType.MYANIMELIST)
            )
        )
        existing_integration = result.scalars().first()

        # Use provided credentials or get from existing integration
        client_id = auth_request.client_id
        client_secret = auth_request.client_secret

        if not client_id and existing_integration:
            client_id = existing_integration.client_id
            client_secret = existing_integration.client_secret

        client = MyAnimeListClient(client_id, client_secret)

        # Authenticate with MyAnimeList
        auth_data = await client.authenticate(
            {
                "authorization_code": auth_request.authorization_code,
                "code_verifier": auth_request.code_verifier,
                "redirect_uri": auth_request.redirect_uri,
            }
        )

        if existing_integration:
            # Update existing integration
            integration = existing_integration
            integration.access_token = auth_data["access_token"]
            integration.refresh_token = auth_data["refresh_token"]
            integration.token_expires_at = auth_data["expires_at"]
            integration.external_user_id = auth_data["user_info"]["user_id"]
            integration.external_username = auth_data["user_info"]["username"]
            integration.last_sync_status = SyncStatus.PENDING

            # Update credentials if provided
            if client_id:
                integration.client_id = client_id
            if client_secret:
                integration.client_secret = client_secret
        else:
            # Create new integration
            integration = ExternalIntegration(
                user_id=current_user.id,
                integration_type=IntegrationType.MYANIMELIST,
                client_id=client_id,
                client_secret=client_secret,
                access_token=auth_data["access_token"],
                refresh_token=auth_data["refresh_token"],
                token_expires_at=auth_data["expires_at"],
                external_user_id=auth_data["user_info"]["user_id"],
                external_username=auth_data["user_info"]["username"],
                sync_enabled=True,
                auto_sync=True,
                last_sync_status=SyncStatus.PENDING,
            )
            db.add(integration)

        await db.commit()
        await db.refresh(integration)

        return integration

    except Exception as e:
        logger.error(f"Failed to connect MyAnimeList account: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect MyAnimeList account: {str(e)}",
        )


@router.post("/kitsu/connect", response_model=ExternalIntegrationSchema)
async def connect_kitsu(
    auth_request: KitsuAuthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Connect user's Kitsu account."""
    try:
        # Get existing integration for credentials or use provided ones
        result = await db.execute(
            select(ExternalIntegration).where(
                (ExternalIntegration.user_id == current_user.id)
                & (ExternalIntegration.integration_type == IntegrationType.KITSU)
            )
        )
        existing_integration = result.scalars().first()

        # Use credentials from existing integration or provided ones
        client_id = auth_request.client_id or (
            existing_integration.client_id if existing_integration else None
        )
        client_secret = auth_request.client_secret or (
            existing_integration.client_secret if existing_integration else None
        )

        # Create Kitsu client
        from app.core.services.integrations import KitsuClient

        client = KitsuClient(client_id, client_secret)

        # Authenticate with Kitsu
        auth_data = await client.authenticate(
            auth_request.username, auth_request.password
        )

        # Get user info
        user_info = await client.get_user_info(auth_data["access_token"])

        if existing_integration:
            # Update existing integration
            existing_integration.access_token = auth_data["access_token"]
            existing_integration.refresh_token = auth_data.get("refresh_token")
            existing_integration.external_user_id = user_info["id"]
            existing_integration.external_username = user_info["username"]
            existing_integration.token_expires_at = datetime.utcnow() + timedelta(
                seconds=auth_data.get("expires_in", 3600)
            )
            existing_integration.last_sync_status = SyncStatus.SUCCESS
            existing_integration.last_sync_at = datetime.utcnow()

            if client_id:
                existing_integration.client_id = client_id
            if client_secret:
                existing_integration.client_secret = client_secret

            await db.commit()
            await db.refresh(existing_integration)
            return existing_integration
        else:
            # Create new integration
            integration = ExternalIntegration(
                user_id=current_user.id,
                integration_type=IntegrationType.KITSU,
                client_id=client_id,
                client_secret=client_secret,
                access_token=auth_data["access_token"],
                refresh_token=auth_data.get("refresh_token"),
                external_user_id=user_info["id"],
                external_username=user_info["username"],
                token_expires_at=datetime.utcnow()
                + timedelta(seconds=auth_data.get("expires_in", 3600)),
                sync_enabled=True,
                last_sync_status=SyncStatus.SUCCESS,
                last_sync_at=datetime.utcnow(),
            )

            db.add(integration)
            await db.commit()
            await db.refresh(integration)
            return integration

    except Exception as e:
        logger.error(f"Failed to connect Kitsu account: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Kitsu account: {str(e)}",
        )


@router.put("/{integration_type}", response_model=ExternalIntegrationSchema)
async def update_integration_settings(
    integration_type: IntegrationType,
    update_data: ExternalIntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update integration settings."""
    result = await db.execute(
        select(ExternalIntegration).where(
            (ExternalIntegration.user_id == current_user.id)
            & (ExternalIntegration.integration_type == integration_type)
        )
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{integration_type.value} integration not found",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(integration, field, value)

    await db.commit()
    await db.refresh(integration)

    return integration


@router.delete("/{integration_type}")
async def disconnect_integration(
    integration_type: IntegrationType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Disconnect an integration."""
    result = await db.execute(
        select(ExternalIntegration).where(
            (ExternalIntegration.user_id == current_user.id)
            & (ExternalIntegration.integration_type == integration_type)
        )
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{integration_type.value} integration not found",
        )

    await db.delete(integration)
    await db.commit()

    return {
        "message": f"{integration_type.value} integration disconnected successfully"
    }


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger manual sync for an integration."""
    result = await db.execute(
        select(ExternalIntegration).where(
            (ExternalIntegration.user_id == current_user.id)
            & (ExternalIntegration.integration_type == sync_request.integration_type)
        )
    )
    integration = result.scalars().first()

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{sync_request.integration_type.value} integration not found",
        )

    if not integration.sync_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sync is disabled for this integration",
        )

    # Update sync status to in progress
    integration.last_sync_status = SyncStatus.IN_PROGRESS
    await db.commit()

    # Add background task for actual syncing
    background_tasks.add_task(
        sync_integration_task,
        integration.id,
        sync_request.force_full_sync,
        sync_request.sync_direction,
    )

    return SyncResponse(
        integration_type=sync_request.integration_type,
        status=SyncStatus.IN_PROGRESS,
        message="Sync started successfully",
        started_at=datetime.utcnow(),
    )


async def sync_integration_task(
    integration_id: UUID,
    force_full_sync: bool = False,
    sync_direction: str = "bidirectional",
):
    """Background task for syncing integration data."""
    try:
        sync_service = SyncService()
        await sync_service.sync_integration(
            integration_id, force_full_sync, sync_direction
        )
        logger.info(f"Sync completed successfully for integration {integration_id}")
    except Exception as e:
        logger.error(f"Sync failed for integration {integration_id}: {e}")
