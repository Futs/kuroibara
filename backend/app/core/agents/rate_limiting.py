"""
Per-Agent Rate Limiting System for Kuroibara.

This module provides sophisticated rate limiting with circuit breakers,
adaptive limits, and provider-specific configurations.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit breaker active
    HALF_OPEN = "half_open"  # Testing if provider recovered


class RateLimitError(Exception):
    """Rate limit exceeded error."""

    pass


class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open error."""

    pass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_concurrent: int = 2  # Max concurrent requests
    min_time_ms: int = 1000  # Min time between requests (ms)
    max_requests_per_minute: int = 60  # Max requests per minute
    circuit_breaker_threshold: int = 5  # Failures before circuit opens
    circuit_breaker_timeout: int = 300  # Seconds before retry
    adaptive_adjustment: bool = True  # Enable adaptive rate limiting
    burst_limit: int = 5  # Max burst requests
    burst_window_ms: int = 1000  # Burst window in milliseconds

    # Adaptive adjustment parameters
    success_rate_threshold: float = 0.95  # Success rate to increase speed
    failure_rate_threshold: float = 0.8  # Success rate to decrease speed
    adjustment_step_ms: int = 100  # Adjustment step size
    min_adjustment_requests: int = 10  # Min requests before adjusting


@dataclass
class RateLimitMetrics:
    """Metrics for rate limiting."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    throttled_requests: int = 0
    circuit_breaker_opens: int = 0
    average_wait_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_adjustment_time: Optional[datetime] = None
    current_min_time_ms: int = 1000

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def throttle_rate(self) -> float:
        """Calculate throttle rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.throttled_requests / self.total_requests) * 100


class AgentRateLimiter:
    """
    Rate limiter for individual agents with circuit breaker and adaptive behavior.
    """

    def __init__(self, agent_name: str, config: RateLimitConfig):
        self.agent_name = agent_name
        self.config = config
        self.metrics = RateLimitMetrics()

        # Concurrency control
        self.semaphore = asyncio.Semaphore(config.max_concurrent)

        # Timing control
        self.last_request_time = 0.0
        self.request_times: List[float] = []
        self.burst_times: List[float] = []

        # Circuit breaker
        self.circuit_state = CircuitState.CLOSED
        self.circuit_opened_at = 0.0
        self.consecutive_failures = 0
        self.consecutive_successes = 0

        # Adaptive rate limiting
        self.current_min_time_ms = config.min_time_ms
        self.metrics.current_min_time_ms = config.min_time_ms

        logger.debug(f"Initialized rate limiter for {agent_name} with config: {config}")

    async def acquire(self) -> None:
        """
        Acquire permission to make a request.

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RateLimitError: If rate limit is exceeded
        """
        # Check circuit breaker
        if not self._check_circuit_breaker():
            raise CircuitBreakerOpenError(f"Circuit breaker open for {self.agent_name}")

        # Acquire semaphore for concurrency control
        await self.semaphore.acquire()

        try:
            # Check rate limits
            await self._enforce_rate_limits()

            # Record request
            self.metrics.total_requests += 1
            self.metrics.last_request_time = datetime.utcnow()

        except Exception:
            self.semaphore.release()
            raise

    def release(
        self, success: bool = True, response_time: Optional[float] = None
    ) -> None:
        """
        Release the rate limiter and update metrics.

        Args:
            success: Whether the request was successful
            response_time: Response time in seconds
        """
        try:
            if success:
                self.metrics.successful_requests += 1
                self.consecutive_successes += 1
                self.consecutive_failures = 0

                # Close circuit breaker if in half-open state
                if self.circuit_state == CircuitState.HALF_OPEN:
                    if self.consecutive_successes >= 3:  # Require 3 successes to close
                        self.circuit_state = CircuitState.CLOSED
                        logger.info(f"Circuit breaker closed for {self.agent_name}")
            else:
                self.metrics.failed_requests += 1
                self.consecutive_failures += 1
                self.consecutive_successes = 0

                # Check if we should open circuit breaker
                if self.consecutive_failures >= self.config.circuit_breaker_threshold:
                    self._open_circuit()

            # Adaptive rate limiting
            if self.config.adaptive_adjustment:
                self._adjust_rate_limit(success, response_time)

        finally:
            self.semaphore.release()

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows requests."""
        current_time = time.time()

        if self.circuit_state == CircuitState.OPEN:
            if (
                current_time - self.circuit_opened_at
                > self.config.circuit_breaker_timeout
            ):
                self.circuit_state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker half-open for {self.agent_name}")
                return True
            return False

        return True

    async def _enforce_rate_limits(self) -> None:
        """Enforce all rate limiting rules."""
        current_time = time.time()
        current_time_ms = current_time * 1000

        # Enforce minimum time between requests
        time_since_last = current_time_ms - self.last_request_time
        if time_since_last < self.current_min_time_ms:
            wait_time = (self.current_min_time_ms - time_since_last) / 1000
            self.metrics.throttled_requests += 1
            self.metrics.average_wait_time = (
                self.metrics.average_wait_time * (self.metrics.throttled_requests - 1)
                + wait_time
            ) / self.metrics.throttled_requests
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time() * 1000

        # Check burst limit
        self._check_burst_limit()

        # Check requests per minute limit
        self._check_minute_limit()

    def _check_burst_limit(self) -> None:
        """Check burst rate limit."""
        current_time = time.time()
        burst_window_start = current_time - (self.config.burst_window_ms / 1000)

        # Clean old burst requests
        self.burst_times = [t for t in self.burst_times if t > burst_window_start]

        if len(self.burst_times) >= self.config.burst_limit:
            raise RateLimitError(f"Burst limit exceeded for {self.agent_name}")

        self.burst_times.append(current_time)

    def _check_minute_limit(self) -> None:
        """Check requests per minute limit."""
        current_time = time.time()
        minute_start = current_time - 60

        # Clean old requests
        self.request_times = [t for t in self.request_times if t > minute_start]

        if len(self.request_times) >= self.config.max_requests_per_minute:
            raise RateLimitError(f"Minute limit exceeded for {self.agent_name}")

        self.request_times.append(current_time)

    def _open_circuit(self) -> None:
        """Open the circuit breaker."""
        self.circuit_state = CircuitState.OPEN
        self.circuit_opened_at = time.time()
        self.metrics.circuit_breaker_opens += 1
        logger.warning(
            f"Circuit breaker opened for {self.agent_name} after "
            f"{self.consecutive_failures} consecutive failures"
        )

    def _adjust_rate_limit(self, success: bool, response_time: Optional[float]) -> None:
        """Adaptively adjust rate limits based on performance."""
        # Only adjust if we have enough data
        if self.metrics.total_requests < self.config.min_adjustment_requests:
            return

        # Don't adjust too frequently
        now = datetime.utcnow()
        if (
            self.metrics.last_adjustment_time
            and (now - self.metrics.last_adjustment_time).total_seconds() < 30
        ):
            return

        success_rate = self.metrics.success_rate / 100

        # Increase speed if high success rate
        if success_rate >= self.config.success_rate_threshold:
            if self.current_min_time_ms > 200:  # Don't go below 200ms
                old_time = self.current_min_time_ms
                self.current_min_time_ms = max(
                    200, self.current_min_time_ms - self.config.adjustment_step_ms
                )
                self.metrics.current_min_time_ms = self.current_min_time_ms
                logger.debug(
                    f"Increased speed for {self.agent_name}: {old_time}ms -> {self.current_min_time_ms}ms "
                    f"(success rate: {success_rate:.2%})"
                )

        # Decrease speed if low success rate
        elif success_rate < self.config.failure_rate_threshold:
            if self.current_min_time_ms < 10000:  # Don't go above 10s
                old_time = self.current_min_time_ms
                self.current_min_time_ms = min(
                    10000, self.current_min_time_ms + self.config.adjustment_step_ms * 2
                )
                self.metrics.current_min_time_ms = self.current_min_time_ms
                logger.debug(
                    f"Decreased speed for {self.agent_name}: {old_time}ms -> {self.current_min_time_ms}ms "
                    f"(success rate: {success_rate:.2%})"
                )

        self.metrics.last_adjustment_time = now

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status."""
        return {
            "agent_name": self.agent_name,
            "circuit_state": self.circuit_state.value,
            "current_min_time_ms": self.current_min_time_ms,
            "concurrent_requests": self.config.max_concurrent - self.semaphore._value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": self.metrics.success_rate,
                "throttle_rate": self.metrics.throttle_rate,
                "circuit_breaker_opens": self.metrics.circuit_breaker_opens,
                "average_wait_time": self.metrics.average_wait_time,
                "last_request": (
                    self.metrics.last_request_time.isoformat()
                    if self.metrics.last_request_time
                    else None
                ),
            },
            "config": {
                "max_concurrent": self.config.max_concurrent,
                "min_time_ms": self.config.min_time_ms,
                "max_requests_per_minute": self.config.max_requests_per_minute,
                "adaptive_adjustment": self.config.adaptive_adjustment,
            },
        }

    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.circuit_state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        logger.info(f"Circuit breaker reset for {self.agent_name}")

    def update_config(self, new_config: RateLimitConfig) -> None:
        """Update rate limiting configuration."""
        old_concurrent = self.config.max_concurrent
        self.config = new_config

        # Update semaphore if max_concurrent changed
        if new_config.max_concurrent != old_concurrent:
            self.semaphore = asyncio.Semaphore(new_config.max_concurrent)

        # Reset adaptive timing if disabled
        if not new_config.adaptive_adjustment:
            self.current_min_time_ms = new_config.min_time_ms
            self.metrics.current_min_time_ms = new_config.min_time_ms

        logger.info(f"Updated rate limit config for {self.agent_name}: {new_config}")


class RateLimiterManager:
    """
    Manager for all agent rate limiters with provider-specific configurations.
    """

    def __init__(self):
        self.limiters: Dict[str, AgentRateLimiter] = {}
        self.provider_configs = self._load_provider_configs()
        self.default_config = RateLimitConfig()

        logger.info("Initialized RateLimiterManager")

    def _load_provider_configs(self) -> Dict[str, RateLimitConfig]:
        """Load provider-specific rate limit configurations."""
        return {
            # High-performance providers
            "MangaDex": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=5000,  # 5 seconds between API requests (user reports)
                max_requests_per_minute=12,  # Reduced due to longer delays
                burst_limit=2,  # Reduced burst limit
                adaptive_adjustment=True,
            ),
            "MangaPill": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1000,
                max_requests_per_minute=45,
                burst_limit=3,
                adaptive_adjustment=True,
            ),
            # Medium-performance providers
            "Toonily": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1200,
                max_requests_per_minute=40,
                burst_limit=3,
                adaptive_adjustment=True,
            ),
            "MangaTown": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1500,
                max_requests_per_minute=35,
                burst_limit=2,
                adaptive_adjustment=True,
            ),
            # Conservative providers (require careful handling)
            "ManhuaFast": RateLimitConfig(
                max_concurrent=1,
                min_time_ms=2000,
                max_requests_per_minute=25,
                burst_limit=2,
                circuit_breaker_threshold=3,
                adaptive_adjustment=True,
            ),
            "ArcaneScans": RateLimitConfig(
                max_concurrent=1,
                min_time_ms=1800,
                max_requests_per_minute=30,
                burst_limit=2,
                adaptive_adjustment=True,
            ),
            # NSFW providers (often more restrictive)
            "Manga18fx": RateLimitConfig(
                max_concurrent=1,
                min_time_ms=2500,
                max_requests_per_minute=20,
                burst_limit=1,
                circuit_breaker_threshold=3,
                adaptive_adjustment=True,
            ),
            # Generic providers
            "MangaFreak": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1500,
                max_requests_per_minute=30,
                burst_limit=2,
                adaptive_adjustment=True,
            ),
            "MangaSail": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1200,
                max_requests_per_minute=35,
                burst_limit=3,
                adaptive_adjustment=True,
            ),
            "MangaKakalotFun": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1000,
                max_requests_per_minute=40,
                burst_limit=3,
                adaptive_adjustment=True,
            ),
            "MangaDNA": RateLimitConfig(
                max_concurrent=2,
                min_time_ms=1300,
                max_requests_per_minute=35,
                burst_limit=2,
                adaptive_adjustment=True,
            ),
        }

    def get_limiter(self, agent_name: str) -> AgentRateLimiter:
        """Get or create rate limiter for an agent."""
        if agent_name not in self.limiters:
            config = self.provider_configs.get(agent_name, self.default_config)
            self.limiters[agent_name] = AgentRateLimiter(agent_name, config)
            logger.debug(f"Created rate limiter for {agent_name}")

        return self.limiters[agent_name]

    async def execute_with_rate_limit(
        self, agent_name: str, func: Callable, *args, **kwargs
    ) -> Any:
        """
        Execute a function with rate limiting.

        Args:
            agent_name: Name of the agent
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RateLimitError: If rate limit is exceeded
        """
        limiter = self.get_limiter(agent_name)

        start_time = time.time()
        await limiter.acquire()

        try:
            result = await func(*args, **kwargs)
            response_time = time.time() - start_time
            limiter.release(success=True, response_time=response_time)
            return result

        except Exception as e:
            response_time = time.time() - start_time
            limiter.release(success=False, response_time=response_time)
            raise e

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limiting metrics for all agents."""
        metrics = {}
        for agent_name, limiter in self.limiters.items():
            metrics[agent_name] = limiter.get_status()
        return metrics

    def get_agent_metrics(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get rate limiting metrics for a specific agent."""
        limiter = self.limiters.get(agent_name)
        return limiter.get_status() if limiter else None

    def update_agent_config(self, agent_name: str, config: RateLimitConfig) -> bool:
        """Update rate limiting configuration for an agent."""
        try:
            if agent_name in self.limiters:
                self.limiters[agent_name].update_config(config)
            else:
                # Create new limiter with config
                self.limiters[agent_name] = AgentRateLimiter(agent_name, config)

            # Update provider configs
            self.provider_configs[agent_name] = config

            logger.info(f"Updated rate limit config for {agent_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating rate limit config for {agent_name}: {e}")
            return False

    def reset_circuit_breaker(self, agent_name: str) -> bool:
        """Reset circuit breaker for an agent."""
        try:
            limiter = self.limiters.get(agent_name)
            if limiter:
                limiter.reset_circuit_breaker()
                return True
            return False

        except Exception as e:
            logger.error(f"Error resetting circuit breaker for {agent_name}: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all rate limiters."""
        total_limiters = len(self.limiters)
        active_circuits = sum(
            1
            for limiter in self.limiters.values()
            if limiter.circuit_state == CircuitState.CLOSED
        )
        open_circuits = sum(
            1
            for limiter in self.limiters.values()
            if limiter.circuit_state == CircuitState.OPEN
        )
        half_open_circuits = sum(
            1
            for limiter in self.limiters.values()
            if limiter.circuit_state == CircuitState.HALF_OPEN
        )

        total_requests = sum(
            limiter.metrics.total_requests for limiter in self.limiters.values()
        )
        total_throttled = sum(
            limiter.metrics.throttled_requests for limiter in self.limiters.values()
        )

        return {
            "total_limiters": total_limiters,
            "circuit_states": {
                "closed": active_circuits,
                "open": open_circuits,
                "half_open": half_open_circuits,
            },
            "overall_stats": {
                "total_requests": total_requests,
                "total_throttled": total_throttled,
                "throttle_rate": (total_throttled / max(1, total_requests)) * 100,
            },
        }


# Global rate limiter manager instance
rate_limiter_manager = RateLimiterManager()
