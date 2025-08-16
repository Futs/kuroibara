import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.providers.base import BaseProvider
from app.core.providers.enhanced_generic import EnhancedGenericProvider
from app.core.providers.factory import provider_factory
from app.core.providers.generic import GenericProvider
from app.core.providers.mangadex import MangaDexProvider
from app.core.providers.mangapill import MangaPillProvider

# Import agent system for new architecture
try:
    from app.core.agents.compatibility import compatibility_provider_registry

    AGENT_SYSTEM_AVAILABLE = True
except ImportError:
    AGENT_SYSTEM_AVAILABLE = False

# from app.core.providers.mangasee import MangaSeeProvider  # Module not found

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for manga providers.

    This class now serves as a compatibility layer that delegates to the
    new agent system when available, while maintaining backward compatibility.
    """

    def __init__(self):
        # Check if agent system is available
        if AGENT_SYSTEM_AVAILABLE:
            logger.info("Initializing ProviderRegistry with Agent System backend")
            self._use_agent_system = True
            self._agent_registry = compatibility_provider_registry
            # Delegate initialization to agent system
            return

        # Fallback to legacy provider system
        logger.info("Initializing ProviderRegistry with legacy provider system")
        self._use_agent_system = False
        self._providers: Dict[str, BaseProvider] = {}

        # Initialize provider factory
        provider_factory.register_provider_class(MangaDexProvider)
        provider_factory.register_provider_class(MangaPillProvider)

        # MangaSeeProvider removed - moved to weebcentral.com
        provider_factory.register_provider_class(GenericProvider)
        provider_factory.register_provider_class(EnhancedGenericProvider)
        logger.info("Registered provider classes")

        # Load provider configurations
        self._load_provider_configs()

        # Register default providers if no configs were loaded
        if not self._providers:
            logger.info(
                "No providers loaded from config, registering default providers"
            )
            self.register_provider(MangaDexProvider())
            # MangaPlusProvider removed - protobuf dependency
            # MangaSeeProvider removed - moved to weebcentral.com

        logger.info(
            f"ProviderRegistry initialized with {len(self._providers)} providers: {list(self._providers.keys())}"
        )

    def register_provider(self, provider: BaseProvider) -> None:
        """Register a provider."""
        if self._use_agent_system:
            return self._agent_registry.register_provider(provider)
        else:
            self._providers[provider.name.lower()] = provider

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        if self._use_agent_system:
            return self._agent_registry.get_provider(name)
        else:
            return self._providers.get(name.lower())

    def get_all_providers(self) -> List[BaseProvider]:
        """Get all registered providers."""
        if self._use_agent_system:
            return self._agent_registry.get_all_providers()
        else:
            return list(self._providers.values())

    def get_provider_names(self) -> List[str]:
        """Get the names of all registered providers."""
        if self._use_agent_system:
            return self._agent_registry.get_provider_names()
        else:
            return sorted([provider.name for provider in self._providers.values()])

    def get_provider_info(self) -> List[Dict[str, Any]]:
        """Get information about all registered providers."""
        if self._use_agent_system:
            return self._agent_registry.get_provider_info()

        # Legacy implementation for fallback
        # Get all providers with their priority information
        providers_with_priority = []

        for provider in self._providers.values():
            provider_id = provider.name.lower()

            # Get priority from provider config (default to 999 for unspecified)
            priority = 999
            for config in provider_factory._provider_configs.values():
                if config.get("id") == provider_id:
                    priority = config.get("priority", 999)
                    break

            providers_with_priority.append((provider, priority))

        # Sort by priority (lower numbers = higher priority), then by name
        providers_with_priority.sort(key=lambda x: (x[1], x[0].name.lower()))

        # Define default providers for is_priority flag
        default_providers = [
            "mangadex",
            "mangaplus",
            "mangasee",
            "toonily",
            "mangabuddy",
            "mangadna",
            "manga18fx",
            "webcomicsapp",
        ]

        # Build provider info list with requires_flaresolverr information
        provider_info_list = []
        for provider, priority in providers_with_priority:
            provider_id = provider.name.lower()

            # Get requires_flaresolverr and enabled status from provider config
            requires_flaresolverr = False
            enabled = True
            for config in provider_factory._provider_configs.values():
                if config.get("id") == provider_id:
                    requires_flaresolverr = config.get("requires_flaresolverr", False)
                    enabled = config.get("enabled", True)
                    break

            provider_info_list.append(
                {
                    "id": provider_id,
                    "name": provider.name,
                    "url": provider.url,
                    "supports_nsfw": provider.supports_nsfw,
                    "requires_flaresolverr": requires_flaresolverr,
                    "enabled": enabled,
                    "is_priority": provider.name.lower() in default_providers,
                    "priority": priority,
                }
            )

        return provider_info_list

    def _load_provider_configs(self) -> None:
        """Load provider configurations from JSON files."""
        try:
            # Get the directory containing provider configurations
            config_dir = Path(__file__).parent / "config"

            # Check if directory exists
            if not config_dir.exists():
                logger.warning(f"Provider config directory not found: {config_dir}")
                return

            # Check if FlareSolverr is available
            flaresolverr_url = os.getenv("FLARESOLVERR_URL")
            flaresolverr_available = bool(flaresolverr_url and flaresolverr_url.strip())

            if flaresolverr_available:
                logger.info(f"FlareSolverr available at: {flaresolverr_url}")
            else:
                logger.info(
                    "FlareSolverr not configured - Cloudflare-protected providers will be disabled"
                )

            # Define config files to load (order matters - default providers get priority)
            config_files = ["providers_default.json"]

            # Add Cloudflare providers if FlareSolverr is available (loaded after defaults)
            if flaresolverr_available:
                config_files.append("providers_cloudflare.json")
                logger.info("Loading Cloudflare-protected providers (lower priority)")

            # Add community providers (loaded last with lowest priority)
            community_dir = config_dir / "community"
            if community_dir.exists():
                community_files = list(community_dir.glob("*.json"))
                if community_files:
                    logger.info(
                        f"Found {len(community_files)} community provider files"
                    )
                    # Add community files to the list
                    for community_file in sorted(community_files):
                        config_files.append(f"community/{community_file.name}")

            # Fallback to old batch files if new structure doesn't exist
            if not (config_dir / "providers_default.json").exists():
                logger.info("Using legacy provider configuration files")
                config_files = [
                    "providers_batch1.json",
                    "providers_batch2.json",
                    "providers_batch3.json",
                    "providers_batch4.json",
                ]

            # Load specified config files
            for config_filename in config_files:
                config_file = config_dir / config_filename
                if not config_file.exists():
                    logger.warning(f"Config file not found: {config_file}")
                    continue

                try:
                    logger.info(f"Loading provider config from {config_file}")

                    # Load and filter providers based on FlareSolverr availability
                    with open(config_file, "r") as f:
                        import json

                        provider_configs = json.load(f)

                    # Filter out Cloudflare providers if FlareSolverr is not available
                    # Also filter out disabled providers
                    filtered_configs = []
                    for config in provider_configs:
                        # Check if provider is enabled (default to True if not specified)
                        is_enabled = config.get("enabled", True)
                        if not is_enabled:
                            logger.info(
                                f"Skipping {config.get('name', 'Unknown')} - provider is disabled"
                            )
                            continue

                        requires_flaresolverr = config.get(
                            "requires_flaresolverr", False
                        )
                        if requires_flaresolverr and not flaresolverr_available:
                            logger.debug(
                                f"Skipping {config.get('name', 'Unknown')} - requires FlareSolverr"
                            )
                            continue

                        # Add FlareSolverr URL to params if available and needed
                        if flaresolverr_available and config.get("params", {}).get(
                            "use_flaresolverr"
                        ):
                            config["params"]["flaresolverr_url"] = flaresolverr_url

                        filtered_configs.append(config)

                    # Load filtered configs into factory
                    provider_factory._provider_configs.update(
                        {config["id"]: config for config in filtered_configs}
                    )

                    # Create providers from filtered config
                    providers = []
                    for config in filtered_configs:
                        try:
                            provider = provider_factory.create_provider(config["id"])
                            if provider:
                                providers.append(provider)
                        except Exception as e:
                            logger.error(
                                f"Failed to create provider {config.get('name', 'Unknown')}: {e}"
                            )

                    # Register providers
                    for provider in providers:
                        self.register_provider(provider)

                    logger.info(f"Loaded {len(providers)} providers from {config_file}")
                except Exception as e:
                    logger.error(
                        f"Error loading provider config from {config_file}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error loading provider configs: {e}")


# Create a singleton instance
provider_registry = ProviderRegistry()
