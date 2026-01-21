"""
Backward compatibility shim for monitoring_diagnostics

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.monitoring.diagnostics import *  # noqa: F401, F403
