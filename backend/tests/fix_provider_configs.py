#!/usr/bin/env python3
"""
Script to fix provider configurations by removing invalid 'url' parameter
and moving necessary parameters into 'params' section.
"""

import json
from pathlib import Path


def fix_provider_config(config):
    """Fix a single provider configuration."""
    fixed_config = config.copy()

    # Remove the 'url' parameter if it exists (it's not valid for GenericProvider)
    if "url" in fixed_config:
        del fixed_config["url"]

    # Ensure supports_nsfw is in params for GenericProvider
    if "supports_nsfw" in fixed_config and "params" in fixed_config:
        fixed_config["params"]["supports_nsfw"] = fixed_config["supports_nsfw"]

    return fixed_config


def fix_providers_file(file_path):
    """Fix all providers in a configuration file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            providers = json.load(f)

        # Fix each provider
        fixed_providers = []
        for provider in providers:
            fixed_provider = fix_provider_config(provider)
            fixed_providers.append(fixed_provider)

        # Write back the fixed configuration
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(fixed_providers, f, indent=2, ensure_ascii=False)

        print(f"Fixed {len(fixed_providers)} providers in {file_path}")
        return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix provider configurations."""
    print("=== Fixing Provider Configurations ===\n")

    # Path to the providers_default.json file
    config_file = Path(
        "kuroibara/backend/app/core/providers/config/providers_default.json"
    )

    if config_file.exists():
        success = fix_providers_file(config_file)
        if success:
            print(f"✅ Successfully fixed provider configurations in {config_file}")
        else:
            print(f"❌ Failed to fix provider configurations in {config_file}")
    else:
        print(f"❌ Configuration file not found: {config_file}")


if __name__ == "__main__":
    main()
