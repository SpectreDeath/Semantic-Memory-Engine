"""
SME Bootstrap - Centralized path management and environment initialization.
"""

import logging
import sys
from pathlib import Path

from src.core.env_validator import validate_environment

# Calculate project root (assumes this file is in src/bootstrap.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def initialize():
    """Add project root to sys.path if not already present."""
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    # Validate environment and log issues (non-blocking)
    env_issues = validate_environment()
    for issue in env_issues:
        logging.warning(f"Environment issue: {issue}")

    return root_str


if __name__ == "__main__":
    print(f"Project Root: {initialize()}")
