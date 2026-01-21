"""
Backward compatibility shim for semantic_loom

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.core.loom import *  # noqa: F401, F403
