#!/usr/bin/env python3
"""
Simple script to create test database for PostgreSQL testing.
Run this before running tests.
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        print(f"✅ {description} successful")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            print(f"✅ {description} (already exists)")
            return True
        else:
            print(f"❌ {description} failed: {e.stderr.strip()}")
            return False


def main():
    """Create test database using Docker."""
    # Check if docker container is running
    check_cmd = "docker ps | grep kuroibara-postgres"
    if not run_command(check_cmd, "Checking if PostgreSQL container is running"):
        print("❌ PostgreSQL container is not running. Please run './dev.sh' first.")
        sys.exit(1)

    # Create test database
    create_db_cmd = 'docker exec kuroibara-postgres-1 psql -U kuroibara -d postgres -c "CREATE DATABASE test_kuroibara;"'
    run_command(create_db_cmd, "Creating test database")

    print("\n✅ Test database setup complete!")
    print("You can now run tests with: pytest")


if __name__ == "__main__":
    main()
