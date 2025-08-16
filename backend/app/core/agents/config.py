"""
Agent configuration system for hot-swappable settings.

This module provides dynamic configuration management for agents including
hot-swapping, enable/disable functionality, and runtime configuration updates.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AgentStatus
from .registry import agent_registry

logger = logging.getLogger(__name__)


class AgentConfigManager:
    """
    Configuration manager for agents with hot-swapping capabilities.

    Features:
    - Hot-swappable configuration
    - Enable/disable agents at runtime
    - Configuration validation
    - Configuration persistence
    - Rollback capabilities
    """

    def __init__(self):
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._config_backup: Dict[str, Dict[str, Any]] = {}
        self._config_file_path: Optional[Path] = None
        self._load_default_configs()

    def _load_default_configs(self) -> None:
        """Load default configurations for all agents."""
        try:
            # Get configuration directory
            config_dir = Path(__file__).parent.parent / "providers" / "config"
            self._config_file_path = config_dir / "agent_runtime_config.json"

            # Load existing runtime config if it exists
            if self._config_file_path.exists():
                with open(self._config_file_path, "r") as f:
                    self._config_cache = json.load(f)
                logger.info(
                    f"Loaded runtime configuration from {self._config_file_path}"
                )
            else:
                # Create default configuration for all agents
                self._create_default_config()

        except Exception as e:
            logger.error(f"Error loading agent configurations: {e}")
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration for all agents."""
        agents = agent_registry.get_all_agents()

        for agent in agents:
            self._config_cache[agent.name] = {
                "enabled": True,
                "priority": getattr(agent, "priority", 999),
                "circuit_breaker": {"threshold": 5, "timeout": 300, "enabled": True},
                "rate_limiting": {
                    "max_concurrent": 3,
                    "min_time_between_requests": 1000,  # milliseconds
                    "enabled": True,
                },
                "monitoring": {
                    "health_check_enabled": True,
                    "metrics_collection": True,
                    "alert_on_failures": True,
                },
                "timeouts": {"request_timeout": 30, "health_check_timeout": 30},
            }

        logger.info(f"Created default configuration for {len(agents)} agents")

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Configuration dictionary
        """
        return self._config_cache.get(agent_name, {})

    def update_agent_config(
        self, agent_name: str, config: Dict[str, Any], persist: bool = True
    ) -> bool:
        """
        Update configuration for a specific agent.

        Args:
            agent_name: Name of the agent
            config: New configuration (partial updates supported)
            persist: Whether to persist changes to disk

        Returns:
            True if update was successful
        """
        try:
            # Backup current config
            if agent_name in self._config_cache:
                self._config_backup[agent_name] = self._config_cache[agent_name].copy()

            # Validate configuration
            if not self._validate_config(config):
                logger.error(f"Invalid configuration for agent {agent_name}")
                return False

            # Update configuration (merge with existing)
            if agent_name not in self._config_cache:
                self._config_cache[agent_name] = {}

            self._merge_config(self._config_cache[agent_name], config)

            # Apply configuration to agent
            self._apply_config_to_agent(agent_name, self._config_cache[agent_name])

            # Persist if requested
            if persist:
                self._save_config()

            logger.info(f"Updated configuration for agent {agent_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating configuration for agent {agent_name}: {e}")
            # Rollback on error
            if agent_name in self._config_backup:
                self._config_cache[agent_name] = self._config_backup[agent_name]
            return False

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure and values."""
        try:
            # Check for valid boolean values
            if "enabled" in config and not isinstance(config["enabled"], bool):
                return False

            # Check circuit breaker config
            if "circuit_breaker" in config:
                cb_config = config["circuit_breaker"]
                if "threshold" in cb_config and not isinstance(
                    cb_config["threshold"], int
                ):
                    return False
                if "timeout" in cb_config and not isinstance(
                    cb_config["timeout"], (int, float)
                ):
                    return False

            # Check rate limiting config
            if "rate_limiting" in config:
                rl_config = config["rate_limiting"]
                if "max_concurrent" in rl_config and not isinstance(
                    rl_config["max_concurrent"], int
                ):
                    return False
                if "min_time_between_requests" in rl_config and not isinstance(
                    rl_config["min_time_between_requests"], (int, float)
                ):
                    return False

            # Check timeouts
            if "timeouts" in config:
                timeout_config = config["timeouts"]
                for timeout_key in ["request_timeout", "health_check_timeout"]:
                    if timeout_key in timeout_config and not isinstance(
                        timeout_config[timeout_key], (int, float)
                    ):
                        return False

            return True

        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False

    def _merge_config(
        self, base_config: Dict[str, Any], update_config: Dict[str, Any]
    ) -> None:
        """Merge update configuration into base configuration."""
        for key, value in update_config.items():
            if (
                isinstance(value, dict)
                and key in base_config
                and isinstance(base_config[key], dict)
            ):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value

    def _apply_config_to_agent(self, agent_name: str, config: Dict[str, Any]) -> None:
        """Apply configuration changes to the actual agent."""
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            logger.warning(f"Agent {agent_name} not found for configuration update")
            return

        # Apply enabled/disabled status
        if "enabled" in config:
            if config["enabled"]:
                if agent.status == AgentStatus.INACTIVE:
                    agent.status = AgentStatus.ACTIVE
                    logger.info(f"Enabled agent {agent_name}")
            else:
                agent.status = AgentStatus.INACTIVE
                logger.info(f"Disabled agent {agent_name}")

        # Apply circuit breaker settings
        if "circuit_breaker" in config:
            cb_config = config["circuit_breaker"]
            if "threshold" in cb_config:
                agent._circuit_breaker_threshold = cb_config["threshold"]
            if "timeout" in cb_config:
                agent._circuit_breaker_timeout = cb_config["timeout"]

        # Apply error isolation settings
        try:
            from .error_isolation import isolation_manager

            isolation_manager.configure_agent_isolation(
                agent_name,
                {
                    "max_concurrent_requests": config.get("rate_limiting", {}).get(
                        "max_concurrent", 3
                    ),
                    "circuit_breaker_threshold": config.get("circuit_breaker", {}).get(
                        "threshold", 5
                    ),
                    "circuit_breaker_timeout": config.get("circuit_breaker", {}).get(
                        "timeout", 300
                    ),
                    "timeout_threshold": config.get("timeouts", {}).get(
                        "request_timeout", 30
                    ),
                },
            )
        except ImportError:
            logger.debug("Error isolation system not available")

    def enable_agent(self, agent_name: str) -> bool:
        """Enable an agent."""
        return self.update_agent_config(agent_name, {"enabled": True})

    def disable_agent(self, agent_name: str) -> bool:
        """Disable an agent."""
        return self.update_agent_config(agent_name, {"enabled": False})

    def reset_agent_config(self, agent_name: str) -> bool:
        """Reset agent configuration to defaults."""
        try:
            # Remove from cache to trigger default creation
            if agent_name in self._config_cache:
                del self._config_cache[agent_name]

            # Recreate default config for this agent
            agent = agent_registry.get_agent(agent_name)
            if agent:
                self._config_cache[agent_name] = {
                    "enabled": True,
                    "priority": getattr(agent, "priority", 999),
                    "circuit_breaker": {
                        "threshold": 5,
                        "timeout": 300,
                        "enabled": True,
                    },
                    "rate_limiting": {
                        "max_concurrent": 3,
                        "min_time_between_requests": 1000,
                        "enabled": True,
                    },
                    "monitoring": {
                        "health_check_enabled": True,
                        "metrics_collection": True,
                        "alert_on_failures": True,
                    },
                    "timeouts": {"request_timeout": 30, "health_check_timeout": 30},
                }

                # Apply the reset configuration
                self._apply_config_to_agent(agent_name, self._config_cache[agent_name])
                self._save_config()

                logger.info(f"Reset configuration for agent {agent_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error resetting configuration for agent {agent_name}: {e}")
            return False

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent configurations."""
        return self._config_cache.copy()

    def _save_config(self) -> None:
        """Save configuration to disk."""
        try:
            if self._config_file_path:
                # Ensure directory exists
                self._config_file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(self._config_file_path, "w") as f:
                    json.dump(self._config_cache, f, indent=2)

                logger.debug(f"Saved configuration to {self._config_file_path}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def reload_config(self) -> bool:
        """Reload configuration from disk."""
        try:
            if self._config_file_path and self._config_file_path.exists():
                with open(self._config_file_path, "r") as f:
                    new_config = json.load(f)

                # Apply all configurations
                for agent_name, config in new_config.items():
                    self._config_cache[agent_name] = config
                    self._apply_config_to_agent(agent_name, config)

                logger.info("Reloaded configuration from disk")
                return True

            return False

        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration status."""
        agents = agent_registry.get_all_agents()

        summary = {
            "total_agents": len(agents),
            "enabled_agents": 0,
            "disabled_agents": 0,
            "agents_with_custom_config": 0,
            "configuration_file": (
                str(self._config_file_path) if self._config_file_path else None
            ),
        }

        for agent in agents:
            config = self.get_agent_config(agent.name)
            if config.get("enabled", True):
                summary["enabled_agents"] += 1
            else:
                summary["disabled_agents"] += 1

            # Check if agent has non-default configuration
            if len(config) > 1:  # More than just enabled/disabled
                summary["agents_with_custom_config"] += 1

        return summary


# Global configuration manager instance
agent_config_manager = AgentConfigManager()
