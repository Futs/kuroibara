import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.providers.base import BaseProvider
from app.core.providers.registry import provider_registry
from app.db.session import AsyncSessionLocal
from app.models.provider import ProviderStatus, ProviderStatusEnum

logger = logging.getLogger(__name__)


class ProviderMonitorService:
    """Service for monitoring provider health and availability."""

    def __init__(self):
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._is_running = False

    async def initialize_provider_statuses(self, db: AsyncSession) -> None:
        """Initialize provider status records for all registered providers."""
        try:
            providers = provider_registry.get_all_providers()

            for provider in providers:
                # Check if provider status already exists
                result = await db.execute(
                    select(ProviderStatus).where(
                        ProviderStatus.provider_id == provider.name.lower()
                    )
                )
                existing_status = result.scalar_one_or_none()

                if not existing_status:
                    # Create new provider status
                    provider_status = ProviderStatus(
                        provider_id=provider.name.lower(),
                        provider_name=provider.name,
                        provider_url=provider.url,
                        status=ProviderStatusEnum.UNKNOWN.value,
                        is_enabled=True,
                        check_interval=60,  # Default 60 minutes
                        max_consecutive_failures=3,
                    )
                    db.add(provider_status)
                    logger.info(f"Created provider status for {provider.name}")
                else:
                    # Update existing provider info if needed
                    if (
                        existing_status.provider_name != provider.name
                        or existing_status.provider_url != provider.url
                    ):
                        existing_status.provider_name = provider.name
                        existing_status.provider_url = provider.url
                        logger.info(f"Updated provider info for {provider.name}")

            await db.commit()
            logger.info(f"Initialized provider statuses for {len(providers)} providers")

        except Exception as e:
            logger.error(f"Error initializing provider statuses: {e}")
            await db.rollback()

    async def test_all_providers_on_startup(self) -> None:
        """Test all providers on application startup."""
        logger.info("Starting provider health checks on startup")

        async with AsyncSessionLocal() as db:
            await self.initialize_provider_statuses(db)

            providers = provider_registry.get_all_providers()

            # Test providers concurrently with a reasonable limit
            semaphore = asyncio.Semaphore(5)  # Limit concurrent checks

            async def test_provider_with_semaphore(provider: BaseProvider):
                async with semaphore:
                    await self._test_single_provider(provider, db)

            tasks = [test_provider_with_semaphore(provider) for provider in providers]
            await asyncio.gather(*tasks, return_exceptions=True)

            await db.commit()

        logger.info("Completed startup provider health checks")

    async def _test_single_provider(
        self, provider: BaseProvider, db: AsyncSession
    ) -> None:
        """Test a single provider and update its status."""
        try:
            logger.debug(f"Testing provider: {provider.name}")

            # Perform health check
            is_healthy, response_time, error_message = await provider.health_check(
                timeout=30
            )

            # Get provider status record
            result = await db.execute(
                select(ProviderStatus).where(
                    ProviderStatus.provider_id == provider.name.lower()
                )
            )
            provider_status = result.scalar_one_or_none()

            if provider_status:
                provider_status.update_status(is_healthy, response_time, error_message)

                # Check if provider should be auto-disabled or re-enabled
                auto_action = await self._check_auto_disable_enable(provider_status)
                if auto_action:
                    action, reason = auto_action
                    if action == "disable":
                        provider_status.is_enabled = False
                        logger.warning(f"Auto-disabled provider {provider.name}: {reason}")
                    elif action == "enable":
                        provider_status.is_enabled = True
                        logger.info(f"Auto-enabled provider {provider.name}: {reason}")

                logger.info(
                    f"Provider {provider.name}: {'HEALTHY' if is_healthy else 'UNHEALTHY'} "
                    f"({response_time}ms) {'[ENABLED]' if provider_status.is_enabled else '[DISABLED]'}"
                    + (f" - {error_message}" if error_message else "")
                )
            else:
                logger.warning(f"Provider status not found for {provider.name}")

        except Exception as e:
            logger.error(f"Error testing provider {provider.name}: {e}")

    async def _check_auto_disable_enable(self, provider_status: ProviderStatus) -> Optional[Tuple[str, str]]:
        """
        Check if a provider should be auto-disabled or re-enabled.

        Returns:
            Tuple of (action, reason) if action should be taken, None otherwise.
            action: "disable" or "enable"
            reason: Human-readable reason for the action
        """
        try:
            # Auto-disable criteria
            if bool(provider_status.is_enabled):
                # Disable if uptime is 0% and has been checked multiple times
                if (float(provider_status.uptime_percentage or 0) == 0.0 and
                    int(provider_status.total_checks or 0) >= 3):
                    return ("disable", f"0% uptime over {provider_status.total_checks} checks")

                # Disable if consecutive failures exceed threshold
                if (int(provider_status.consecutive_failures or 0) >= int(provider_status.max_consecutive_failures or 0) and
                    int(provider_status.max_consecutive_failures or 0) > 0):
                    return ("disable", f"{provider_status.consecutive_failures} consecutive failures")

                # Disable if no successful check in 48+ hours
                if (provider_status.last_check is not None and
                    int(provider_status.successful_checks or 0) == 0 and
                    provider_status.last_check < datetime.now(timezone.utc) - timedelta(hours=48)):
                    return ("disable", "No successful checks in 48+ hours")

            # Auto-enable criteria
            else:
                # Re-enable if provider becomes healthy after being disabled
                if (provider_status.status == ProviderStatusEnum.ACTIVE.value and
                    int(provider_status.consecutive_failures or 0) == 0):
                    return ("enable", "Provider is healthy again")

                # Re-enable if uptime improves significantly
                if (float(provider_status.uptime_percentage or 0) >= 50.0 and
                    int(provider_status.total_checks or 0) >= 5):
                    return ("enable", f"Uptime improved to {provider_status.uptime_percentage:.1f}%")

            return None

        except Exception as e:
            logger.error(f"Error checking auto-disable/enable for {provider_status.provider_name}: {e}")
            return None

    async def start_monitoring(self) -> None:
        """Start the provider monitoring service."""
        if self._is_running:
            logger.warning("Provider monitoring is already running")
            return

        self._is_running = True
        logger.info("Starting provider monitoring service")

        # Start monitoring task
        self._monitoring_tasks["main"] = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop the provider monitoring service."""
        if not self._is_running:
            return

        self._is_running = False
        logger.info("Stopping provider monitoring service")

        # Cancel all monitoring tasks
        for task_name, task in self._monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Cancelled monitoring task: {task_name}")

        self._monitoring_tasks.clear()

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that schedules provider checks."""
        while self._is_running:
            try:
                async with AsyncSessionLocal() as db:
                    # Get providers that need to be checked
                    now = datetime.now(timezone.utc)

                    result = await db.execute(
                        select(ProviderStatus).where(
                            ProviderStatus.is_enabled is True,
                            func.extract("epoch", now - ProviderStatus.last_check) / 60
                            >= ProviderStatus.check_interval,
                        )
                    )
                    providers_to_check = result.scalars().all()

                    if providers_to_check:
                        logger.info(f"Checking {len(providers_to_check)} providers")

                        # Check providers concurrently
                        semaphore = asyncio.Semaphore(3)  # Limit concurrent checks

                        async def check_provider_with_semaphore(provider_status):
                            async with semaphore:
                                await self._check_provider_by_status(
                                    provider_status, db
                                )

                        tasks = [
                            check_provider_with_semaphore(ps)
                            for ps in providers_to_check
                        ]
                        await asyncio.gather(*tasks, return_exceptions=True)

                        await db.commit()

                # Wait before next check cycle (check every 5 minutes)
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _check_provider_by_status(
        self, provider_status: ProviderStatus, db: AsyncSession
    ) -> None:
        """Check a provider based on its status record."""
        try:
            # Get the actual provider instance
            provider = provider_registry.get_provider(provider_status.provider_id)
            if not provider:
                logger.warning(
                    f"Provider not found in registry: {provider_status.provider_id}"
                )
                return

            # Perform health check
            is_healthy, response_time, error_message = await provider.health_check(
                timeout=30
            )

            # Update status
            provider_status.update_status(is_healthy, response_time, error_message)

            logger.debug(
                f"Checked provider {provider.name}: {'HEALTHY' if is_healthy else 'UNHEALTHY'}"
            )

        except Exception as e:
            logger.error(
                f"Error checking provider {provider_status.provider_name}: {e}"
            )

    async def get_provider_statuses(self, db: AsyncSession) -> List[ProviderStatus]:
        """Get all provider statuses."""
        result = await db.execute(select(ProviderStatus))
        return result.scalars().all()

    async def update_provider_settings(
        self,
        db: AsyncSession,
        provider_id: str,
        is_enabled: Optional[bool] = None,
        check_interval: Optional[int] = None,
    ) -> Optional[ProviderStatus]:
        """Update provider monitoring settings."""
        result = await db.execute(
            select(ProviderStatus).where(ProviderStatus.provider_id == provider_id)
        )
        provider_status = result.scalar_one_or_none()

        if not provider_status:
            return None

        if is_enabled is not None:
            provider_status.is_enabled = is_enabled

        if check_interval is not None:
            provider_status.check_interval = check_interval

        await db.commit()
        return provider_status

    async def daily_health_check(self) -> Dict[str, any]:
        """
        Perform comprehensive daily health check on all providers.
        This is designed to be called by a scheduled job.

        Returns:
            Dictionary with health check results and actions taken.
        """
        logger.info("Starting daily provider health check")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_providers": 0,
            "healthy_providers": 0,
            "unhealthy_providers": 0,
            "disabled_providers": 0,
            "enabled_providers": 0,
            "actions_taken": [],
            "provider_details": []
        }

        try:
            async with AsyncSessionLocal() as db:
                # Get all provider statuses
                result = await db.execute(select(ProviderStatus))
                provider_statuses = result.scalars().all()

                results["total_providers"] = len(provider_statuses)

                # Test all providers concurrently
                semaphore = asyncio.Semaphore(10)  # Limit concurrent checks

                async def check_provider_with_semaphore(provider_status: ProviderStatus):
                    async with semaphore:
                        return await self._daily_check_single_provider(provider_status, db, results)

                tasks = [check_provider_with_semaphore(ps) for ps in provider_statuses]
                await asyncio.gather(*tasks, return_exceptions=True)

                await db.commit()

                # Log summary
                logger.info(
                    f"Daily health check completed: "
                    f"{results['healthy_providers']}/{results['total_providers']} healthy, "
                    f"{results['enabled_providers']} enabled, "
                    f"{len(results['actions_taken'])} actions taken"
                )

        except Exception as e:
            logger.error(f"Error in daily health check: {e}")
            results["error"] = str(e)

        return results

    async def _daily_check_single_provider(
        self, provider_status: ProviderStatus, db: AsyncSession, results: Dict[str, any]
    ) -> None:
        """Check a single provider during daily health check."""
        try:
            # Get the actual provider instance
            provider = provider_registry.get_provider(provider_status.provider_name)
            if not provider:
                logger.warning(f"Provider {provider_status.provider_name} not found in registry")
                return

            # Perform health check
            is_healthy, response_time, error_message = await provider.health_check(timeout=30)

            # Update status
            provider_status.update_status(is_healthy, response_time, error_message)

            # Check for auto-disable/enable actions
            auto_action = await self._check_auto_disable_enable(provider_status)
            if auto_action:
                action, reason = auto_action
                old_status = "enabled" if provider_status.is_enabled else "disabled"

                if action == "disable":
                    provider_status.is_enabled = False
                    results["actions_taken"].append({
                        "provider": provider_status.provider_name,
                        "action": "disabled",
                        "reason": reason,
                        "previous_status": old_status
                    })
                    logger.warning(f"Daily check auto-disabled {provider_status.provider_name}: {reason}")

                elif action == "enable":
                    provider_status.is_enabled = True
                    results["actions_taken"].append({
                        "provider": provider_status.provider_name,
                        "action": "enabled",
                        "reason": reason,
                        "previous_status": old_status
                    })
                    logger.info(f"Daily check auto-enabled {provider_status.provider_name}: {reason}")

            # Update results
            if is_healthy:
                results["healthy_providers"] = results.get("healthy_providers", 0) + 1
            else:
                results["unhealthy_providers"] = results.get("unhealthy_providers", 0) + 1

            if provider_status.is_enabled:
                results["enabled_providers"] = results.get("enabled_providers", 0) + 1
            else:
                results["disabled_providers"] = results.get("disabled_providers", 0) + 1

            # Add provider details
            results["provider_details"].append({
                "name": provider_status.provider_name,
                "status": "healthy" if is_healthy else "unhealthy",
                "enabled": provider_status.is_enabled,
                "uptime": provider_status.uptime_percentage,
                "consecutive_failures": provider_status.consecutive_failures,
                "response_time": response_time,
                "error": error_message
            })

        except Exception as e:
            logger.error(f"Error in daily check for {provider_status.provider_name}: {e}")
            results["unhealthy_providers"] += 1


# Global instance
provider_monitor = ProviderMonitorService()
