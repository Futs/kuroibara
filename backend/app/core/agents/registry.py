"""
Agent Registry for managing all agents in the Kuroibara system.

This registry provides centralized management of agents with capability-based
selection, health monitoring, and hot-swappable configuration.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentCapability, AgentStatus, BaseAgent
from .factory import AgentFactory

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for managing all agents in the system.

    Provides:
    - Agent registration and discovery
    - Capability-based agent selection
    - Health monitoring and status tracking
    - Hot-swappable configuration
    - Error isolation between agents
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agents_by_capability: Dict[AgentCapability, List[BaseAgent]] = {}
        self._factory = AgentFactory()

        logger.info("Initializing AgentRegistry")

        # Initialize capability mapping
        for capability in AgentCapability:
            self._agents_by_capability[capability] = []

        # Load agent configurations
        self._load_agent_configs()

        logger.info(
            f"AgentRegistry initialized with {len(self._agents)} agents: {list(self._agents.keys())}"
        )

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent in the registry.

        Args:
            agent: The agent to register
        """
        agent_id = agent.name.lower()
        self._agents[agent_id] = agent

        # Update capability mapping
        for capability in agent.capabilities:
            if agent not in self._agents_by_capability[capability]:
                self._agents_by_capability[capability].append(agent)

        logger.info(
            f"Registered agent: {agent.name} with capabilities: {[c.value for c in agent.capabilities]}"
        )

    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent from the registry.

        Args:
            agent_name: Name of the agent to unregister

        Returns:
            True if agent was found and removed, False otherwise
        """
        agent_id = agent_name.lower()
        agent = self._agents.get(agent_id)

        if not agent:
            return False

        # Remove from main registry
        del self._agents[agent_id]

        # Remove from capability mapping
        for capability in agent.capabilities:
            if agent in self._agents_by_capability[capability]:
                self._agents_by_capability[capability].remove(agent)

        logger.info(f"Unregistered agent: {agent.name}")
        return True

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name (case-insensitive).

        Args:
            name: Name of the agent

        Returns:
            The agent if found, None otherwise
        """
        # Try exact lowercase match first
        agent = self._agents.get(name.lower())
        if agent:
            return agent

        # Try case-insensitive search through all agents
        for agent in self._agents.values():
            if agent.name.lower() == name.lower():
                return agent

        return None

    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())

    def get_active_agents(self) -> List[BaseAgent]:
        """Get all agents that are currently active."""
        return [agent for agent in self._agents.values() if agent.is_healthy()]

    def get_agents_by_capability(self, capability: AgentCapability) -> List[BaseAgent]:
        """
        Get all agents that support a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List of agents that support the capability
        """
        return [
            agent
            for agent in self._agents_by_capability[capability]
            if agent.is_healthy()
        ]

    def get_best_agent_for_capability(
        self, capability: AgentCapability
    ) -> Optional[BaseAgent]:
        """
        Get the best agent for a specific capability based on performance metrics.

        Args:
            capability: The capability needed

        Returns:
            The best performing agent for the capability, or None if none available
        """
        agents = self.get_agents_by_capability(capability)

        if not agents:
            return None

        # Sort by success rate (descending) and average response time (ascending)
        agents.sort(
            key=lambda a: (-a.metrics.success_rate, a.metrics.average_response_time)
        )

        return agents[0]

    def get_agent_info(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all registered agents.

        Returns:
            List of dictionaries containing agent information
        """
        agent_info = []

        for agent in self._agents.values():
            info = {
                "id": agent.name.lower(),
                "name": agent.name,
                "url": agent.url,
                "supports_nsfw": agent.supports_nsfw,
                "status": agent.status.value,
                "capabilities": [cap.value for cap in agent.capabilities],
                "metrics": {
                    "total_requests": agent.metrics.total_requests,
                    "success_rate": agent.metrics.success_rate,
                    "average_response_time": agent.metrics.average_response_time,
                    "last_request_time": (
                        agent.metrics.last_request_time.isoformat()
                        if agent.metrics.last_request_time
                        else None
                    ),
                    "last_error": agent.metrics.last_error,
                    "circuit_breaker_count": agent.metrics.circuit_breaker_count,
                },
            }
            agent_info.append(info)

        # Sort by status (active first) and success rate
        agent_info.sort(
            key=lambda x: (
                0 if x["status"] == "active" else 1,
                -x["metrics"]["success_rate"],
            )
        )

        return agent_info

    def enable_agent(self, agent_name: str) -> bool:
        """
        Enable an agent.

        Args:
            agent_name: Name of the agent to enable

        Returns:
            True if successful, False if agent not found
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return False

        if agent.status == AgentStatus.INACTIVE:
            agent.status = AgentStatus.ACTIVE
            logger.info(f"Enabled agent: {agent.name}")

        return True

    def disable_agent(self, agent_name: str) -> bool:
        """
        Disable an agent.

        Args:
            agent_name: Name of the agent to disable

        Returns:
            True if successful, False if agent not found
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return False

        agent.status = AgentStatus.INACTIVE
        logger.info(f"Disabled agent: {agent.name}")
        return True

    def reset_agent_circuit_breaker(self, agent_name: str) -> bool:
        """
        Reset the circuit breaker for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            True if successful, False if agent not found
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return False

        agent.status = AgentStatus.ACTIVE
        agent._circuit_opened_at = None
        logger.info(f"Reset circuit breaker for agent: {agent.name}")
        return True

    def _load_agent_configs(self) -> None:
        """Load agent configurations from JSON files."""
        try:
            # Get the directory containing agent configurations
            config_dir = Path(__file__).parent.parent / "providers" / "config"

            if not config_dir.exists():
                logger.warning(f"Agent config directory not found: {config_dir}")
                return

            # Check if FlareSolverr is available
            flaresolverr_url = os.getenv("FLARESOLVERR_URL")
            flaresolverr_available = bool(flaresolverr_url and flaresolverr_url.strip())

            if flaresolverr_available:
                logger.info(f"FlareSolverr available at: {flaresolverr_url}")
            else:
                logger.info(
                    "FlareSolverr not configured - Cloudflare-protected agents will be disabled"
                )

            # Load provider configurations and convert to agents
            config_files = ["providers_default.json"]

            if flaresolverr_available:
                config_files.append("providers_cloudflare.json")

            for config_filename in config_files:
                config_file = config_dir / config_filename
                if not config_file.exists():
                    logger.warning(f"Config file not found: {config_file}")
                    continue

                try:
                    logger.info(f"Loading agent config from {config_file}")
                    agents = self._factory.create_agents_from_config(
                        config_file, flaresolverr_url
                    )

                    for agent in agents:
                        self.register_agent(agent)

                    logger.info(f"Loaded {len(agents)} agents from {config_file}")

                except Exception as e:
                    logger.error(f"Error loading agent config from {config_file}: {e}")

        except Exception as e:
            logger.error(f"Error loading agent configs: {e}")


# Create a singleton instance
agent_registry = AgentRegistry()
