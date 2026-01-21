"""
Backward compatibility shim for harvester_spider

This module re-exports from the new location for existing code
that depends on the old import path.
"""

from src.harvester.spider import *  # noqa: F401, F403
