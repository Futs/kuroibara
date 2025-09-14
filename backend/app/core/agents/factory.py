"""
Agent Factory for creating agents from configurations.

This factory converts existing provider configurations into agent instances,
providing a bridge between the old provider system and the new agent architecture.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from app.core.providers.base import BaseProvider
from app.core.providers.enhanced_generic import EnhancedGenericProvider
from app.core.providers.generic import GenericProvider
from app.core.providers.hiperdex import HiperDexProvider
from app.core.providers.javascript_provider import JavaScriptProvider
from app.core.providers.madaradex import MadaraDexProvider
from app.core.providers.mangadex import MangaDexProvider
from app.core.providers.mangapill import MangaPillProvider
from app.core.providers.mangasail import MangaSailProvider

from .base import BaseAgent
from .provider_agent import ProviderAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating agents from provider configurations.

    This factory takes existing provider configurations and creates
    agent instances that wrap the providers with agent functionality.
    """

    def __init__(self):
        self._provider_classes: Dict[str, Type[BaseProvider]] = {}
        self._register_provider_classes()

    def _register_provider_classes(self):
        """Register all available provider classes."""
        self._provider_classes.update(
            {
                "MadaraDexProvider": MadaraDexProvider,
                "MangaDexProvider": MangaDexProvider,
                "MangaPillProvider": MangaPillProvider,
                "MangaSailProvider": MangaSailProvider,
                "GenericProvider": GenericProvider,
                "EnhancedGenericProvider": EnhancedGenericProvider,
                "JavaScriptProvider": JavaScriptProvider,
                "HiperDexProvider": HiperDexProvider,
            }
        )

        logger.debug(
            f"Registered provider classes: {list(self._provider_classes.keys())}"
        )

    def create_agent_from_config(
        self, config: Dict[str, Any], flaresolverr_url: Optional[str] = None
    ) -> Optional[BaseAgent]:
        """
        Create an agent from a provider configuration.

        Args:
            config: Provider configuration dictionary
            flaresolverr_url: FlareSolverr URL if available

        Returns:
            Agent instance or None if creation failed
        """
        try:
            provider_id = config.get("id", "").lower()
            if not provider_id:
                logger.warning("Provider config missing ID")
                return None

            # Check if provider is enabled
            if not config.get("enabled", True):
                logger.info(
                    f"Skipping disabled provider: {config.get('name', provider_id)}"
                )
                return None

            # Check FlareSolverr requirements
            requires_flaresolverr = config.get("requires_flaresolverr", False)
            if requires_flaresolverr and not flaresolverr_url:
                logger.debug(
                    f"Skipping {config.get('name', provider_id)} - "
                    f"requires FlareSolverr"
                )
                return None

            # Create provider instance
            provider = self._create_provider_instance(config, flaresolverr_url)
            if not provider:
                return None

            # Wrap provider in agent
            agent = ProviderAgent(provider, config)

            logger.debug(f"Created agent for provider: {provider.name}")
            return agent

        except Exception as e:
            logger.error(
                f"Error creating agent from config {config.get('name', 'Unknown')}: {e}"
            )
            return None

    def _create_provider_instance(
        self, config: Dict[str, Any], flaresolverr_url: Optional[str] = None
    ) -> Optional[BaseProvider]:
        """Create a provider instance from configuration."""
        class_name = config.get("class_name")
        if not class_name:
            logger.warning(f"Class name not specified for provider: {config.get('id')}")
            return None

        provider_class = self._provider_classes.get(class_name)
        if not provider_class:
            logger.warning(f"Provider class not found: {class_name}")
            return None

        try:
            provider_id = config.get("id", "").lower()

            # Handle special provider cases
            if provider_id == "mangadex":
                # MangaDexProvider takes no arguments
                return provider_class()
            elif provider_id == "mangasail":
                # MangaSailProvider takes no arguments
                return provider_class()
            elif provider_id == "hiperdex":
                # HiperDexProvider takes no arguments (self-configuring)
                return provider_class()
            else:
                # Standard provider initialization
                provider_kwargs = config.get("params", {}).copy()

                # Add required parameters
                provider_kwargs["name"] = config["name"]

                # Handle different provider types
                if class_name == "EnhancedGenericProvider":
                    # EnhancedGenericProvider expects 'base_url', not 'url'
                    if "base_url" not in provider_kwargs and "url" in config:
                        provider_kwargs["base_url"] = config["url"]
                else:
                    # Other providers expect 'url'
                    if "url" in config:
                        provider_kwargs["url"] = config["url"]

                # Add important top-level config values
                if "supports_nsfw" in config:
                    provider_kwargs["supports_nsfw"] = config["supports_nsfw"]
                if "use_flaresolverr" in config:
                    provider_kwargs["use_flaresolverr"] = config["use_flaresolverr"]
                if flaresolverr_url and config.get("params", {}).get(
                    "use_flaresolverr"
                ):
                    provider_kwargs["flaresolverr_url"] = flaresolverr_url

                return provider_class(**provider_kwargs)

        except Exception as e:
            logger.error(
                f"Error creating provider instance for "
                f"{config.get('name', 'Unknown')}: {e}"
            )
            return None

    def create_agents_from_config(
        self, config_file: Path, flaresolverr_url: Optional[str] = None
    ) -> List[BaseAgent]:
        """
        Create multiple agents from a configuration file.

        Args:
            config_file: Path to the configuration file
            flaresolverr_url: FlareSolverr URL if available

        Returns:
            List of created agents
        """
        agents = []

        try:
            with open(config_file, "r") as f:
                provider_configs = json.load(f)

            for config in provider_configs:
                agent = self.create_agent_from_config(config, flaresolverr_url)
                if agent:
                    agents.append(agent)

            logger.info(f"Created {len(agents)} agents from {config_file}")

        except Exception as e:
            logger.error(f"Error loading agents from {config_file}: {e}")

        return agents

    def register_provider_class(self, provider_class: Type[BaseProvider]) -> None:
        """
        Register a new provider class.

        Args:
            provider_class: The provider class to register
        """
        self._provider_classes[provider_class.__name__] = provider_class
        logger.debug(f"Registered provider class: {provider_class.__name__}")

    def get_registered_classes(self) -> List[str]:
        """Get list of registered provider class names."""
        return list(self._provider_classes.keys())
