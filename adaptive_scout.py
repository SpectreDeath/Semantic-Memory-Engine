"""
Backward compatibility shim for adaptive_scout

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.query.scout_integration import Scout  # noqa: F401
from src.query.scout import AdaptiveRetriever  # noqa: F401
