#!/usr/bin/env python3

# Simple test to verify sorting logic
providers = [
    {"name": "ZZZ Provider"},
    {"name": "AAA Provider"},
    {"name": "MangaDex"},
    {"name": "Banana Provider"},
    {"name": "Apple Provider"},
]

print("Original order:")
for p in providers:
    print(f"- {p['name']}")

print("\nSorted order:")
sorted_providers = sorted(providers, key=lambda p: p['name'].lower())
for p in sorted_providers:
    print(f"- {p['name']}")

print("\nSorted names only:")
names = [p['name'] for p in providers]
sorted_names = sorted(names)
for name in sorted_names:
    print(f"- {name}")
