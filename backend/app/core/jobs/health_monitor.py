"""
Enhanced Provider Health Monitoring System.

This module provides comprehensive health monitoring for manga providers
including automated health checks, performance tracking, and provider
status management.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .events import JobPriority, JobType
from .models import HealthCheckJob

logger = logging.getLogger(__name__)


class ProviderHealthStatus(Enum):
    """Health status of a provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


class HealthCheckType(Enum):
    """Types of health checks."""

    BASIC = "basic"  # Basic connectivity and search
    COMPREHENSIVE = "comprehensive"  # Full functionality test
    PERFORMANCE = "performance"  # Performance benchmarking
    SCHEDULED = "scheduled"  # Regular scheduled check
    MANUAL = "manual"  # User-initiated check


@dataclass
class HealthMetrics:
    """Health metrics for a provider."""

    provider_name: str
    status: ProviderHealthStatus = ProviderHealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

    # Performance metrics
    average_response_time: float = 0.0
    success_rate: float = 0.0
    requests_per_minute: float = 0.0

    # Error tracking
    consecutive_failures: int = 0
    total_failures: int = 0
    total_successes: int = 0

    # Health check history
    recent_checks: List[Dict[str, Any]] = field(default_factory=list)

    # Status tracking
    status_changed_at: Optional[datetime] = None
    auto_disabled: bool = False
    manual_override: bool = False

    def update_success(self, response_time: float) -> None:
        """Update metrics after a successful check."""
        now = datetime.utcnow()
        self.last_check = now
        self.last_success = now
        self.consecutive_failures = 0
        self.total_successes += 1

        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            # Exponential moving average
            self.average_response_time = (self.average_response_time * 0.8) + (
                response_time * 0.2
            )

        # Update success rate
        total_requests = self.total_successes + self.total_failures
        if total_requests > 0:
            self.success_rate = (self.total_successes / total_requests) * 100

        # Update status based on metrics
        self._update_status()

    def update_failure(self, error_message: str) -> None:
        """Update metrics after a failed check."""
        now = datetime.utcnow()
        self.last_check = now
        self.last_failure = now
        self.consecutive_failures += 1
        self.total_failures += 1

        # Update success rate
        total_requests = self.total_successes + self.total_failures
        if total_requests > 0:
            self.success_rate = (self.total_successes / total_requests) * 100

        # Add to recent checks
        self.recent_checks.append(
            {"timestamp": now.isoformat(), "status": "failed", "error": error_message}
        )

        # Keep only recent checks (last 10)
        self.recent_checks = self.recent_checks[-10:]

        # Update status based on metrics
        self._update_status()

    def _update_status(self) -> None:
        """Update health status based on current metrics."""
        if self.manual_override:
            return  # Don't auto-update if manually overridden

        old_status = self.status

        # Determine new status
        if self.consecutive_failures >= 5:
            new_status = ProviderHealthStatus.UNHEALTHY
        elif self.consecutive_failures >= 3:
            new_status = ProviderHealthStatus.DEGRADED
        elif (
            self.success_rate < 80 and self.total_successes + self.total_failures >= 10
        ):
            new_status = ProviderHealthStatus.DEGRADED
        elif self.success_rate >= 95 or self.consecutive_failures == 0:
            new_status = ProviderHealthStatus.HEALTHY
        else:
            new_status = ProviderHealthStatus.DEGRADED

        # Update status if changed
        if new_status != old_status:
            self.status = new_status
            self.status_changed_at = datetime.utcnow()
            logger.info(
                f"Provider {self.provider_name} status changed: {old_status.value} -> {new_status.value}"
            )

    def get_health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        if self.status == ProviderHealthStatus.DISABLED:
            return 0.0

        # Base score from success rate
        score = self.success_rate

        # Penalty for consecutive failures
        failure_penalty = min(self.consecutive_failures * 10, 50)
        score -= failure_penalty

        # Bonus for recent success
        if self.last_success and datetime.utcnow() - self.last_success < timedelta(
            hours=1
        ):
            score += 10

        # Response time factor
        if self.average_response_time > 0:
            if self.average_response_time < 1.0:
                score += 5  # Fast response bonus
            elif self.average_response_time > 5.0:
                score -= 10  # Slow response penalty

        return max(0.0, min(100.0, score))


class EnhancedHealthMonitor:
    """
    Enhanced health monitoring system for providers.

    Features:
    - Automated health checks
    - Performance monitoring
    - Provider status management
    - Health-based provider selection
    - Integration with job queue
    """

    def __init__(self, queue_manager=None):
        self.queue_manager = queue_manager
        self._provider_metrics: Dict[str, HealthMetrics] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._is_running = False

        # Configuration
        self.check_interval = 300  # 5 minutes
        self.performance_check_interval = 3600  # 1 hour
        self.failure_threshold = 5
        self.degraded_threshold = 3

        logger.info("EnhancedHealthMonitor initialized")

    async def start(self) -> None:
        """Start health monitoring."""
        if self._is_running:
            return

        self._is_running = True

        # Start monitoring for all known providers
        await self._initialize_providers()

        # Start scheduled health checks
        for provider_name in self._provider_metrics:
            await self._start_provider_monitoring(provider_name)

        logger.info("Enhanced health monitoring started")

    async def stop(self) -> None:
        """Stop health monitoring."""
        self._is_running = False

        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._monitoring_tasks.clear()
        logger.info("Enhanced health monitoring stopped")

    async def _initialize_providers(self) -> None:
        """Initialize health metrics for all providers."""
        try:
            from ...agents import agent_registry

            agents = agent_registry.get_all_agents()

            for agent in agents:
                if agent.name not in self._provider_metrics:
                    self._provider_metrics[agent.name] = HealthMetrics(
                        provider_name=agent.name
                    )
                    logger.debug(f"Initialized health metrics for {agent.name}")

        except ImportError:
            logger.warning("Agent registry not available for provider initialization")

    async def _start_provider_monitoring(self, provider_name: str) -> None:
        """Start monitoring for a specific provider."""
        if provider_name in self._monitoring_tasks:
            return

        task = asyncio.create_task(self._monitor_provider(provider_name))
        self._monitoring_tasks[provider_name] = task

        logger.debug(f"Started monitoring for provider {provider_name}")

    async def _monitor_provider(self, provider_name: str) -> None:
        """Monitor a provider with scheduled health checks."""
        while self._is_running:
            try:
                # Schedule basic health check
                await self.schedule_health_check(
                    provider_name,
                    HealthCheckType.SCHEDULED,
                    test_search=True,
                    test_metadata=True,
                )

                # Wait for next check
                await asyncio.sleep(self.check_interval)

                # Occasionally run performance checks
                if datetime.utcnow().minute == 0:  # Once per hour
                    await self.schedule_health_check(
                        provider_name,
                        HealthCheckType.PERFORMANCE,
                        test_search=True,
                        test_metadata=True,
                        test_download=True,
                        performance_benchmark=True,
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in provider monitoring for {provider_name}: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def schedule_health_check(
        self,
        provider_name: str,
        check_type: HealthCheckType = HealthCheckType.BASIC,
        test_search: bool = True,
        test_metadata: bool = True,
        test_download: bool = False,
        performance_benchmark: bool = False,
    ) -> Optional[str]:
        """
        Schedule a health check job for a provider.

        Returns:
            Job ID if scheduled successfully
        """
        if not self.queue_manager:
            logger.warning("No queue manager available for health check scheduling")
            return None

        # Create health check job
        job = HealthCheckJob(
            provider_name=provider_name,
            check_type=check_type.value,
            test_search=test_search,
            test_metadata=test_metadata,
            test_download=test_download,
            performance_benchmark=performance_benchmark,
            priority=(
                JobPriority.CRITICAL
                if check_type == HealthCheckType.MANUAL
                else JobPriority.HIGH
            ),
        )

        # Add to queue
        job_id = self.queue_manager.add_job(job)

        logger.debug(
            f"Scheduled {check_type.value} health check for {provider_name}: {job_id}"
        )
        return job_id

    def update_health_metrics(
        self,
        provider_name: str,
        success: bool,
        response_time: float = 0.0,
        error_message: str = "",
    ) -> None:
        """Update health metrics for a provider."""
        if provider_name not in self._provider_metrics:
            self._provider_metrics[provider_name] = HealthMetrics(
                provider_name=provider_name
            )

        metrics = self._provider_metrics[provider_name]

        if success:
            metrics.update_success(response_time)
            logger.debug(
                f"Updated success metrics for {provider_name}: {response_time:.2f}s"
            )
        else:
            metrics.update_failure(error_message)
            logger.warning(
                f"Updated failure metrics for {provider_name}: {error_message}"
            )

        # Auto-disable provider if too many failures
        if (
            metrics.consecutive_failures >= self.failure_threshold
            and not metrics.auto_disabled
        ):
            self.disable_provider(
                provider_name,
                auto=True,
                reason=f"Too many consecutive failures ({metrics.consecutive_failures})",
            )

    def get_provider_health(self, provider_name: str) -> Optional[HealthMetrics]:
        """Get health metrics for a provider."""
        return self._provider_metrics.get(provider_name)

    def get_all_provider_health(self) -> Dict[str, HealthMetrics]:
        """Get health metrics for all providers."""
        return self._provider_metrics.copy()

    def get_healthy_providers(self) -> List[str]:
        """Get list of healthy providers."""
        return [
            name
            for name, metrics in self._provider_metrics.items()
            if metrics.status == ProviderHealthStatus.HEALTHY
        ]

    def get_provider_ranking(self) -> List[tuple]:
        """Get providers ranked by health score."""
        rankings = []
        for name, metrics in self._provider_metrics.items():
            if metrics.status != ProviderHealthStatus.DISABLED:
                rankings.append((name, metrics.get_health_score()))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def disable_provider(
        self, provider_name: str, auto: bool = False, reason: str = ""
    ) -> bool:
        """Disable a provider."""
        if provider_name not in self._provider_metrics:
            return False

        metrics = self._provider_metrics[provider_name]
        old_status = metrics.status

        metrics.status = ProviderHealthStatus.DISABLED
        metrics.status_changed_at = datetime.utcnow()
        metrics.auto_disabled = auto

        logger.warning(
            f"Disabled provider {provider_name} ({'auto' if auto else 'manual'}): {reason}"
        )

        # Try to disable in agent registry
        try:
            from ...agents import agent_registry

            agent = agent_registry.get_agent(provider_name)
            if agent:
                agent.status = "DISABLED"  # Assuming agent has status attribute
        except ImportError:
            pass

        return True

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider."""
        if provider_name not in self._provider_metrics:
            return False

        metrics = self._provider_metrics[provider_name]

        # Reset failure counters
        metrics.consecutive_failures = 0
        metrics.auto_disabled = False
        metrics.manual_override = False
        metrics.status = ProviderHealthStatus.UNKNOWN
        metrics.status_changed_at = datetime.utcnow()

        logger.info(f"Enabled provider {provider_name}")

        # Try to enable in agent registry
        try:
            from ...agents import agent_registry

            agent = agent_registry.get_agent(provider_name)
            if agent:
                agent.status = "ACTIVE"  # Assuming agent has status attribute
        except ImportError:
            pass

        # Schedule immediate health check
        asyncio.create_task(
            self.schedule_health_check(provider_name, HealthCheckType.MANUAL)
        )

        return True

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        total_providers = len(self._provider_metrics)
        healthy_count = len(
            [
                m
                for m in self._provider_metrics.values()
                if m.status == ProviderHealthStatus.HEALTHY
            ]
        )
        degraded_count = len(
            [
                m
                for m in self._provider_metrics.values()
                if m.status == ProviderHealthStatus.DEGRADED
            ]
        )
        unhealthy_count = len(
            [
                m
                for m in self._provider_metrics.values()
                if m.status == ProviderHealthStatus.UNHEALTHY
            ]
        )
        disabled_count = len(
            [
                m
                for m in self._provider_metrics.values()
                if m.status == ProviderHealthStatus.DISABLED
            ]
        )

        return {
            "total_providers": total_providers,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "disabled": disabled_count,
            "overall_health_percentage": (healthy_count / max(1, total_providers))
            * 100,
            "monitoring_active": self._is_running,
            "active_monitoring_tasks": len(self._monitoring_tasks),
        }


# Global health monitor instance
health_monitor = EnhancedHealthMonitor()
