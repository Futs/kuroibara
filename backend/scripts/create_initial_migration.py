#!/usr/bin/env python3
"""
Script to create the initial database migration.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def main() -> None:
    """Create the initial database migration."""
    # Change to the backend directory
    os.chdir(Path(__file__).parent.parent)
    
    # Create the initial migration
    subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "Initial migration"],
        check=True,
    )
    
    print("Initial migration created successfully.")


if __name__ == "__main__":
    main()
