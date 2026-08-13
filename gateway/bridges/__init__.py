"""
Gateway Bridges Package
========================
Modular component bridges for Lawnmower Gateway / SME.
"""

from __future__ import annotations

from gateway.bridges.core import SmeCoreBridge
from gateway.bridges.nexus_database import NexusDatabaseBridge
from gateway.bridges.semantic_graph import SemanticGraphBridge
from gateway.bridges.session import SessionBridge
from gateway.bridges.surface import SurfaceBridge

__all__ = [
    "SessionBridge",
    "SemanticGraphBridge",
    "NexusDatabaseBridge",
    "SurfaceBridge",
    "SmeCoreBridge",
]
