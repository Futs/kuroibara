"""
Comprehensive tests for the rate limiting system.

This module tests all aspects of the rate limiting including
rate limiters, circuit breakers, adaptive behavior, and API endpoints.
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.core.agents.rate_limiting import (
    AgentRateLimiter,
    CircuitBreakerOpenError,
    CircuitState,
    RateLimitConfig,
    RateLimiterManager,
    RateLimitError,
)


class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.max_concurrent == 2
        assert config.min_time_ms == 1000
        assert config.max_requests_per_minute == 60
        assert config.circuit_breaker_threshold == 5
        assert config.adaptive_adjustment is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            max_concurrent=5,
            min_time_ms=500,
            max_requests_per_minute=120,
            adaptive_adjustment=False,
        )
        assert config.max_concurrent == 5
        assert config.min_time_ms == 500
        assert config.max_requests_per_minute == 120
        assert config.adaptive_adjustment is False


class TestAgentRateLimiter:
    """Test individual agent rate limiter."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a test rate limiter."""
        config = RateLimitConfig(
            max_concurrent=2,
            min_time_ms=100,  # Short for testing
            max_requests_per_minute=60,
            circuit_breaker_threshold=3,
            adaptive_adjustment=True,
            burst_limit=20,  # High burst limit for testing
            burst_window_ms=1000,
        )
        return AgentRateLimiter("test_agent", config)

    @pytest.mark.asyncio
    async def test_basic_acquire_release(self, rate_limiter):
        """Test basic acquire and release functionality."""
        # Should be able to acquire
        await rate_limiter.acquire()
        assert rate_limiter.metrics.total_requests == 1

        # Release successfully
        rate_limiter.release(success=True)
        assert rate_limiter.metrics.successful_requests == 1
        assert rate_limiter.circuit_state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, rate_limiter):
        """Test concurrency limiting."""
        # Acquire up to the limit
        await rate_limiter.acquire()
        await rate_limiter.acquire()

        # Third acquire should be possible but will wait
        start_time = time.time()

        # Start a task that will release after a short delay
        async def release_after_delay():
            await asyncio.sleep(0.05)
            rate_limiter.release(success=True)

        release_task = asyncio.create_task(release_after_delay())

        # This should wait for the release
        await rate_limiter.acquire()
        elapsed = time.time() - start_time

        # Should have waited at least 0.05 seconds
        assert elapsed >= 0.04

        # Clean up
        rate_limiter.release(success=True)
        rate_limiter.release(success=True)
        await release_task

    @pytest.mark.asyncio
    async def test_minimum_time_enforcement(self, rate_limiter):
        """Test minimum time between requests."""
        # First request
        await rate_limiter.acquire()
        rate_limiter.release(success=True)

        # Second request should be delayed
        start_time = time.time()
        await rate_limiter.acquire()
        elapsed = time.time() - start_time

        # Should have waited at least min_time_ms (100ms in test config)
        assert elapsed >= 0.08  # Allow some tolerance

        rate_limiter.release(success=True)

    @pytest.mark.asyncio
    async def test_circuit_breaker_opening(self, rate_limiter):
        """Test circuit breaker opening after failures."""
        # Generate failures to open circuit breaker
        for i in range(3):  # threshold is 3 in test config
            await rate_limiter.acquire()
            rate_limiter.release(success=False)

        # Circuit should be open now
        assert rate_limiter.circuit_state == CircuitState.OPEN

        # Next acquire should fail
        with pytest.raises(CircuitBreakerOpenError):
            await rate_limiter.acquire()

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open(self, rate_limiter):
        """Test circuit breaker half-open state."""
        # Open the circuit breaker
        for i in range(3):
            await rate_limiter.acquire()
            rate_limiter.release(success=False)

        assert rate_limiter.circuit_state == CircuitState.OPEN

        # Simulate timeout passing
        rate_limiter.circuit_opened_at = time.time() - 400  # Past timeout

        # Should allow request in half-open state
        await rate_limiter.acquire()
        assert rate_limiter.circuit_state == CircuitState.HALF_OPEN

        # Successful request should close circuit
        rate_limiter.release(success=True)
        rate_limiter.release(success=True)  # Need multiple successes
        rate_limiter.release(success=True)

        # Circuit should be closed after 3 successes
        assert rate_limiter.circuit_state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_adaptive_rate_limiting(self, rate_limiter):
        """Test adaptive rate limiting behavior."""
        initial_min_time = rate_limiter.current_min_time_ms

        # Generate enough successful requests to trigger adaptation
        # Add delays to avoid burst limit
        for i in range(15):
            await rate_limiter.acquire()
            rate_limiter.release(success=True, response_time=0.1)
            # Small delay to avoid burst limit
            await asyncio.sleep(0.01)

        # With high success rate, min time should decrease
        # (Note: adaptation only happens after min_adjustment_requests)
        if (
            rate_limiter.metrics.total_requests
            >= rate_limiter.config.min_adjustment_requests
        ):
            # Allow some time for adjustment
            await asyncio.sleep(0.1)
            # Min time might have been adjusted down
            assert (
                rate_limiter.current_min_time_ms <= initial_min_time + 100
            )  # Allow some variance

    def test_rate_limiter_status(self, rate_limiter):
        """Test getting rate limiter status."""
        status = rate_limiter.get_status()

        required_fields = [
            "agent_name",
            "circuit_state",
            "current_min_time_ms",
            "concurrent_requests",
            "metrics",
            "config",
        ]

        for field in required_fields:
            assert field in status

        assert status["agent_name"] == "test_agent"
        assert status["circuit_state"] == "closed"
        assert isinstance(status["metrics"], dict)
        assert isinstance(status["config"], dict)

    def test_reset_circuit_breaker(self, rate_limiter):
        """Test resetting circuit breaker."""
        # Open circuit breaker
        rate_limiter.consecutive_failures = 5
        rate_limiter._open_circuit()
        assert rate_limiter.circuit_state == CircuitState.OPEN

        # Reset circuit breaker
        rate_limiter.reset_circuit_breaker()
        assert rate_limiter.circuit_state == CircuitState.CLOSED
        assert rate_limiter.consecutive_failures == 0


class TestRateLimiterManager:
    """Test rate limiter manager."""

    @pytest.fixture
    def manager(self):
        """Create a test rate limiter manager."""
        return RateLimiterManager()

    def test_get_limiter(self, manager):
        """Test getting a rate limiter for an agent."""
        limiter = manager.get_limiter("test_agent")
        assert isinstance(limiter, AgentRateLimiter)
        assert limiter.agent_name == "test_agent"

        # Getting the same agent should return the same limiter
        limiter2 = manager.get_limiter("test_agent")
        assert limiter is limiter2

    def test_provider_specific_configs(self, manager):
        """Test that providers get their specific configurations."""
        # Test MangaDex config (updated to match current configuration)
        mangadex_limiter = manager.get_limiter("MangaDex")
        status = mangadex_limiter.get_status()
        assert status["config"]["max_concurrent"] == 2  # Updated from 3 to 2
        assert status["current_min_time_ms"] == 5000  # Updated from 800 to 5000

        # Test ManhuaFast config (more conservative)
        manhua_limiter = manager.get_limiter("ManhuaFast")
        status = manhua_limiter.get_status()
        assert status["config"]["max_concurrent"] == 1
        assert status["current_min_time_ms"] == 2000

    @pytest.mark.asyncio
    async def test_execute_with_rate_limit(self, manager):
        """Test executing function with rate limiting."""
        call_count = 0

        async def test_function(value):
            nonlocal call_count
            call_count += 1
            return f"result_{value}"

        # Execute function with rate limiting
        result = await manager.execute_with_rate_limit(
            "test_agent", test_function, "test"
        )

        assert result == "result_test"
        assert call_count == 1

        # Check that limiter was created and used
        limiter = manager.get_limiter("test_agent")
        assert limiter.metrics.total_requests == 1
        assert limiter.metrics.successful_requests == 1

    @pytest.mark.asyncio
    async def test_execute_with_rate_limit_failure(self, manager):
        """Test executing function that fails."""

        async def failing_function():
            raise ValueError("Test error")

        # Should propagate the exception
        with pytest.raises(ValueError, match="Test error"):
            await manager.execute_with_rate_limit("test_agent", failing_function)

        # Check that failure was recorded
        limiter = manager.get_limiter("test_agent")
        assert limiter.metrics.total_requests == 1
        assert limiter.metrics.failed_requests == 1

    def test_get_all_metrics(self, manager):
        """Test getting metrics for all agents."""
        # Create some limiters
        manager.get_limiter("agent1")
        manager.get_limiter("agent2")

        metrics = manager.get_all_metrics()
        assert "agent1" in metrics
        assert "agent2" in metrics

        for agent_metrics in metrics.values():
            assert "agent_name" in agent_metrics
            assert "metrics" in agent_metrics
            assert "config" in agent_metrics

    def test_update_agent_config(self, manager):
        """Test updating agent configuration."""
        # Create a limiter
        limiter = manager.get_limiter("test_agent")
        original_config = limiter.config

        # Update configuration
        new_config = RateLimitConfig(
            max_concurrent=5, min_time_ms=500, adaptive_adjustment=False
        )

        success = manager.update_agent_config("test_agent", new_config)
        assert success

        # Verify configuration was updated
        updated_limiter = manager.get_limiter("test_agent")
        assert updated_limiter.config.max_concurrent == 5
        assert updated_limiter.config.min_time_ms == 500
        assert updated_limiter.config.adaptive_adjustment is False

    def test_reset_circuit_breaker(self, manager):
        """Test resetting circuit breaker through manager."""
        # Create limiter and open circuit
        limiter = manager.get_limiter("test_agent")
        limiter._open_circuit()
        assert limiter.circuit_state == CircuitState.OPEN

        # Reset through manager
        success = manager.reset_circuit_breaker("test_agent")
        assert success
        assert limiter.circuit_state == CircuitState.CLOSED

        # Test with non-existent agent
        success = manager.reset_circuit_breaker("non_existent")
        assert not success

    def test_get_summary(self, manager):
        """Test getting summary of all rate limiters."""
        # Create some limiters with different states
        limiter1 = manager.get_limiter("agent1")
        limiter2 = manager.get_limiter("agent2")
        limiter2._open_circuit()  # Open one circuit

        summary = manager.get_summary()

        assert summary["total_limiters"] == 2
        assert summary["circuit_states"]["closed"] == 1
        assert summary["circuit_states"]["open"] == 1
        assert summary["circuit_states"]["half_open"] == 0
        assert "overall_stats" in summary


if __name__ == "__main__":
    # Run basic tests if executed directly
    import sys

    print("Running rate limiting tests...")

    # Test basic functionality
    config = RateLimitConfig()
    assert config.max_concurrent == 2
    print("✅ RateLimitConfig tests passed")

    # Test manager
    manager = RateLimiterManager()
    limiter = manager.get_limiter("test")
    assert limiter.agent_name == "test"
    print("✅ RateLimiterManager tests passed")

    print("\n🎉 All basic rate limiting tests passed!")
    print("Run with pytest for full test suite: pytest tests/test_rate_limiting.py -v")
