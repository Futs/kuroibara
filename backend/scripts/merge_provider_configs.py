#!/usr/bin/env python3
"""
Script to merge provider configuration files.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def merge_provider_configs():
    """Merge provider configuration files."""
    # Get the directory containing provider configurations
    config_dir = Path(__file__).parent.parent / "app" / "core" / "providers" / "config"

    # Check if directory exists
    if not config_dir.exists():
        print(f"Provider config directory not found: {config_dir}")
        return

    # Get all JSON files in the config directory
    config_files = list(config_dir.glob("providers_batch*.json"))

    if not config_files:
        print("No provider batch files found")
        return

    # Load all provider configurations
    all_providers = []
    for config_file in config_files:
        print(f"Loading provider config from {config_file}")
        with open(config_file, "r") as f:
            providers = json.load(f)
            all_providers.extend(providers)

    # Save merged configuration
    output_file = config_dir / "providers.json"
    with open(output_file, "w") as f:
        json.dump(all_providers, f, indent=2)

    print(f"Merged {len(all_providers)} providers into {output_file}")


if __name__ == "__main__":
    merge_provider_configs()
