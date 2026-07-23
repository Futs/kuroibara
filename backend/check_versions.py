#!/usr/bin/env python3

import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from packaging.version import InvalidVersion, Version

PYPI_URL = "https://pypi.org/pypi/{}/json"


def parse_requirement(line):
    """Parse a requirement line and return (package_name, version)."""
    line = line.strip()

    if not line or line.startswith("#"):
        return None

    # Remove inline comments
    line = line.split("#", 1)[0].strip()

    # Ignore includes and editable installs
    if line.startswith(("-r", "--requirement", "-e", "--editable")):
        return None

    # Package name (remove extras like requests[socks])
    pkg = re.split(r"[<>=!~]", line)[0].strip()
    pkg_name = pkg.split("[")[0]

    # Find version
    match = re.search(r"([0-9][0-9A-Za-z.\-_]*)", line)
    if not match:
        return None

    version = match.group(1)

    return pkg_name, version


def get_versions(package, current_version):
    """Return latest same-major and latest overall versions from PyPI."""
    try:
        response = requests.get(PYPI_URL.format(package), timeout=15)
        response.raise_for_status()

        data = response.json()

        versions = []

        for version in data["releases"]:
            try:
                v = Version(version)
            except InvalidVersion:
                continue

            # Ignore prereleases/dev releases
            if v.is_prerelease or v.is_devrelease:
                continue

            versions.append(v)

        if not versions:
            return package, current_version, "-", "-", "No releases"

        versions.sort()

        current = Version(current_version)

        same_major = [v for v in versions if v.major == current.major]

        latest_minor = same_major[-1] if same_major else current
        latest_major = versions[-1]

        if current == latest_major:
            status = "✓ Latest"
        elif current == latest_minor:
            status = "Major update"
        else:
            status = "Minor update"

        return (
            package,
            str(current),
            str(latest_minor),
            str(latest_major),
            status,
        )

    except Exception as e:
        return (
            package,
            current_version,
            "-",
            "-",
            f"ERROR: {e.__class__.__name__}",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Compare requirements.txt versions against PyPI."
    )

    parser.add_argument(
        "requirements",
        help="Path to requirements.txt",
    )

    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent requests (default: 10)",
    )

    args = parser.parse_args()

    requirements = []

    with open(args.requirements, encoding="utf-8") as f:
        for line in f:
            parsed = parse_requirement(line)
            if parsed:
                requirements.append(parsed)

    print(f"\nChecking {len(requirements)} packages...\n")

    results = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(get_versions, pkg, version)
            for pkg, version in requirements
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
        print(
            f"{package:25}"
            f"{current:15}"
            f"{minor:15}"
            f"{major:15}"
            f"{status}"
        )


if __name__ == "__main__":
    main()