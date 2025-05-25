# version.py

"""
HelixLang Version Information

- Stores semantic versioning (major.minor.patch).
- Optionally integrates build metadata: release channel, date, commit hash.
- Provides CLI access to version with `--version`.
- Can compare versions for compatibility checks.
"""

import os
import platform
import datetime
from typing import Tuple, Optional


# -------------------------------
# Core Semantic Version Info
# -------------------------------

MAJOR = 1
MINOR = 4
PATCH = 2
RELEASE_CHANNEL = "stable"  # Options: dev, beta, rc, stable

# Format: "1.4.2-stable"
VERSION_STRING = f"{MAJOR}.{MINOR}.{PATCH}-{RELEASE_CHANNEL}"


# -------------------------------
# Build Metadata
# -------------------------------

# Fetched from environment variable or fallback to unknown
BUILD_DATE = os.getenv("HELIXLANG_BUILD_DATE", datetime.datetime.utcnow().strftime("%Y-%m-%d"))
COMMIT_HASH = os.getenv("HELIXLANG_COMMIT_HASH", "unknown")
PYTHON_VERSION = platform.python_version()


# -------------------------------
# Functions for Runtime Access
# -------------------------------

def get_version() -> str:
    return VERSION_STRING

def get_version_tuple() -> Tuple[int, int, int]:
    return (MAJOR, MINOR, PATCH)

def get_metadata() -> dict:
    return {
        "version": VERSION_STRING,
        "commit_hash": COMMIT_HASH,
        "build_date": BUILD_DATE,
        "python_version": PYTHON_VERSION,
        "release_channel": RELEASE_CHANNEL
    }

def is_compatible(min_version: Tuple[int, int, int]) -> bool:
    """
    Check if the current version is >= `min_version`.
    """
    return get_version_tuple() >= min_version


# -------------------------------
# CLI Support
# -------------------------------

def print_version_info():
    """
    Print full version information to console.
    Useful for --version flag.
    """
    print(f"HelixLang {get_version()}")
    print(f"Build date: {BUILD_DATE}")
    print(f"Commit hash: {COMMIT_HASH}")
    print(f"Python version: {PYTHON_VERSION}")
    print(f"Channel: {RELEASE_CHANNEL}")


# -------------------------------
# Example Usage / CLI Entry
# -------------------------------

if __name__ == "__main__":
    import sys
    if "--version" in sys.argv or "-v" in sys.argv:
        print_version_info()
    else:
        print("Run with --version to see HelixLang version info.")
