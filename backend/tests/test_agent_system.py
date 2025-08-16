"""
Comprehensive tests for the agent system.

This module tests all aspects of the agent architecture including
agent registry, error isolation, monitoring, and configuration.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agents import (
    AgentCapability,
    AgentStatus,
    BaseAgent,
    agent_config_manager,
    agent_monitor,
    agent_registry,
    isolation_manager,
)
from app.core.agents.provider_agent import ProviderAgent
from app.core.providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def __init__(self, name="TestProvider", fail_requests=False):
        self._name = name
        self._fail_requests = fail_requests

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return "https://test.example.com"

    @property
    def supports_nsfw(self) -> bool:
        return False

    async def search(self, query: str, page: int = 1, limit: int = 20):
        if self._fail_requests:
            raise Exception("Mock search failure")
        return [], 0, False

    async def get_manga_details(self, manga_id: str):
        if self._fail_requests:
            raise Exception("Mock details failure")
        return {}

    async def get_chapters(self, manga_id: str, page: int = 1, limit: int = 100):
        if self._fail_requests:
            raise Exception("Mock chapters failure")
        return [], 0, False

    async def get_pages(self, manga_id: str, chapter_id: str):
        if self._fail_requests:
            raise Exception("Mock pages failure")
        return []

    async def download_page(self, page_url: str):
        if self._fail_requests:
            raise Exception("Mock download failure")
        return b"mock image data"

    async def download_cover(self, manga_id: str):
        if self._fail_requests:
            raise Exception("Mock cover failure")
        return b"mock cover data"

    async def health_check(self, timeout: int = 30):
        if self._fail_requests:
            return False, 5000, "Mock health check failure"
        return True, 100, None


class TestAgentSystem:
    """Test suite for the agent system."""

    def test_agent_registry_basic_functionality(self):
        """Test basic agent registry functionality."""
        # Test getting all agents
        agents = agent_registry.get_all_agents()
        assert len(agents) > 0, "Should have agents loaded"

        # Test getting agent by name
        first_agent = agents[0]
        retrieved_agent = agent_registry.get_agent(first_agent.name)
        assert retrieved_agent is not None, "Should retrieve agent by name"
        assert retrieved_agent.name == first_agent.name, "Retrieved agent should match"

    def test_capability_based_selection(self):
        """Test capability-based agent selection."""
        # Test getting agents by capability
        search_agents = agent_registry.get_agents_by_capability(AgentCapability.SEARCH)
        assert len(search_agents) > 0, "Should have agents with search capability"

        # Test getting best agent for capability
        best_agent = agent_registry.get_best_agent_for_capability(
            AgentCapability.SEARCH
        )
        assert best_agent is not None, "Should have a best agent for search"
        assert (
            AgentCapability.SEARCH in best_agent.capabilities
        ), "Best agent should have search capability"

    def test_agent_status_management(self):
        """Test agent status management."""
        agents = agent_registry.get_all_agents()
        if not agents:
            pytest.skip("No agents available for testing")

        test_agent = agents[0]
        original_status = test_agent.status

        # Test enabling/disabling
        agent_registry.disable_agent(test_agent.name)
        assert test_agent.status == AgentStatus.INACTIVE, "Agent should be disabled"

        agent_registry.enable_agent(test_agent.name)
        assert test_agent.status == AgentStatus.ACTIVE, "Agent should be enabled"

        # Restore original status
        test_agent.status = original_status

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling and circuit breaker."""
        # Create a mock provider that fails
        mock_provider = MockProvider("TestFailingProvider", fail_requests=True)
        test_agent = ProviderAgent(mock_provider)

        # Test that errors are handled properly
        with pytest.raises(Exception):
            await test_agent.search("test query")

        # Check that metrics were updated
        assert test_agent.metrics.failed_requests > 0, "Should record failed requests"
        assert test_agent.metrics.success_rate == 0.0, "Success rate should be 0%"

    @pytest.mark.asyncio
    async def test_agent_success_tracking(self):
        """Test agent success tracking."""
        # Create a mock provider that succeeds
        mock_provider = MockProvider("TestSuccessProvider", fail_requests=False)
        test_agent = ProviderAgent(mock_provider)

        # Test successful operation
        result = await test_agent.search("test query")
        assert result == ([], 0, False), "Should return expected result"

        # Check that metrics were updated
        assert (
            test_agent.metrics.successful_requests > 0
        ), "Should record successful requests"
        assert test_agent.metrics.success_rate == 100.0, "Success rate should be 100%"

    def test_monitoring_system(self):
        """Test the monitoring system."""
        # Test metrics summary
        summary = agent_monitor.get_agent_metrics_summary()
        assert "total_agents" in summary, "Summary should include total agents"
        assert "active_agents" in summary, "Summary should include active agents"
        assert "agents" in summary, "Summary should include agent list"

        # Test performance report
        report = agent_monitor.get_performance_report()
        assert (
            "overall_statistics" in report
        ), "Report should include overall statistics"
        assert "generated_at" in report, "Report should include generation timestamp"

    def test_configuration_system(self):
        """Test the configuration system."""
        agents = agent_registry.get_all_agents()
        if not agents:
            pytest.skip("No agents available for testing")

        test_agent_name = agents[0].name

        # Test getting configuration
        config = agent_config_manager.get_agent_config(test_agent_name)
        assert isinstance(config, dict), "Configuration should be a dictionary"

        # Test updating configuration
        original_enabled = config.get("enabled", True)
        result = agent_config_manager.update_agent_config(
            test_agent_name, {"enabled": not original_enabled}, persist=False
        )
        assert result, "Configuration update should succeed"

        # Verify configuration was updated
        updated_config = agent_config_manager.get_agent_config(test_agent_name)
        assert updated_config["enabled"] == (
            not original_enabled
        ), "Configuration should be updated"

        # Reset configuration
        agent_config_manager.update_agent_config(
            test_agent_name, {"enabled": original_enabled}, persist=False
        )

    def test_error_isolation_system(self):
        """Test the error isolation system."""
        # Test isolation status
        status = isolation_manager.get_isolation_status()
        assert (
            "quarantined_agents" in status
        ), "Status should include quarantined agents"
        assert "failure_patterns" in status, "Status should include failure patterns"
        assert "bulkhead_usage" in status, "Status should include bulkhead usage"

        # Test agent configuration
        test_config = {
            "max_concurrent_requests": 2,
            "circuit_breaker_threshold": 3,
            "timeout_threshold": 15,
        }
        isolation_manager.configure_agent_isolation("test_agent", test_config)

        # Verify configuration was applied
        agent_config = isolation_manager.get_agent_config("test_agent")
        assert (
            agent_config["max_concurrent_requests"] == 2
        ), "Configuration should be applied"

    def test_provider_compatibility(self):
        """Test backward compatibility with provider registry."""
        from app.core.providers.registry import provider_registry

        # Test that provider registry works with agent system
        providers = provider_registry.get_all_providers()
        assert len(providers) > 0, "Should have providers available"

        # Test getting provider info
        provider_info = provider_registry.get_provider_info()
        assert len(provider_info) > 0, "Should have provider info"

        # Verify info structure includes agent-specific fields
        first_info = provider_info[0]
        assert "agent_status" in first_info, "Provider info should include agent status"
        assert "capabilities" in first_info, "Provider info should include capabilities"
        assert "metrics" in first_info, "Provider info should include metrics"

    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(self):
        """Test concurrent operations across multiple agents."""
        agents = agent_registry.get_active_agents()[
            :3
        ]  # Test with first 3 active agents

        if len(agents) < 2:
            pytest.skip("Need at least 2 agents for concurrency testing")

        # Create concurrent health check tasks
        tasks = [agent.health_check(timeout=10) for agent in agents]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify results
        assert len(results) == len(agents), "Should have result for each agent"

        # Check that at least some operations succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0, "At least some operations should succeed"

    def test_agent_info_completeness(self):
        """Test that agent info includes all required fields."""
        agent_info = agent_registry.get_agent_info()

        if not agent_info:
            pytest.skip("No agents available for testing")

        required_fields = [
            "id",
            "name",
            "url",
            "supports_nsfw",
            "status",
            "capabilities",
            "metrics",
        ]

        for info in agent_info:
            for field in required_fields:
                assert field in info, f"Agent info should include {field}"

            # Verify metrics structure
            metrics = info["metrics"]
            metrics_fields = ["total_requests", "success_rate", "average_response_time"]
            for field in metrics_fields:
                assert field in metrics, f"Metrics should include {field}"


class TestAgentIsolation:
    """Test suite specifically for agent isolation features."""

    @pytest.mark.asyncio
    async def test_bulkhead_pattern(self):
        """Test bulkhead isolation pattern."""
        # Configure a test agent with limited concurrency
        isolation_manager.configure_agent_isolation(
            "test_bulkhead", {"max_concurrent_requests": 1}
        )

        # Create a slow operation
        async def slow_operation():
            await asyncio.sleep(0.1)
            return "success"

        # Test that bulkhead limits concurrency
        start_time = asyncio.get_event_loop().time()

        tasks = [
            isolation_manager.execute_with_isolation("test_bulkhead", slow_operation)
            for _ in range(3)
        ]

        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # With max_concurrent=1, operations should be serialized
        # Total time should be approximately 3 * 0.1 = 0.3 seconds
        total_time = end_time - start_time
        assert total_time >= 0.25, "Operations should be serialized due to bulkhead"
        assert all(r == "success" for r in results), "All operations should succeed"


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_suite = TestAgentSystem()

    print("Running agent system tests...")

    try:
        test_suite.test_agent_registry_basic_functionality()
        print("✅ Agent registry tests passed")

        test_suite.test_capability_based_selection()
        print("✅ Capability selection tests passed")

        test_suite.test_monitoring_system()
        print("✅ Monitoring system tests passed")

        test_suite.test_configuration_system()
        print("✅ Configuration system tests passed")

        test_suite.test_provider_compatibility()
        print("✅ Provider compatibility tests passed")

        print("\n🎉 All agent system tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
