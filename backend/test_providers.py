#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'postgresql://user:password@localhost/db')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')

from app.core.providers.registry import provider_registry

def main():
    print("Testing Provider Registry...")
    print(f"Number of providers: {len(provider_registry.get_all_providers())}")
    print(f"Provider names: {provider_registry.get_provider_names()}")

    print("\nProvider info objects:")
    provider_info = provider_registry.get_provider_info()
    print(f"Number of provider info objects: {len(provider_info)}")

    print("\nFirst 10 provider info objects (should be alphabetically sorted):")
    for info in provider_info[:10]:
        print(f"- ID: {info['id']}, Name: {info['name']}, URL: {info['url']}, NSFW: {info['supports_nsfw']}")

    print("\nProvider names (should be alphabetically sorted):")
    provider_names = provider_registry.get_provider_names()
    for name in provider_names[:10]:
        print(f"- {name}")

    print("\nLast 5 provider names:")
    for name in provider_names[-5:]:
        print(f"- {name}")

if __name__ == "__main__":
    main()
