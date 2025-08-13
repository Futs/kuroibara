#!/usr/bin/env python3
"""
Generate Individual Provider Test Scripts
Creates a separate test script for each provider based on the template.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append("/app")
sys.path.append("/app/backend")


def generate_provider_tests():
    """Generate individual test scripts for each provider."""

    # Provider list (from the registry output)
    providers = [
        "AllPornComic",
        "AnshScans",
        "ArcaneScans",
        "DynastyScans",
        "FreeManga",
        "HentaiNexus",
        "HentaiRead",
        "HentaiWebtoon",
        "Manga18FX",
        "MangaDNA",
        "MangaDex",
        "MangaFire",
        "MangaFoxFull",
        "MangaFreak",
        "MangaGG",
        "MangaHere",
        "MangaHub",
        "MangaKakalotFun",
        "MangaPill",
        "MangaReaderTo",
        "MangaSail",
        "MangaTown",
        "ManhuaFast",
        "Manhuaga",
        "NovelCool",
        "OmegaScans",
        "ReadAllComics",
        "ReaperScans",
        "TAADD",
        "Toonily",
        "Tsumino",
        "WuxiaWorld",
    ]

    # Priority providers (test these first)
    priority_providers = [
        "MangaDex",
        "MangaHub",
        "ManhuaFast",
        "MangaKakalotFun",
        "MangaDNA",
        "FreeManga",
        "OmegaScans",
        "MangaSail",
        "Toonily",
    ]

    # Read the template
    template_path = Path(__file__).parent / "test_provider_template.py"
    with open(template_path, "r") as f:
        template_content = f.read()

    # Create individual provider tests directory
    individual_tests_dir = Path(__file__).parent / "individual_provider_tests"
    individual_tests_dir.mkdir(exist_ok=True)

    print(f"🔧 Generating individual provider test scripts...")
    print(f"📁 Output directory: {individual_tests_dir}")
    print(f"📊 Total providers: {len(providers)}")
    print()

    # Generate scripts for each provider
    for i, provider in enumerate(providers, 1):
        # Replace the template placeholder with actual provider name
        provider_content = template_content.replace("TEMPLATE_PROVIDER_NAME", provider)

        # Create filename (lowercase with underscores)
        filename = f"test_{provider.lower()}.py"
        filepath = individual_tests_dir / filename

        # Write the file
        with open(filepath, "w") as f:
            f.write(provider_content)

        # Make it executable
        os.chmod(filepath, 0o755)

        # Show progress
        priority_marker = " ⭐" if provider in priority_providers else ""
        print(f"[{i:2d}/{len(providers)}] Created: {filename}{priority_marker}")

    # Create a README for the individual tests
    readme_content = f"""# Individual Provider Tests

This directory contains individual test scripts for each of the {len(providers)} manga providers.

## Usage

Run any individual provider test:
```bash
# From the main kuroibara directory
docker compose -f docker-compose.dev.yml exec backend python scripts/individual_provider_tests/test_<provider_name>.py

# Examples:
docker compose -f docker-compose.dev.yml exec backend python scripts/individual_provider_tests/test_mangadex.py
docker compose -f docker-compose.dev.yml exec backend python scripts/individual_provider_tests/test_manhuafast.py
docker compose -f docker-compose.dev.yml exec backend python scripts/individual_provider_tests/test_mangakakalotfun.py
```

## Priority Providers ⭐

These providers should be tested first as they show the most promise:

{chr(10).join(f"- test_{provider.lower()}.py" for provider in priority_providers)}

## Test Output

Each test provides detailed output including:
- Search functionality testing
- Manga details retrieval
- Chapter listing
- Page extraction (download capability)
- Detailed error messages and debugging info
- Overall status (Fully Working / Partially Working / Not Working)

## Generated Files

This directory contains {len(providers)} test scripts:

{chr(10).join(f"- test_{provider.lower()}.py" for provider in sorted(providers))}

## Maintenance

These scripts are auto-generated from `test_provider_template.py`. 
To regenerate all scripts, run:
```bash
docker compose -f docker-compose.dev.yml exec backend python scripts/generate_individual_provider_tests.py
```
"""

    readme_path = individual_tests_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    print()
    print("✅ Generation complete!")
    print(f"📁 Created {len(providers)} individual test scripts")
    print(f"📄 Created README.md with usage instructions")
    print()
    print("🎯 Priority providers to test first:")
    for provider in priority_providers:
        print(f"   - test_{provider.lower()}.py")
    print()
    print("🚀 Example usage:")
    print(
        "   docker compose -f docker-compose.dev.yml exec backend python scripts/individual_provider_tests/test_mangadex.py"
    )


if __name__ == "__main__":
    generate_provider_tests()
