import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.providers.registry import provider_registry
from app.core.services.provider_monitor import provider_monitor
from app.db.session import AsyncSessionLocal
from app.models.provider import ProviderStatus
from app.models.user import User
from app.schemas.provider import (
    ProviderCheckIntervalUpdate,
    ProviderHealthCheck,
    ProviderInfo,
)
from app.schemas.provider import ProviderStatus as ProviderStatusSchema
from app.schemas.provider import (
    ProviderStatusUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ProviderInfo])
async def get_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get available providers with their health status.
    """
    try:
        # Get provider info from registry
        provider_info_list = provider_registry.get_provider_info()

        # Get provider statuses from database
        result = await db.execute(select(ProviderStatus))
        provider_statuses = {ps.provider_id: ps for ps in result.scalars().all()}

        # Combine provider info with status
        enhanced_providers = []
        for provider_info in provider_info_list:
            provider_id = provider_info["id"]
            status_record = provider_statuses.get(provider_id)

            enhanced_provider = ProviderInfo(
                id=provider_info["id"],
                name=provider_info["name"],
                url=provider_info["url"],
                supports_nsfw=provider_info["supports_nsfw"],
                status=status_record.status if status_record else "unknown",
                is_enabled=status_record.is_enabled if status_record else True,
                last_check=status_record.last_check if status_record else None,
                response_time=status_record.response_time if status_record else None,
                uptime_percentage=(
                    status_record.uptime_percentage if status_record else 100
                ),
                consecutive_failures=(
                    status_record.consecutive_failures if status_record else 0
                ),
                is_healthy=status_record.is_healthy if status_record else True,
            )
            enhanced_providers.append(enhanced_provider)

        return enhanced_providers

    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get providers",
        )


@router.get("/status", response_model=List[ProviderStatusSchema])
async def get_provider_statuses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get detailed status information for all providers.
    """
    try:
        statuses = await provider_monitor.get_provider_statuses(db)
        return statuses
    except Exception as e:
        logger.error(f"Error getting provider statuses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider statuses",
        )


@router.patch("/{provider_id}/status", response_model=ProviderStatusSchema)
async def update_provider_status(
    provider_id: str,
    status_update: ProviderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update provider monitoring settings.
    """
    # Check if user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can modify provider settings",
        )

    try:
        # Get provider status
        result = await db.execute(
            select(ProviderStatus).where(ProviderStatus.provider_id == provider_id)
        )
        provider_status = result.scalar_one_or_none()

        if not provider_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_id}' not found",
            )

        # Update fields
        if status_update.status is not None:
            provider_status.status = status_update.status
        if status_update.is_enabled is not None:
            provider_status.is_enabled = status_update.is_enabled
        if status_update.check_interval is not None:
            provider_status.check_interval = status_update.check_interval
        if status_update.max_consecutive_failures is not None:
            provider_status.max_consecutive_failures = (
                status_update.max_consecutive_failures
            )

        await db.commit()
        await db.refresh(provider_status)

        logger.info(
            f"Updated provider {provider_id} settings by user {current_user.username}"
        )
        return provider_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider status: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider status",
        )


@router.post("/{provider_id}/test", response_model=ProviderHealthCheck)
async def test_provider(
    provider_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Manually test a provider's health.
    """
    try:
        # Get provider from registry
        provider = provider_registry.get_provider(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_id}' not found",
            )

        # Perform health check
        is_success, response_time, error_message = await provider.health_check(
            timeout=30
        )

        # Update provider status in background
        async def update_status():
            async with AsyncSessionLocal() as bg_db:
                result = await bg_db.execute(
                    select(ProviderStatus).where(
                        ProviderStatus.provider_id == provider_id
                    )
                )
                provider_status = result.scalar_one_or_none()

                if provider_status:
                    provider_status.update_status(
                        is_success, response_time, error_message
                    )
                    await bg_db.commit()

        background_tasks.add_task(update_status)

        return ProviderHealthCheck(
            provider_id=provider_id,
            is_success=is_success,
            response_time=response_time,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test provider",
        )


@router.patch("/check-interval", response_model=dict)
async def update_user_check_interval(
    interval_update: ProviderCheckIntervalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update user's provider check interval preference.
    """
    # Validate interval values
    valid_intervals = [
        30,
        60,
        120,
        1440,
        10080,
        43200,
    ]  # 30min, 1h, 2h, daily, weekly, monthly
    if interval_update.interval not in valid_intervals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interval. Must be one of: {valid_intervals}",
        )

    try:
        current_user.provider_check_interval = interval_update.interval
        await db.commit()

        logger.info(
            f"Updated check interval for user {current_user.username} to {interval_update.interval} minutes"
        )

        return {
            "message": "Check interval updated successfully",
            "interval": interval_update.interval,
        }

    except Exception as e:
        logger.error(f"Error updating check interval: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update check interval",
        )


@router.get("/statistics", response_model=dict)
async def get_provider_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get provider statistics and health overview.
    """
    try:
        result = await db.execute(select(ProviderStatus))
        statuses = result.scalars().all()

        total_providers = len(statuses)
        active_providers = len([s for s in statuses if s.status == "active"])
        down_providers = len([s for s in statuses if s.status == "down"])
        unknown_providers = len([s for s in statuses if s.status == "unknown"])
        enabled_providers = len([s for s in statuses if s.is_enabled])

        # Calculate average uptime
        avg_uptime = (
            sum(s.uptime_percentage for s in statuses) / total_providers
            if total_providers > 0
            else 0
        )

        # Get fastest and slowest providers
        providers_with_response_time = [
            s for s in statuses if s.response_time is not None
        ]
        fastest_provider = (
            min(providers_with_response_time, key=lambda x: x.response_time)
            if providers_with_response_time
            else None
        )
        slowest_provider = (
            max(providers_with_response_time, key=lambda x: x.response_time)
            if providers_with_response_time
            else None
        )

        return {
            "total_providers": total_providers,
            "active_providers": active_providers,
            "down_providers": down_providers,
            "unknown_providers": unknown_providers,
            "enabled_providers": enabled_providers,
            "disabled_providers": total_providers - enabled_providers,
            "average_uptime_percentage": round(avg_uptime, 2),
            "fastest_provider": (
                {
                    "name": fastest_provider.provider_name,
                    "response_time": fastest_provider.response_time,
                }
                if fastest_provider
                else None
            ),
            "slowest_provider": (
                {
                    "name": slowest_provider.provider_name,
                    "response_time": slowest_provider.response_time,
                }
                if slowest_provider
                else None
            ),
            "health_distribution": {
                "active": active_providers,
                "down": down_providers,
                "unknown": unknown_providers,
            },
        }

    except Exception as e:
        logger.error(f"Error getting provider statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider statistics",
        )


@router.post("/health-check/daily")
async def trigger_daily_health_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Manually trigger a daily provider health check.
    This will check all providers and auto-disable/enable based on health criteria.
    """
    try:
        # Run health check in background
        background_tasks.add_task(provider_monitor.daily_health_check)

        return {
            "message": "Daily provider health check started",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        logger.error(f"Error triggering daily health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger health check",
        )


@router.get("/health-status")
async def get_provider_health_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get detailed health status for all providers including auto-disable/enable information.
    """
    try:
        # Get all provider statuses
        result = await db.execute(select(ProviderStatus))
        provider_statuses = result.scalars().all()

        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_providers": len(provider_statuses),
                "enabled_providers": 0,
                "disabled_providers": 0,
                "healthy_providers": 0,
                "unhealthy_providers": 0,
                "auto_disabled_providers": 0
            },
            "providers": []
        }

        for ps in provider_statuses:
            # Determine if provider was auto-disabled
            is_auto_disabled = (
                not ps.is_enabled and
                (ps.uptime_percentage == 0.0 or
                 ps.consecutive_failures >= ps.max_consecutive_failures)
            )

            provider_info = {
                "name": ps.provider_name,
                "id": ps.provider_id,
                "enabled": ps.is_enabled,
                "status": ps.status,
                "uptime_percentage": ps.uptime_percentage,
                "consecutive_failures": ps.consecutive_failures,
                "max_consecutive_failures": ps.max_consecutive_failures,
                "total_checks": ps.total_checks,
                "successful_checks": ps.successful_checks,
                "last_check": ps.last_check.isoformat() if ps.last_check else None,
                "last_success": ps.last_success.isoformat() if ps.last_success else None,
                "average_response_time": ps.average_response_time,
                "auto_disabled": is_auto_disabled,
                "last_error": ps.last_error_message
            }

            health_status["providers"].append(provider_info)

            # Update summary
            if ps.is_enabled:
                health_status["summary"]["enabled_providers"] += 1
            else:
                health_status["summary"]["disabled_providers"] += 1

            if ps.status == "healthy":
                health_status["summary"]["healthy_providers"] += 1
            else:
                health_status["summary"]["unhealthy_providers"] += 1

            if is_auto_disabled:
                health_status["summary"]["auto_disabled_providers"] += 1

        # Sort providers by name
        health_status["providers"].sort(key=lambda x: x["name"])

        return health_status

    except Exception as e:
        logger.error(f"Error getting provider health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider health status",
        )


@router.post("/enable/{provider_id}")
async def manually_enable_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Manually enable a provider (override auto-disable).
    """
    try:
        # Get provider status
        result = await db.execute(
            select(ProviderStatus).where(ProviderStatus.provider_id == provider_id)
        )
        provider_status = result.scalar_one_or_none()

        if not provider_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_id}' not found",
            )

        # Enable the provider
        provider_status.is_enabled = True
        await db.commit()

        logger.info(f"Provider {provider_id} manually enabled by user {current_user.email}")

        return {
            "message": f"Provider '{provider_status.provider_name}' enabled",
            "provider_id": provider_id,
            "enabled": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable provider",
        )


@router.post("/disable/{provider_id}")
async def manually_disable_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Manually disable a provider.
    """
    try:
        # Get provider status
        result = await db.execute(
            select(ProviderStatus).where(ProviderStatus.provider_id == provider_id)
        )
        provider_status = result.scalar_one_or_none()

        if not provider_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider_id}' not found",
            )

        # Disable the provider
        provider_status.is_enabled = False
        await db.commit()

        logger.info(f"Provider {provider_id} manually disabled by user {current_user.email}")

        return {
            "message": f"Provider '{provider_status.provider_name}' disabled",
            "provider_id": provider_id,
            "enabled": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable provider",
        )
