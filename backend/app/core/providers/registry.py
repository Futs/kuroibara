import os
import logging
from typing import Dict, List, Optional, Type
from pathlib import Path

from app.core.providers.base import BaseProvider
from app.core.providers.factory import provider_factory
from app.core.providers.mangadex import MangaDexProvider
from app.core.providers.mangaplus import MangaPlusProvider
from app.core.providers.mangasee import MangaSeeProvider
from app.core.providers.generic import GenericProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for manga providers."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}

        # Initialize provider factory
        provider_factory.register_provider_class(MangaDexProvider)
        provider_factory.register_provider_class(MangaPlusProvider)
        provider_factory.register_provider_class(MangaSeeProvider)
        provider_factory.register_provider_class(GenericProvider)

        # Load provider configurations
        self._load_provider_configs()

        # Register default providers if no configs were loaded
        if not self._providers:
            self.register_provider(MangaDexProvider())
            self.register_provider(MangaPlusProvider())
            self.register_provider(MangaSeeProvider())

    def register_provider(self, provider: BaseProvider) -> None:
        """Register a provider."""
        self._providers[provider.name.lower()] = provider

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a provider by name."""
        return self._providers.get(name.lower())

    def get_all_providers(self) -> List[BaseProvider]:
        """Get all registered providers."""
        return list(self._providers.values())

    def get_provider_names(self) -> List[str]:
        """Get the names of all registered providers."""
        return [provider.name for provider in self._providers.values()]

    def _load_provider_configs(self) -> None:
        """Load provider configurations from JSON files."""
        try:
            # Get the directory containing provider configurations
            config_dir = Path(__file__).parent / "config"

            # Check if directory exists
            if not config_dir.exists():
                logger.warning(f"Provider config directory not found: {config_dir}")
                return

            # Load all JSON files in the config directory
            for config_file in config_dir.glob("*.json"):
                try:
                    logger.info(f"Loading provider config from {config_file}")
                    provider_factory.load_provider_configs(str(config_file))

                    # Create providers from config
                    providers = provider_factory.create_all_providers()

                    # Register providers
                    for provider in providers:
                        self.register_provider(provider)

                    logger.info(f"Loaded {len(providers)} providers from {config_file}")
                except Exception as e:
                    logger.error(f"Error loading provider config from {config_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading provider configs: {e}")


# Create a singleton instance
provider_registry = ProviderRegistry()
