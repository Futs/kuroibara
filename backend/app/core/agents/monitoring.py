"""
Agent monitoring and metrics collection system.

This module provides comprehensive monitoring capabilities for agents including
performance tracking, health monitoring, alerting, and metrics aggregation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import AgentStatus
from .registry import agent_registry

logger = logging.getLogger(__name__)


class AgentMonitor:
    """
    Comprehensive monitoring system for agents.

    Features:
    - Real-time performance tracking
    - Health monitoring with alerts
    - Metrics aggregation and reporting
    - Performance trend analysis
    - Automatic health checks
    """

    def __init__(self):
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._health_check_interval = 300  # 5 minutes
        self._metrics_retention_hours = 24
        self._performance_thresholds = {
            "max_response_time": 30.0,  # seconds
            "min_success_rate": 80.0,  # percentage
            "max_error_rate": 20.0,  # percentage
        }

        # Historical metrics storage (in production, this would be a database)
        self._historical_metrics: Dict[str, List[Dict[str, Any]]] = {}

    async def start_monitoring(self) -> None:
        """Start the monitoring system."""
        if self._monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Agent monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Agent monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                await self._perform_health_checks()
                await self._collect_metrics()
                await self._analyze_performance()
                await self._cleanup_old_metrics()

                # Wait for next monitoring cycle
                await asyncio.sleep(self._health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all agents."""
        agents = agent_registry.get_all_agents()

        if not agents:
            return

        logger.debug(f"Performing health checks on {len(agents)} agents")

        # Limit concurrent health checks
        semaphore = asyncio.Semaphore(5)

        async def check_agent_health(agent):
            async with semaphore:
                try:
                    is_healthy, response_time, error_message = await agent.health_check(
                        timeout=30
                    )

                    # Record health check result
                    self._record_health_check(
                        agent.name, is_healthy, response_time, error_message
                    )

                    # Check for performance issues
                    await self._check_performance_alerts(
                        agent, response_time, is_healthy
                    )

                except Exception as e:
                    logger.error(f"Health check failed for agent {agent.name}: {e}")
                    self._record_health_check(agent.name, False, None, str(e))

        # Run health checks concurrently
        tasks = [check_agent_health(agent) for agent in agents]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _record_health_check(
        self,
        agent_name: str,
        is_healthy: bool,
        response_time: Optional[int],
        error_message: Optional[str],
    ) -> None:
        """Record a health check result."""
        if agent_name not in self._historical_metrics:
            self._historical_metrics[agent_name] = []

        health_record = {
            "timestamp": datetime.utcnow(),
            "type": "health_check",
            "is_healthy": is_healthy,
            "response_time": response_time,
            "error_message": error_message,
        }

        self._historical_metrics[agent_name].append(health_record)

    async def _check_performance_alerts(
        self, agent, response_time: Optional[int], is_healthy: bool
    ) -> None:
        """Check for performance issues and generate alerts."""
        alerts = []

        # Check response time
        if (
            response_time
            and response_time > self._performance_thresholds["max_response_time"] * 1000
        ):
            alerts.append(f"High response time: {response_time}ms")

        # Check success rate
        if agent.metrics.total_requests > 10:  # Only check if we have enough data
            success_rate = agent.metrics.success_rate
            if success_rate < self._performance_thresholds["min_success_rate"]:
                alerts.append(f"Low success rate: {success_rate:.1f}%")

        # Check if agent is unhealthy
        if not is_healthy:
            alerts.append("Health check failed")

        # Check circuit breaker status
        if agent.status == AgentStatus.CIRCUIT_OPEN:
            alerts.append("Circuit breaker is open")

        # Log alerts
        for alert in alerts:
            logger.warning(f"ALERT - Agent {agent.name}: {alert}")

    async def _collect_metrics(self) -> None:
        """Collect current metrics from all agents."""
        agents = agent_registry.get_all_agents()

        for agent in agents:
            if agent.name not in self._historical_metrics:
                self._historical_metrics[agent.name] = []

            metrics_record = {
                "timestamp": datetime.utcnow(),
                "type": "metrics",
                "total_requests": agent.metrics.total_requests,
                "successful_requests": agent.metrics.successful_requests,
                "failed_requests": agent.metrics.failed_requests,
                "success_rate": agent.metrics.success_rate,
                "average_response_time": agent.metrics.average_response_time,
                "status": agent.status.value,
                "circuit_breaker_count": agent.metrics.circuit_breaker_count,
            }

            self._historical_metrics[agent.name].append(metrics_record)

    async def _analyze_performance(self) -> None:
        """Analyze performance trends and patterns."""
        # This could include trend analysis, anomaly detection, etc.
        # For now, we'll do basic performance analysis

        for agent_name, metrics in self._historical_metrics.items():
            if len(metrics) < 2:
                continue

            # Get recent metrics (last hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_metrics = [
                m
                for m in metrics
                if m["timestamp"] > recent_cutoff and m["type"] == "metrics"
            ]

            if len(recent_metrics) >= 2:
                # Analyze trends
                first_metric = recent_metrics[0]
                last_metric = recent_metrics[-1]

                # Check for degrading performance
                if (
                    last_metric["success_rate"] < first_metric["success_rate"] - 10
                    and last_metric["success_rate"] < 70
                ):
                    logger.warning(
                        f"Performance degradation detected for agent {agent_name}"
                    )

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory bloat."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self._metrics_retention_hours)

        for agent_name in self._historical_metrics:
            self._historical_metrics[agent_name] = [
                metric
                for metric in self._historical_metrics[agent_name]
                if metric["timestamp"] > cutoff_time
            ]

    def get_agent_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all agent metrics including rate limiting."""
        agents = agent_registry.get_all_agents()

        summary = {
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.status == AgentStatus.ACTIVE]),
            "unhealthy_agents": len([a for a in agents if not a.is_healthy()]),
            "agents": [],
        }

        # Get rate limiting metrics
        try:
            from .rate_limiting import rate_limiter_manager

            rate_limit_metrics = rate_limiter_manager.get_all_metrics()
        except ImportError:
            rate_limit_metrics = {}

        # Get progress tracking metrics
        try:
            from ..progress import progress_tracker

            progress_operations = progress_tracker.get_operations()
            progress_by_agent = {}
            for operation in progress_operations:
                agent_name = operation.metadata.get("agent_name", "unknown")
                if agent_name not in progress_by_agent:
                    progress_by_agent[agent_name] = {
                        "total_operations": 0,
                        "active_operations": 0,
                        "completed_operations": 0,
                        "failed_operations": 0,
                    }

                progress_by_agent[agent_name]["total_operations"] += 1
                if operation.is_active():
                    progress_by_agent[agent_name]["active_operations"] += 1
                elif operation.status.value == "completed":
                    progress_by_agent[agent_name]["completed_operations"] += 1
                elif operation.status.value == "failed":
                    progress_by_agent[agent_name]["failed_operations"] += 1
        except ImportError:
            progress_by_agent = {}

        for agent in agents:
            agent_summary = {
                "name": agent.name,
                "status": agent.status.value,
                "is_healthy": agent.is_healthy(),
                "total_requests": agent.metrics.total_requests,
                "success_rate": agent.metrics.success_rate,
                "average_response_time": agent.metrics.average_response_time,
                "last_request": (
                    agent.metrics.last_request_time.isoformat()
                    if agent.metrics.last_request_time
                    else None
                ),
                "circuit_breaker_count": agent.metrics.circuit_breaker_count,
            }

            # Add rate limiting metrics if available
            if agent.name in rate_limit_metrics:
                rl_metrics = rate_limit_metrics[agent.name]
                agent_summary["rate_limiting"] = {
                    "circuit_state": rl_metrics["circuit_state"],
                    "current_min_time_ms": rl_metrics["current_min_time_ms"],
                    "concurrent_requests": rl_metrics["concurrent_requests"],
                    "throttle_rate": rl_metrics["metrics"]["throttle_rate"],
                    "rate_limit_success_rate": rl_metrics["metrics"]["success_rate"],
                }

            # Add progress tracking metrics if available
            if agent.name in progress_by_agent:
                progress_metrics = progress_by_agent[agent.name]
                agent_summary["progress_tracking"] = {
                    "total_operations": progress_metrics["total_operations"],
                    "active_operations": progress_metrics["active_operations"],
                    "completed_operations": progress_metrics["completed_operations"],
                    "failed_operations": progress_metrics["failed_operations"],
                    "success_rate": (
                        (
                            progress_metrics["completed_operations"]
                            / max(1, progress_metrics["total_operations"])
                        )
                        * 100
                        if progress_metrics["total_operations"] > 0
                        else 0
                    ),
                }

            summary["agents"].append(agent_summary)

        # Sort by success rate (descending)
        summary["agents"].sort(key=lambda x: x["success_rate"], reverse=True)

        return summary

    def get_agent_historical_metrics(
        self, agent_name: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get historical metrics for a specific agent."""
        if agent_name not in self._historical_metrics:
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            metric
            for metric in self._historical_metrics[agent_name]
            if metric["timestamp"] > cutoff_time
        ]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report including rate limiting."""
        agents = agent_registry.get_all_agents()

        # Calculate overall statistics
        total_requests = sum(agent.metrics.total_requests for agent in agents)
        total_successful = sum(agent.metrics.successful_requests for agent in agents)
        overall_success_rate = (
            (total_successful / total_requests * 100) if total_requests > 0 else 0
        )

        # Find best and worst performing agents
        agents_with_requests = [a for a in agents if a.metrics.total_requests > 0]
        best_agent = (
            max(agents_with_requests, key=lambda a: a.metrics.success_rate)
            if agents_with_requests
            else None
        )
        worst_agent = (
            min(agents_with_requests, key=lambda a: a.metrics.success_rate)
            if agents_with_requests
            else None
        )

        # Get rate limiting statistics
        try:
            from .rate_limiting import rate_limiter_manager

            rate_limit_summary = rate_limiter_manager.get_summary()
        except ImportError:
            rate_limit_summary = {
                "total_limiters": 0,
                "circuit_states": {},
                "overall_stats": {},
            }

        # Get progress tracking statistics
        try:
            from ..progress import get_progress_system_status

            progress_status = get_progress_system_status()
        except ImportError:
            progress_status = {"system_status": "unavailable"}

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "overall_statistics": {
                "total_agents": len(agents),
                "active_agents": len(
                    [a for a in agents if a.status == AgentStatus.ACTIVE]
                ),
                "total_requests": total_requests,
                "overall_success_rate": overall_success_rate,
            },
            "rate_limiting_statistics": {
                "total_rate_limiters": rate_limit_summary["total_limiters"],
                "circuit_breaker_states": rate_limit_summary["circuit_states"],
                "throttling_stats": rate_limit_summary["overall_stats"],
            },
            "progress_tracking_statistics": {
                "system_status": progress_status.get("system_status", "unknown"),
                "total_operations": progress_status.get("progress_tracker", {}).get(
                    "total_operations", 0
                ),
                "active_operations": progress_status.get("progress_tracker", {}).get(
                    "active_operations", 0
                ),
                "websocket_connections": progress_status.get(
                    "websocket_manager", {}
                ).get("active_connections", 0),
            },
            "job_queue_statistics": self._get_job_queue_statistics(),
            "health_monitoring_statistics": self._get_health_monitoring_statistics(),
            "best_performing_agent": (
                {
                    "name": best_agent.name,
                    "success_rate": best_agent.metrics.success_rate,
                    "total_requests": best_agent.metrics.total_requests,
                }
                if best_agent
                else None
            ),
            "worst_performing_agent": (
                {
                    "name": worst_agent.name,
                    "success_rate": worst_agent.metrics.success_rate,
                    "total_requests": worst_agent.metrics.total_requests,
                }
                if worst_agent
                else None
            ),
            "agents_needing_attention": [
                {"name": agent.name, "issues": self._get_agent_issues(agent)}
                for agent in agents
                if self._get_agent_issues(agent)
            ],
        }

    def _get_agent_issues(self, agent) -> List[str]:
        """Get a list of issues for an agent including rate limiting issues."""
        issues = []

        if not agent.is_healthy():
            issues.append("Unhealthy")

        if agent.status == AgentStatus.CIRCUIT_OPEN:
            issues.append("Circuit breaker open")

        if agent.metrics.total_requests > 10 and agent.metrics.success_rate < 50:
            issues.append("Low success rate")

        if agent.metrics.average_response_time > 10:
            issues.append("High response time")

        # Check rate limiting issues
        try:
            from .rate_limiting import CircuitState, rate_limiter_manager

            rate_metrics = rate_limiter_manager.get_agent_metrics(agent.name)
            if rate_metrics:
                if rate_metrics["circuit_state"] == CircuitState.OPEN.value:
                    issues.append("Rate limit circuit breaker open")

                if rate_metrics["metrics"]["throttle_rate"] > 50:
                    issues.append("High throttling rate")

                if rate_metrics["current_min_time_ms"] > 5000:
                    issues.append("Very slow rate limiting")
        except ImportError:
            pass

        return issues

    def _get_job_queue_statistics(self) -> Dict[str, Any]:
        """Get job queue statistics."""
        try:
            from ..jobs import queue_manager

            queue_status = queue_manager.get_queue_status()

            return {
                "available": True,
                "is_running": queue_status["is_running"],
                "total_jobs": queue_status["total_jobs"],
                "active_workers": queue_status["active_workers"],
                "active_downloads": queue_status["active_downloads"],
                "active_health_checks": queue_status["active_health_checks"],
                "max_concurrent_downloads": queue_status["max_concurrent_downloads"],
                "max_concurrent_health_checks": queue_status[
                    "max_concurrent_health_checks"
                ],
                "jobs_by_status": queue_status["jobs_by_status"],
                "jobs_by_type": queue_status["jobs_by_type"],
                "queue_utilization": {
                    "download_utilization": (
                        queue_status["active_downloads"]
                        / max(1, queue_status["max_concurrent_downloads"])
                    )
                    * 100,
                    "health_check_utilization": (
                        queue_status["active_health_checks"]
                        / max(1, queue_status["max_concurrent_health_checks"])
                    )
                    * 100,
                },
                "performance_stats": queue_status["statistics"],
            }
        except ImportError:
            return {"available": False, "error": "Job queue system not available"}
        except Exception as e:
            return {"available": False, "error": str(e)}

    def _get_health_monitoring_statistics(self) -> Dict[str, Any]:
        """Get health monitoring statistics."""
        try:
            from ..jobs import health_monitor

            health_summary = health_monitor.get_health_summary()

            # Get provider rankings
            rankings = health_monitor.get_provider_ranking()

            # Calculate health distribution
            total_providers = health_summary["total_providers"]
            health_distribution = {
                "healthy_percentage": (
                    health_summary["healthy"] / max(1, total_providers)
                )
                * 100,
                "degraded_percentage": (
                    health_summary["degraded"] / max(1, total_providers)
                )
                * 100,
                "unhealthy_percentage": (
                    health_summary["unhealthy"] / max(1, total_providers)
                )
                * 100,
                "disabled_percentage": (
                    health_summary["disabled"] / max(1, total_providers)
                )
                * 100,
            }

            return {
                "available": True,
                "monitoring_active": health_summary["monitoring_active"],
                "total_providers": total_providers,
                "provider_counts": {
                    "healthy": health_summary["healthy"],
                    "degraded": health_summary["degraded"],
                    "unhealthy": health_summary["unhealthy"],
                    "disabled": health_summary["disabled"],
                },
                "health_distribution": health_distribution,
                "overall_health_percentage": health_summary[
                    "overall_health_percentage"
                ],
                "top_providers": rankings[:5] if rankings else [],  # Top 5 providers
                "bottom_providers": (
                    rankings[-3:] if len(rankings) > 3 else []
                ),  # Bottom 3 providers
                "active_monitoring_tasks": health_summary["active_monitoring_tasks"],
            }
        except ImportError:
            return {
                "available": False,
                "error": "Health monitoring system not available",
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# Global monitor instance
agent_monitor = AgentMonitor()
