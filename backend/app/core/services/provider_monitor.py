import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.db.session import AsyncSessionLocal
from app.models.provider import ProviderStatus, ProviderStatusEnum
from app.core.providers.registry import provider_registry
from app.core.providers.base import BaseProvider

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
                    select(ProviderStatus).where(ProviderStatus.provider_id == provider.name.lower())
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
                        max_consecutive_failures=3
                    )
                    db.add(provider_status)
                    logger.info(f"Created provider status for {provider.name}")
                else:
                    # Update existing provider info if needed
                    if (existing_status.provider_name != provider.name or 
                        existing_status.provider_url != provider.url):
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

    async def _test_single_provider(self, provider: BaseProvider, db: AsyncSession) -> None:
        """Test a single provider and update its status."""
        try:
            logger.debug(f"Testing provider: {provider.name}")
            
            # Perform health check
            is_healthy, response_time, error_message = await provider.health_check(timeout=30)
            
            # Get provider status record
            result = await db.execute(
                select(ProviderStatus).where(ProviderStatus.provider_id == provider.name.lower())
            )
            provider_status = result.scalar_one_or_none()
            
            if provider_status:
                provider_status.update_status(is_healthy, response_time, error_message)
                logger.info(f"Provider {provider.name}: {'HEALTHY' if is_healthy else 'UNHEALTHY'} "
                           f"({response_time}ms)" + (f" - {error_message}" if error_message else ""))
            else:
                logger.warning(f"Provider status not found for {provider.name}")
                
        except Exception as e:
            logger.error(f"Error testing provider {provider.name}: {e}")

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
                            ProviderStatus.is_enabled == True,
                            func.extract('epoch', now - ProviderStatus.last_check) / 60 >= ProviderStatus.check_interval
                        )
                    )
                    providers_to_check = result.scalars().all()
                    
                    if providers_to_check:
                        logger.info(f"Checking {len(providers_to_check)} providers")
                        
                        # Check providers concurrently
                        semaphore = asyncio.Semaphore(3)  # Limit concurrent checks
                        
                        async def check_provider_with_semaphore(provider_status):
                            async with semaphore:
                                await self._check_provider_by_status(provider_status, db)
                        
                        tasks = [check_provider_with_semaphore(ps) for ps in providers_to_check]
                        await asyncio.gather(*tasks, return_exceptions=True)
                        
                        await db.commit()
                
                # Wait before next check cycle (check every 5 minutes)
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _check_provider_by_status(self, provider_status: ProviderStatus, db: AsyncSession) -> None:
        """Check a provider based on its status record."""
        try:
            # Get the actual provider instance
            provider = provider_registry.get_provider(provider_status.provider_id)
            if not provider:
                logger.warning(f"Provider not found in registry: {provider_status.provider_id}")
                return
            
            # Perform health check
            is_healthy, response_time, error_message = await provider.health_check(timeout=30)
            
            # Update status
            provider_status.update_status(is_healthy, response_time, error_message)
            
            logger.debug(f"Checked provider {provider.name}: {'HEALTHY' if is_healthy else 'UNHEALTHY'}")
            
        except Exception as e:
            logger.error(f"Error checking provider {provider_status.provider_name}: {e}")

    async def get_provider_statuses(self, db: AsyncSession) -> List[ProviderStatus]:
        """Get all provider statuses."""
        result = await db.execute(select(ProviderStatus))
        return result.scalars().all()

    async def update_provider_settings(
        self, 
        db: AsyncSession, 
        provider_id: str, 
        is_enabled: Optional[bool] = None,
        check_interval: Optional[int] = None
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


# Global instance
provider_monitor = ProviderMonitorService()
