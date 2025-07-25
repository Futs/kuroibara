import importlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from app.core.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating manga providers."""

    def __init__(self):
        self._provider_classes: Dict[str, Type[BaseProvider]] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}

    def register_provider_class(self, provider_class: Type[BaseProvider]) -> None:
        """Register a provider class."""
        self._provider_classes[provider_class.__name__] = provider_class

    def load_provider_configs(self, config_path: str) -> None:
        """Load provider configurations from a JSON file."""
        try:
            with open(config_path, "r") as f:
                configs = json.load(f)

                for config in configs:
                    provider_id = config.get("id", "").lower()
                    if provider_id:
                        self._provider_configs[provider_id] = config
        except Exception as e:
            logger.error(f"Error loading provider configs: {e}")

    def create_provider(self, provider_id: str) -> Optional[BaseProvider]:
        """Create a provider instance from its ID."""
        # Check if provider config exists
        config = self._provider_configs.get(provider_id.lower())
        if not config:
            logger.warning(f"Provider config not found for ID: {provider_id}")
            return None

        # Get provider class
        class_name = config.get("class_name")
        if not class_name:
            logger.warning(f"Class name not specified for provider: {provider_id}")
            return None

        provider_class = self._provider_classes.get(class_name)
        if not provider_class:
            logger.warning(f"Provider class not found: {class_name}")
            return None

        # Create provider instance
        try:
            # Handle special provider cases that have custom constructors
            if provider_id == "mangadex":
                # MangaDexProvider takes no arguments
                return provider_class()
            elif provider_id == "mangaplus":
                # MangaPlusProvider takes no arguments
                return provider_class()
            else:
                # Standard provider initialization
                # Merge top-level config with params
                provider_kwargs = config.get("params", {}).copy()

                # Add required parameters
                provider_kwargs["name"] = config["name"]

                # Handle different provider types
                if class_name == "EnhancedGenericProvider":
                    # EnhancedGenericProvider expects 'base_url', not 'url'
                    if "base_url" not in provider_kwargs:
                        provider_kwargs["base_url"] = config["url"]
                else:
                    # Other providers expect 'url'
                    provider_kwargs["url"] = config["url"]

                # Add important top-level config values
                if "supports_nsfw" in config:
                    provider_kwargs["supports_nsfw"] = config["supports_nsfw"]
                if "use_flaresolverr" in config:
                    provider_kwargs["use_flaresolverr"] = config["use_flaresolverr"]
                if "flaresolverr_url" in config:
                    provider_kwargs["flaresolverr_url"] = config["flaresolverr_url"]

                return provider_class(**provider_kwargs)
        except Exception as e:
            logger.error(f"Error creating provider {provider_id}: {e}")
            return None

    def create_all_providers(self) -> List[BaseProvider]:
        """Create all registered providers."""
        providers = []

        for provider_id in self._provider_configs:
            provider = self.create_provider(provider_id)
            if provider:
                providers.append(provider)

        return providers

    def discover_provider_classes(self, package_path: str) -> None:
        """Discover provider classes in a package."""
        try:
            # Get package directory
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            # Find all Python files in the package
            for file_path in package_dir.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue

                # Import module
                module_name = f"{package_path}.{file_path.stem}"
                try:
                    module = importlib.import_module(module_name)

                    # Find provider classes in module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # Check if attribute is a provider class
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseProvider)
                            and attr is not BaseProvider
                        ):
                            self.register_provider_class(attr)
                except Exception as e:
                    logger.error(f"Error importing module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error discovering provider classes: {e}")


# Create a singleton instance
provider_factory = ProviderFactory()
