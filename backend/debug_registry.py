#!/usr/bin/env python3
"""
Debug script to understand why the registry is not loading the correct NSFW settings.
"""

import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add debug logging
import logging

logging.basicConfig(level=logging.DEBUG)


def debug_config_loading():
    """Debug the config loading process."""
    print("=== Debugging Config Loading ===")

    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")

    # Check registry file location
    registry_file = Path(__file__).parent / "app" / "core" / "providers" / "registry.py"
    print(f"Registry file path: {registry_file.absolute()}")
    print(f"Registry file exists: {registry_file.exists()}")

    # Check config directory from registry perspective
    config_dir = registry_file.parent / "config"
    print(f"Config dir from registry: {config_dir.absolute()}")
    print(f"Config dir exists: {config_dir.exists()}")

    # Check default file
    default_file = config_dir / "providers_default.json"
    print(f"Default file path: {default_file.absolute()}")
    print(f"Default file exists: {default_file.exists()}")

    # List all config files
    if config_dir.exists():
        config_files = list(config_dir.glob("*.json"))
        print(f"Available config files: {[f.name for f in config_files]}")

    print()


def debug_agent_system():
    """Debug the agent system loading."""
    print("=== Debugging Agent System ===")

    from app.core.providers.registry import provider_registry

    providers = provider_registry.get_all_providers()
    print(f"Providers loaded: {len(providers)}")
    print(f"Provider names: {[p.name for p in providers]}")

    # Check specific NSFW providers
    nsfw_providers = ["Manga18FX", "MangaDNA"]
    for provider_name in nsfw_providers:
        provider = provider_registry.get_provider(provider_name)
        if provider:
            print(f"{provider_name} provider:")
            print(f"  - supports_nsfw: {provider.supports_nsfw}")
            print(f"  - url: {provider.url}")
            print(f"  - type: {type(provider).__name__}")
        else:
            print(f"{provider_name}: NOT FOUND in registry")

    print()


def debug_registry_loading():
    """Debug the registry loading process."""
    print("=== Debugging Registry Loading ===")

    # Import registry to trigger loading
    from app.core.providers.registry import provider_registry

    # Get provider info
    providers_info = provider_registry.get_provider_info()
    print(f"Registry loaded {len(providers_info)} providers")

    # Check NSFW providers specifically
    nsfw_providers = ["manga18fx", "mangadna"]
    for provider_id in nsfw_providers:
        provider_info = next(
            (p for p in providers_info if p["id"] == provider_id), None
        )
        if provider_info:
            print(f"{provider_id} in registry:")
            print(f"  - supports_nsfw: {provider_info.get('supports_nsfw', 'NOT SET')}")
            print(f"  - url: {provider_info.get('url', 'NOT SET')}")
            print(f"  - enabled: {provider_info.get('enabled', 'NOT SET')}")
            print(f"  - priority: {provider_info.get('priority', 'NOT SET')}")
        else:
            print(f"{provider_id}: NOT FOUND in registry")

    print()


def check_config_file_contents():
    """Check the actual contents of config files."""
    print("=== Checking Config File Contents ===")

    config_dir = Path(__file__).parent / "app" / "core" / "providers" / "config"

    # Check providers_default.json
    default_file = config_dir / "providers_default.json"
    if default_file.exists():
        import json

        with open(default_file, "r") as f:
            default_configs = json.load(f)

        print(f"providers_default.json contains {len(default_configs)} providers")
        nsfw_providers = ["manga18fx", "mangadna"]
        for provider_id in nsfw_providers:
            provider_config = next(
                (p for p in default_configs if p["id"] == provider_id), None
            )
            if provider_config:
                print(
                    f"  {provider_id}: supports_nsfw = {provider_config.get('supports_nsfw', 'NOT SET')}"
                )
            else:
                print(f"  {provider_id}: NOT FOUND in providers_default.json")
    else:
        print("providers_default.json does not exist!")

    # Check batch files
    batch_files = [
        "providers_batch1.json",
        "providers_batch2.json",
        "providers_batch3.json",
        "providers_batch4.json",
    ]
    for batch_file in batch_files:
        batch_path = config_dir / batch_file
        if batch_path.exists():
            with open(batch_path, "r") as f:
                batch_configs = json.load(f)

            print(f"{batch_file} contains {len(batch_configs)} providers")
            nsfw_providers = ["manga18fx", "mangadna"]
            for provider_id in nsfw_providers:
                provider_config = next(
                    (p for p in batch_configs if p["id"] == provider_id), None
                )
                if provider_config:
                    print(
                        f"  {provider_id}: supports_nsfw = {provider_config.get('supports_nsfw', 'NOT SET')}"
                    )

    print()


def main():
    """Run all debug checks."""
    print("🔍 Starting Registry Debug Session\n")

    try:
        debug_config_loading()
        check_config_file_contents()
        debug_agent_system()
        debug_registry_loading()

        print("🎯 Debug session completed!")
        print("\n📋 Key Findings:")
        print("  • Check if providers_default.json is being loaded")
        print("  • Verify NSFW settings in loaded configs")
        print("  • Identify which config files are actually being used")
        print("  • Confirm agent system loading behavior")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
