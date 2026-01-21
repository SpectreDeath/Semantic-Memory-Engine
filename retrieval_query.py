"""
Backward compatibility shim for retrieval_query

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.query.engine import *  # noqa: F401, F403
from src.query.verifier import FactVerifier  # noqa: F401
