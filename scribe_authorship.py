"""
Backward compatibility shim for scribe_authorship

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.scribe.engine import *  # noqa: F401, F403
