"""
SME Bootstrap - Centralized path management and environment initialization.
"""

import os
import sys
from pathlib import Path

# Calculate project root (assumes this file is in src/bootstrap.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def initialize():
    """Add project root to sys.path if not already present."""
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    
    # Optional: Initialize core components like logging or config here
    # from src.core.config import Config
    # config = Config()
    
    return root_str

if __name__ == "__main__":
    print(f"Project Root: {initialize()}")
