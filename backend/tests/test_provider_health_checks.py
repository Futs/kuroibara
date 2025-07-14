"""
Tests for provider health check functionality.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.core.services.provider_monitor import ProviderMonitorService
from app.models.provider import ProviderStatusEnum


class TestProviderHealthChecks:
    """Test provider health check and auto-disable/enable functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = ProviderMonitorService()

    @pytest.mark.asyncio
    async def test_auto_disable_zero_uptime(self):
        """Test auto-disable when provider has 0% uptime."""
        # Create a provider status with 0% uptime
        provider_status = MagicMock()
        provider_status.is_enabled = True
        provider_status.uptime_percentage = 0.0
        provider_status.total_checks = 5
        provider_status.consecutive_failures = 2
        provider_status.max_consecutive_failures = 3
        provider_status.successful_checks = 0
        provider_status.last_check = datetime.now(timezone.utc)

        # Check auto-disable logic
        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is not None
        action, reason = result
        assert action == "disable"
        assert "0% uptime" in reason

    @pytest.mark.asyncio
    async def test_auto_disable_consecutive_failures(self):
        """Test auto-disable when provider exceeds consecutive failure threshold."""
        provider_status = MagicMock()
        provider_status.is_enabled = True
        provider_status.uptime_percentage = 20.0
        provider_status.total_checks = 10
        provider_status.consecutive_failures = 5
        provider_status.max_consecutive_failures = 3
        provider_status.successful_checks = 2
        provider_status.last_check = datetime.now(timezone.utc)

        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is not None
        action, reason = result
        assert action == "disable"
        assert "consecutive failures" in reason

    @pytest.mark.asyncio
    async def test_auto_disable_no_success_48_hours(self):
        """Test auto-disable when no successful checks in 48+ hours."""
        provider_status = MagicMock()
        provider_status.is_enabled = True
        provider_status.uptime_percentage = 10.0
        provider_status.total_checks = 10
        provider_status.consecutive_failures = 2
        provider_status.max_consecutive_failures = 3
        provider_status.successful_checks = 0
        provider_status.last_check = datetime.now(timezone.utc) - timedelta(hours=50)

        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is not None
        action, reason = result
        assert action == "disable"
        assert "48+ hours" in reason

    @pytest.mark.asyncio
    async def test_auto_enable_healthy_provider(self):
        """Test auto-enable when disabled provider becomes healthy."""
        provider_status = MagicMock()
        provider_status.is_enabled = False
        provider_status.status = ProviderStatusEnum.ACTIVE.value
        provider_status.consecutive_failures = 0
        provider_status.uptime_percentage = 80.0

        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is not None
        action, reason = result
        assert action == "enable"
        assert "healthy again" in reason

    @pytest.mark.asyncio
    async def test_auto_enable_improved_uptime(self):
        """Test auto-enable when uptime improves significantly."""
        provider_status = MagicMock()
        provider_status.is_enabled = False
        provider_status.status = ProviderStatusEnum.DOWN.value
        provider_status.consecutive_failures = 1
        provider_status.uptime_percentage = 60.0
        provider_status.total_checks = 10

        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is not None
        action, reason = result
        assert action == "enable"
        assert "Uptime improved" in reason

    @pytest.mark.asyncio
    async def test_no_action_healthy_enabled_provider(self):
        """Test no action for healthy enabled provider."""
        provider_status = MagicMock()
        provider_status.is_enabled = True
        provider_status.status = ProviderStatusEnum.ACTIVE.value
        provider_status.uptime_percentage = 95.0
        provider_status.consecutive_failures = 0
        provider_status.max_consecutive_failures = 3
        provider_status.total_checks = 10
        provider_status.successful_checks = 9
        provider_status.last_check = datetime.now(timezone.utc)

        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is None

    @pytest.mark.asyncio
    async def test_no_action_disabled_unhealthy_provider(self):
        """Test no action for disabled unhealthy provider that doesn't meet re-enable criteria."""
        provider_status = MagicMock()
        provider_status.is_enabled = False
        provider_status.status = ProviderStatusEnum.DOWN.value
        provider_status.uptime_percentage = 30.0
        provider_status.consecutive_failures = 2
        provider_status.total_checks = 5

        result = await self.monitor._check_auto_disable_enable(provider_status)

        assert result is None

    @pytest.mark.asyncio
    async def test_daily_health_check_structure(self):
        """Test that daily health check returns proper structure."""
        with patch(
            "app.core.services.provider_monitor.AsyncSessionLocal"
        ) as mock_session:
            # Create a proper async context manager mock
            mock_db = AsyncMock()
            mock_db.commit = AsyncMock(return_value=None)
            mock_db.execute = AsyncMock()

            # Mock the async context manager
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value = mock_session_instance

            # Mock provider statuses query result
            mock_result = Mock()  # Regular Mock, not AsyncMock
            mock_scalars = Mock()  # Regular Mock for scalars result
            mock_scalars.all.return_value = []  # Empty list of providers
            mock_result.scalars.return_value = mock_scalars
            mock_db.execute.return_value = mock_result

            # Run daily health check
            results = await self.monitor.daily_health_check()

            # Verify structure
            assert "timestamp" in results
            assert "total_providers" in results
            assert "healthy_providers" in results
            assert "unhealthy_providers" in results
            assert "disabled_providers" in results
            assert "enabled_providers" in results
            assert "actions_taken" in results
            assert "provider_details" in results

            assert isinstance(results["actions_taken"], list)
            assert isinstance(results["provider_details"], list)

            # Verify the database session was used correctly
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_auto_check(self):
        """Test error handling in auto-disable/enable check."""
        # Create a provider status that will cause an exception
        provider_status = MagicMock()
        provider_status.is_enabled = True
        # Make uptime_percentage raise an exception when accessed
        type(provider_status).uptime_percentage = PropertyMock(
            side_effect=Exception("Test error")
        )

        # Should return None and not raise exception
        result = await self.monitor._check_auto_disable_enable(provider_status)
        assert result is None


# Mock PropertyMock for the test
from unittest.mock import PropertyMock
