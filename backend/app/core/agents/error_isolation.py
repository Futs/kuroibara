"""
Error isolation system for agents.

This module provides advanced error isolation mechanisms including
circuit breakers, bulkheads, and failure detection to prevent
cascading failures between agents.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class IsolationLevel(Enum):
    """Levels of error isolation."""

    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    QUARANTINE = "quarantine"


class ErrorPattern(Enum):
    """Types of error patterns to detect."""

    HIGH_FAILURE_RATE = "high_failure_rate"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    TIMEOUT_PATTERN = "timeout_pattern"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CASCADING_FAILURE = "cascading_failure"


class AgentIsolationManager:
    """
    Manages error isolation for agents to prevent cascading failures.

    Features:
    - Circuit breaker patterns
    - Bulkhead isolation
    - Failure pattern detection
    - Automatic quarantine
    - Recovery monitoring
    """

    def __init__(self):
        self._isolation_configs: Dict[str, Dict[str, Any]] = {}
        self._failure_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self._quarantined_agents: Dict[str, datetime] = {}
        self._bulkhead_semaphores: Dict[str, asyncio.Semaphore] = {}

        # Default isolation configuration
        self._default_config = {
            "circuit_breaker_threshold": 5,
            "circuit_breaker_timeout": 300,
            "failure_rate_threshold": 0.8,
            "consecutive_failure_threshold": 3,
            "timeout_threshold": 30,
            "quarantine_duration": 600,  # 10 minutes
            "max_concurrent_requests": 3,
            "isolation_level": IsolationLevel.BASIC,
        }

    def configure_agent_isolation(
        self, agent_name: str, config: Dict[str, Any]
    ) -> None:
        """
        Configure isolation settings for a specific agent.

        Args:
            agent_name: Name of the agent
            config: Isolation configuration
        """
        self._isolation_configs[agent_name] = {**self._default_config, **config}

        # Create bulkhead semaphore
        max_concurrent = config.get("max_concurrent_requests", 3)
        self._bulkhead_semaphores[agent_name] = asyncio.Semaphore(max_concurrent)

        logger.info(f"Configured isolation for agent {agent_name}: {config}")

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get isolation configuration for an agent."""
        return self._isolation_configs.get(agent_name, self._default_config)

    async def execute_with_isolation(
        self, agent_name: str, operation: Callable, *args, **kwargs
    ) -> Any:
        """
        Execute an operation with error isolation.

        Args:
            agent_name: Name of the agent
            operation: The operation to execute
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result

        Raises:
            Exception: If operation fails or agent is isolated
        """
        config = self.get_agent_config(agent_name)

        # Check if agent is quarantined
        if self._is_agent_quarantined(agent_name):
            raise Exception(
                f"Agent {agent_name} is quarantined due to repeated failures"
            )

        # Apply bulkhead pattern (limit concurrent requests)
        semaphore = self._bulkhead_semaphores.get(agent_name)
        if not semaphore:
            semaphore = asyncio.Semaphore(config["max_concurrent_requests"])
            self._bulkhead_semaphores[agent_name] = semaphore

        async with semaphore:
            try:
                # Execute operation with timeout
                timeout = config.get("timeout_threshold", 30)
                result = await asyncio.wait_for(
                    operation(*args, **kwargs), timeout=timeout
                )

                # Record successful execution
                self._record_success(agent_name)

                return result

            except asyncio.TimeoutError:
                self._record_failure(
                    agent_name, ErrorPattern.TIMEOUT_PATTERN, "Operation timeout"
                )
                raise Exception(f"Operation timeout for agent {agent_name}")

            except Exception as e:
                self._record_failure(agent_name, ErrorPattern.HIGH_FAILURE_RATE, str(e))
                raise

    def _record_success(self, agent_name: str) -> None:
        """Record a successful operation."""
        if agent_name in self._failure_patterns:
            # Reset failure patterns on success
            self._failure_patterns[agent_name] = []

        # Remove from quarantine if successful
        if agent_name in self._quarantined_agents:
            del self._quarantined_agents[agent_name]
            logger.info(f"Agent {agent_name} recovered from quarantine")

    def _record_failure(
        self, agent_name: str, pattern: ErrorPattern, error_message: str
    ) -> None:
        """Record a failure and check for patterns."""
        if agent_name not in self._failure_patterns:
            self._failure_patterns[agent_name] = []

        failure_record = {
            "timestamp": datetime.utcnow(),
            "pattern": pattern,
            "error": error_message,
        }

        self._failure_patterns[agent_name].append(failure_record)

        # Clean old failure records (keep last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self._failure_patterns[agent_name] = [
            record
            for record in self._failure_patterns[agent_name]
            if record["timestamp"] > cutoff_time
        ]

        # Check if agent should be quarantined
        self._check_quarantine_conditions(agent_name)

    def _check_quarantine_conditions(self, agent_name: str) -> None:
        """Check if an agent should be quarantined based on failure patterns."""
        config = self.get_agent_config(agent_name)
        failures = self._failure_patterns.get(agent_name, [])

        if not failures:
            return

        # Check consecutive failures
        consecutive_failures = 0
        for failure in reversed(failures):
            if failure["pattern"] in [
                ErrorPattern.HIGH_FAILURE_RATE,
                ErrorPattern.TIMEOUT_PATTERN,
            ]:
                consecutive_failures += 1
            else:
                break

        if consecutive_failures >= config["consecutive_failure_threshold"]:
            self._quarantine_agent(agent_name, "Too many consecutive failures")
            return

        # Check failure rate in last 10 minutes
        recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
        recent_failures = [f for f in failures if f["timestamp"] > recent_cutoff]

        if len(recent_failures) >= config["circuit_breaker_threshold"]:
            self._quarantine_agent(agent_name, "High failure rate detected")

    def _quarantine_agent(self, agent_name: str, reason: str) -> None:
        """Quarantine an agent due to repeated failures."""
        self._quarantined_agents[agent_name] = datetime.utcnow()
        logger.warning(f"Quarantined agent {agent_name}: {reason}")

    def _is_agent_quarantined(self, agent_name: str) -> bool:
        """Check if an agent is currently quarantined."""
        if agent_name not in self._quarantined_agents:
            return False

        quarantine_time = self._quarantined_agents[agent_name]
        config = self.get_agent_config(agent_name)
        quarantine_duration = config["quarantine_duration"]

        # Check if quarantine period has expired
        if datetime.utcnow() - quarantine_time > timedelta(seconds=quarantine_duration):
            del self._quarantined_agents[agent_name]
            logger.info(f"Agent {agent_name} quarantine period expired")
            return False

        return True

    def get_isolation_status(self) -> Dict[str, Any]:
        """Get current isolation status for all agents."""
        status = {
            "quarantined_agents": {},
            "failure_patterns": {},
            "bulkhead_usage": {},
        }

        # Quarantined agents
        for agent_name, quarantine_time in self._quarantined_agents.items():
            config = self.get_agent_config(agent_name)
            remaining_time = (
                config["quarantine_duration"]
                - (datetime.utcnow() - quarantine_time).total_seconds()
            )
            status["quarantined_agents"][agent_name] = {
                "quarantined_at": quarantine_time.isoformat(),
                "remaining_seconds": max(0, remaining_time),
            }

        # Failure patterns
        for agent_name, failures in self._failure_patterns.items():
            if failures:
                status["failure_patterns"][agent_name] = {
                    "total_failures": len(failures),
                    "recent_failures": len(
                        [
                            f
                            for f in failures
                            if f["timestamp"]
                            > datetime.utcnow() - timedelta(minutes=10)
                        ]
                    ),
                    "last_failure": (
                        failures[-1]["timestamp"].isoformat() if failures else None
                    ),
                }

        # Bulkhead usage
        for agent_name, semaphore in self._bulkhead_semaphores.items():
            config = self.get_agent_config(agent_name)
            max_concurrent = config["max_concurrent_requests"]
            available = semaphore._value
            in_use = max_concurrent - available
            status["bulkhead_usage"][agent_name] = {
                "max_concurrent": max_concurrent,
                "in_use": in_use,
                "available": available,
                "utilization": (in_use / max_concurrent) * 100,
            }

        return status

    def reset_agent_isolation(self, agent_name: str) -> bool:
        """
        Reset isolation state for an agent.

        Args:
            agent_name: Name of the agent to reset

        Returns:
            True if reset was successful
        """
        try:
            # Remove from quarantine
            if agent_name in self._quarantined_agents:
                del self._quarantined_agents[agent_name]

            # Clear failure patterns
            if agent_name in self._failure_patterns:
                self._failure_patterns[agent_name] = []

            logger.info(f"Reset isolation state for agent {agent_name}")
            return True

        except Exception as e:
            logger.error(f"Error resetting isolation for agent {agent_name}: {e}")
            return False


# Global isolation manager instance
isolation_manager = AgentIsolationManager()
