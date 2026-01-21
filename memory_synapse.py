"""
Backward compatibility shim for memory_synapse

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.synapse.synapse import *  # noqa: F401, F403
