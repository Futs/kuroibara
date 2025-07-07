#!/usr/bin/env python3
"""
Script to run database migrations.
"""
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def main() -> None:
    """Run database migrations."""
    # Change to the backend directory
    os.chdir(Path(__file__).parent.parent)

    # Run the migrations
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
    )

    print("Migrations completed successfully.")


if __name__ == "__main__":
    main()
