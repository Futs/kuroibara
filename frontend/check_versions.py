#!/usr/bin/env python3

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from packaging.version import InvalidVersion, Version

REGISTRY_URL = "https://registry.npmjs.org/{}"


def parse_npm_version(version_str):
    """Remove ^, ~, >, <, etc. from npm version strings."""
    if not version_str:
        return ""
    # Remove common npm version decorators
    return re.sub(r"^[\^~><=]+", "", version_str).strip()


def get_versions(package, current_version_str):
    """Return latest same-major and latest overall versions from npm registry."""
    try:
        response = requests.get(REGISTRY_URL.format(package), timeout=15)
        response.raise_for_status()
        data = response.json()

        versions_data = data.get("versions", {})
        if not versions_data:
            return package, current_version_str, "-", "-", "No releases"

        stable_versions = []
        for v_str in versions_data.keys():
            try:
                v = Version(v_str)
                if not v.is_prerelease and not v.is_devrelease:
                    stable_versions.append(v)
            except InvalidVersion:
                continue

        if not stable_versions:
            return package, current_version_str, "-", "-", "No stable releases"

        stable_versions.sort()

        try:
            current_v_obj = Version(parse_npm_version(current_version_str))
        except InvalidVersion:
            return (
                package,
                current_version_str,
                "-",
                "-",
                "ERROR: Invalid current version",
            )

        # Latest Minor: highest version with same major as current
        same_major = [v for v in stable_versions if v.major == current_v_obj.major]
        latest_minor = same_major[-1] if same_major else current_v_obj

        # Latest Major: highest version overall
        latest_major = stable_versions[-1]

        if current_v_obj == latest_major:
            status = "✓ Latest"
        elif current_v_obj == latest_minor:
            status = "Major update"
        else:
            status = "Minor update"

        return (
            package,
            current_version_str,
            str(latest_minor),
            str(latest_major),
            status,
        )

    except Exception as e:
        return (
            package,
            current_version_str,
            "-",
            "-",
            f"ERROR: {e.__class__.__name__}",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare frontend package versions against npm registry."
    )
    parser.add_argument(
        "package_json",
        help="Path to package.json",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)",
    )

    args = parser.parse_args()

    dependencies = {}
    try:
        with open(args.package_json, encoding="utf-8") as f:
            data = json.load(f)
            dependencies.update(data.get("dependencies", {}))
            dependencies.update(data.get("devDependencies", {}))
    except Exception as e:
        print(f"Error reading {args.package_json}: {e}")
        return

    print(f"\nChecking {len(dependencies)} packages...\n")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(get_versions, pkg, ver) for pkg, ver in dependencies.items()
        ]

        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: x[0].lower())

    print(
        f"{'Package':25}"
        f"{'Current':15}"
        f"{'Latest Minor':15}"
        f"{'Latest Major':15}"
        f"Status"
    )

    print("-" * 90)

    for package, current, minor, major, status in results:
        print(f"{package:25}" f"{current:15}" f"{minor:15}" f"{major:15}" f"{status}")


if __name__ == "__main__":
    main()
