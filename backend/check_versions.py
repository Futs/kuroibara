#!/usr/bin/env python3
import json
import sys
import urllib.request

packages = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "alembic",
    "httpx",
    "redis",
    "pytest",
    "black",
    "isort",
    "flake8",
    "mypy",
    "psycopg2-binary",
    "python-jose",
    "passlib",
    "pillow",
    "beautifulsoup4",
    "python-dotenv",
    "pyyaml",
    "tenacity",
    "structlog",
    "rich",
]


def get_latest_version(package):
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            return data["info"]["version"]
    except Exception as e:
        return f"Error: {str(e)}"


print("Package versions from PyPI:")
print("-" * 40)
for package in packages:
    version = get_latest_version(package)
    print(f"{package}: {version}")
