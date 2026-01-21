"""
Backward compatibility shim for pipeline_orchestrator

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.orchestration.orchestrator import *  # noqa: F401, F403
