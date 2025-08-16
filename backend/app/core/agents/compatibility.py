"""
Compatibility layer between the old ProviderRegistry and new AgentRegistry.

This module provides a bridge to ensure existing code continues to work
while gradually migrating to the agent-based architecture.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.providers.base import BaseProvider

from .base import AgentCapability
from .registry import agent_registry

logger = logging.getLogger(__name__)


class AgentProviderAdapter:
    """
    Adapter that makes agents look like providers for backward compatibility.

    This allows existing code that expects BaseProvider instances to work
    seamlessly with the new agent system.
    """

    def __init__(self, agent):
        self._agent = agent

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def url(self) -> str:
        return self._agent.url

    @property
    def supports_nsfw(self) -> bool:
        return self._agent.supports_nsfw

    async def search(self, query: str, page: int = 1, limit: int = 20):
        """Search using the agent."""
        return await self._agent.search(query, page, limit)

    async def get_manga_details(self, manga_id: str):
        """Get manga details using the agent."""
        return await self._agent.get_manga_details(manga_id)

    async def get_chapters(self, manga_id: str, page: int = 1, limit: int = 100):
        """Get chapters using the agent."""
        return await self._agent.get_chapters(manga_id, page, limit)

    async def get_pages(self, manga_id: str, chapter_id: str):
        """Get pages using the agent."""
        return await self._agent.get_pages(manga_id, chapter_id)

    async def download_page(self, page_url: str):
        """Download page using the agent."""
        return await self._agent.download_page(page_url)

    async def download_cover(self, manga_id: str):
        """Download cover using the agent."""
        return await self._agent.download_cover(manga_id)

    async def health_check(self, timeout: int = 30):
        """Health check using the agent."""
        return await self._agent.health_check(timeout)

    def __getattr__(self, name):
        """Delegate any other attributes to the agent."""
        return getattr(self._agent, name)


class CompatibilityProviderRegistry:
    """
    Compatibility layer that provides the old ProviderRegistry interface
    while using the new AgentRegistry underneath.

    This ensures existing code continues to work without modification.
    """

    def __init__(self):
        self._agent_registry = agent_registry
        logger.info(
            "Initialized CompatibilityProviderRegistry with AgentRegistry backend"
        )

    def register_provider(self, provider: BaseProvider) -> None:
        """
        Register a provider (compatibility method).

        Note: This method is deprecated. New providers should be registered
        as agents directly with the AgentRegistry.
        """
        logger.warning(
            f"register_provider() is deprecated. Provider {provider.name} "
            "should be registered as an agent instead."
        )
        # For now, we could wrap the provider as an agent, but this is not recommended

    def get_provider(self, name: str) -> Optional[AgentProviderAdapter]:
        """
        Get a provider by name (returns agent wrapped as provider).

        Args:
            name: Name of the provider

        Returns:
            AgentProviderAdapter wrapping the agent, or None if not found
        """
        # Try exact match first
        agent = self._agent_registry.get_agent(name)
        if agent:
            return AgentProviderAdapter(agent)

        # Try case-insensitive match
        agent = self._agent_registry.get_agent(name.lower())
        if agent:
            return AgentProviderAdapter(agent)

        # Try finding by case-insensitive search through all agents
        for agent in self._agent_registry.get_all_agents():
            if agent.name.lower() == name.lower():
                return AgentProviderAdapter(agent)

        return None

    def get_all_providers(self) -> List[AgentProviderAdapter]:
        """Get all providers (returns agents wrapped as providers)."""
        agents = self._agent_registry.get_all_agents()
        return [AgentProviderAdapter(agent) for agent in agents]

    def get_provider_names(self) -> List[str]:
        """Get the names of all providers."""
        agents = self._agent_registry.get_all_agents()
        return sorted([agent.name for agent in agents])

    def get_provider_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all providers.

        This method maintains compatibility with the old format while
        adding new agent-specific information.
        """
        agent_info = self._agent_registry.get_agent_info()

        # Convert agent info to provider info format for compatibility
        provider_info = []
        for info in agent_info:
            # Extract priority from agent config if available
            priority = 999
            if hasattr(self._agent_registry.get_agent(info["name"]), "priority"):
                priority = self._agent_registry.get_agent(info["name"]).priority

            provider_info.append(
                {
                    "id": info["id"],
                    "name": info["name"],
                    "url": info["url"],
                    "supports_nsfw": info["supports_nsfw"],
                    "requires_flaresolverr": getattr(
                        self._agent_registry.get_agent(info["name"]),
                        "requires_flaresolverr",
                        False,
                    ),
                    "enabled": info["status"] == "active",
                    "is_priority": priority
                    < 50,  # Agents with priority < 50 are considered priority
                    "priority": priority,
                    # New agent-specific fields
                    "agent_status": info["status"],
                    "capabilities": info["capabilities"],
                    "metrics": info["metrics"],
                }
            )

        return provider_info

    # New methods that leverage agent capabilities

    def get_providers_by_capability(
        self, capability: AgentCapability
    ) -> List[AgentProviderAdapter]:
        """
        Get providers that support a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List of providers (agents) that support the capability
        """
        agents = self._agent_registry.get_agents_by_capability(capability)
        return [AgentProviderAdapter(agent) for agent in agents]

    def get_best_provider_for_capability(
        self, capability: AgentCapability
    ) -> Optional[AgentProviderAdapter]:
        """
        Get the best provider for a specific capability.

        Args:
            capability: The capability needed

        Returns:
            The best performing provider for the capability
        """
        agent = self._agent_registry.get_best_agent_for_capability(capability)
        if agent:
            return AgentProviderAdapter(agent)
        return None

    def get_active_providers(self) -> List[AgentProviderAdapter]:
        """Get all active providers."""
        agents = self._agent_registry.get_active_agents()
        return [AgentProviderAdapter(agent) for agent in agents]

    def enable_provider(self, provider_name: str) -> bool:
        """Enable a provider."""
        return self._agent_registry.enable_agent(provider_name)

    def disable_provider(self, provider_name: str) -> bool:
        """Disable a provider."""
        return self._agent_registry.disable_agent(provider_name)

    def reset_provider_circuit_breaker(self, provider_name: str) -> bool:
        """Reset circuit breaker for a provider."""
        return self._agent_registry.reset_agent_circuit_breaker(provider_name)

    def get_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all providers."""
        agent_info = self._agent_registry.get_agent_info()
        metrics = {}

        for info in agent_info:
            metrics[info["name"]] = info["metrics"]

        return metrics

    # Compatibility properties
    @property
    def _providers(self):
        """Compatibility property for code that accesses _providers directly."""
        agents = self._agent_registry.get_all_agents()
        return {agent.name.lower(): AgentProviderAdapter(agent) for agent in agents}


# Create compatibility instance that can replace the old provider_registry
compatibility_provider_registry = CompatibilityProviderRegistry()
