"""
Backward compatibility shim for data_processor

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.core.processor import *  # noqa: F401, F403
