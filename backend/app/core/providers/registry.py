import logging
from typing import List, Optional

from app.core.agents.compatibility import compatibility_provider_registry
from app.core.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for manga providers using the agent system.

    This class provides a simple interface to the agent-based provider system.
    """

    def __init__(self):
        logger.info("Initializing ProviderRegistry with Agent System")
        self._agent_registry = compatibility_provider_registry

        logger.info("ProviderRegistry initialized with Agent System backend")

    def register_provider(self, provider: BaseProvider) -> None:
        """Register a provider."""
        return self._agent_registry.register_provider(provider)

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return self._agent_registry.get_provider(name)

    def get_all_providers(self) -> List[BaseProvider]:
        """Get all registered providers."""
        return self._agent_registry.get_all_providers()

    def get_provider_names(self) -> List[str]:
        """Get the names of all registered providers."""
        return self._agent_registry.get_provider_names()

    def get_provider_info(self):
        """Get information about all registered providers."""
        return self._agent_registry.get_provider_info()


# Create a singleton instance
provider_registry = ProviderRegistry()
