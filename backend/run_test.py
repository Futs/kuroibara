#!/usr/bin/env python3
"""
Run tests and capture output
"""
import subprocess
import sys


def run_tests():
    """Run a simple test to check if our configuration works."""
    try:
        # Run a single test first
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_api.py::test_api_docs",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Test timed out")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
