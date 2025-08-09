#!/usr/bin/env python3
"""
Script to determine which providers are actually active in Kuroibara
based on the loading logic in the provider registry.
"""

import json
import os
from pathlib import Path
from typing import Dict, List


def load_providers_from_file(file_path: Path) -> List[Dict]:
    """Load providers from a JSON configuration file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return []


def simulate_provider_loading():
    """Simulate the provider loading logic from the registry."""
    config_dir = Path("kuroibara/backend/app/core/providers/config")

    # Check if FlareSolverr is available (simulate environment)
    flaresolverr_url = os.getenv("FLARESOLVERR_URL")
    flaresolverr_available = bool(flaresolverr_url and flaresolverr_url.strip())

    print(f"FlareSolverr available: {flaresolverr_available}")
    if flaresolverr_available:
        print(f"FlareSolverr URL: {flaresolverr_url}")

    # Define config files to load (order matters - default providers get priority)
    config_files = ["providers_default.json"]

    # Add Cloudflare providers if FlareSolverr is available
    if flaresolverr_available:
        config_files.append("providers_cloudflare.json")
        print("Would load Cloudflare-protected providers")

    # Add community providers (loaded last with lowest priority)
    community_dir = config_dir / "community"
    if community_dir.exists():
        community_files = list(community_dir.glob("*.json"))
        if community_files:
            print(f"Found {len(community_files)} community provider files")
            for community_file in sorted(community_files):
                config_files.append(f"community/{community_file.name}")

    # Fallback to old batch files if new structure doesn't exist
    if not (config_dir / "providers_default.json").exists():
        print("Using legacy provider configuration files")
        config_files = [
            "providers_batch1.json",
            "providers_batch2.json",
            "providers_batch3.json",
            "providers_batch4.json",
        ]

    print(f"Config files to load: {config_files}")

    # Collect active providers
    active_providers = {}
    disabled_providers = []
    cloudflare_skipped = []

    for config_filename in config_files:
        config_file = config_dir / config_filename
        if not config_file.exists():
            print(f"Config file not found: {config_file}")
            continue

        print(f"\nProcessing: {config_filename}")
        provider_configs = load_providers_from_file(config_file)

        for config in provider_configs:
            provider_id = config.get("id", "")
            provider_name = config.get("name", provider_id)

            # Check if provider is enabled (default to True if not specified)
            is_enabled = config.get("enabled", True)
            if not is_enabled:
                disabled_providers.append(
                    {
                        "id": provider_id,
                        "name": provider_name,
                        "reason": "explicitly disabled",
                        "source": config_filename,
                    }
                )
                print(f"  DISABLED: {provider_name} - explicitly disabled")
                continue

            # Check if requires FlareSolverr
            requires_flaresolverr = config.get("requires_flaresolverr", False)
            if requires_flaresolverr and not flaresolverr_available:
                cloudflare_skipped.append(
                    {
                        "id": provider_id,
                        "name": provider_name,
                        "reason": "requires FlareSolverr",
                        "source": config_filename,
                    }
                )
                print(f"  SKIPPED: {provider_name} - requires FlareSolverr")
                continue

            # Provider would be loaded
            if provider_id not in active_providers:  # Avoid duplicates
                active_providers[provider_id] = {
                    "id": provider_id,
                    "name": provider_name,
                    "url": config.get("url", ""),
                    "supports_nsfw": config.get("supports_nsfw", False),
                    "class_name": config.get("class_name", "GenericProvider"),
                    "priority": config.get("priority", 999),
                    "requires_flaresolverr": requires_flaresolverr,
                    "source": config_filename,
                }
                print(f"  ACTIVE: {provider_name}")
            else:
                print(
                    f"  DUPLICATE: {provider_name} (already loaded from {active_providers[provider_id]['source']})"
                )

    return active_providers, disabled_providers, cloudflare_skipped


def main():
    """Main function."""
    print("=== Kuroibara Active Provider Analysis ===\n")

    active_providers, disabled_providers, cloudflare_skipped = (
        simulate_provider_loading()
    )

    print(f"\n=== SUMMARY ===")
    print(f"Active providers: {len(active_providers)}")
    print(f"Disabled providers: {len(disabled_providers)}")
    print(f"Cloudflare-skipped providers: {len(cloudflare_skipped)}")
    print(
        f"Total providers in configs: {len(active_providers) + len(disabled_providers) + len(cloudflare_skipped)}"
    )

    print(f"\n=== ACTIVE PROVIDERS ({len(active_providers)}) ===")
    # Sort by priority, then by name
    sorted_active = sorted(
        active_providers.values(), key=lambda x: (x["priority"], x["name"].lower())
    )

    for provider in sorted_active:
        nsfw_flag = " [NSFW]" if provider["supports_nsfw"] else ""
        priority_info = (
            f" (priority: {provider['priority']})"
            if provider["priority"] != 999
            else ""
        )
        print(f"  {provider['name']}{nsfw_flag}{priority_info}")

    if disabled_providers:
        print(f"\n=== DISABLED PROVIDERS ({len(disabled_providers)}) ===")
        for provider in disabled_providers:
            print(f"  {provider['name']} - {provider['reason']}")

    if cloudflare_skipped:
        print(f"\n=== CLOUDFLARE-SKIPPED PROVIDERS ({len(cloudflare_skipped)}) ===")
        for provider in cloudflare_skipped:
            print(f"  {provider['name']} - {provider['reason']}")

    # Integration status breakdown
    print(f"\n=== INTEGRATION STATUS BREAKDOWN ===")
    fully_integrated = sum(
        1
        for p in active_providers.values()
        if p["class_name"] in ["MangaDexProvider", "MangaPlusProvider"]
    )
    enhanced_integrated = sum(
        1
        for p in active_providers.values()
        if p["class_name"] == "EnhancedGenericProvider"
    )
    basic_integrated = sum(
        1 for p in active_providers.values() if p["class_name"] == "GenericProvider"
    )

    print(f"  Fully integrated: {fully_integrated}")
    print(f"  Enhanced integration: {enhanced_integrated}")
    print(f"  Basic integration: {basic_integrated}")

    # NSFW breakdown
    nsfw_count = sum(1 for p in active_providers.values() if p["supports_nsfw"])
    print(f"  NSFW providers: {nsfw_count}")


if __name__ == "__main__":
    main()
