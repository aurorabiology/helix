# helixlang/cli/__init__.py

"""
HelixLang Command-Line Interface Package

This package contains the CLI entry points, interactive shell,
and script execution modules for HelixLang.

It may also handle initialization such as setting environment
variables or configuring CLI-specific logging.
"""

import logging
import os

# Example: configure a logger for CLI usage
logger = logging.getLogger("helixlang.cli")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Optional: Set an environment variable to indicate CLI mode
os.environ.setdefault("HELIXLANG_CLI_ACTIVE", "1")
