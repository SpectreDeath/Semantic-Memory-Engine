"""
SME Core Bridge - Composition Bridge
====================================
Unified composition bridge for tool and extension execution, inheriting from
SessionBridge, NexusDatabaseBridge, SemanticGraphBridge, and SurfaceBridge.
"""

from __future__ import annotations

from gateway.bridges.nexus_database import NexusDatabaseBridge
from gateway.bridges.semantic_graph import SemanticGraphBridge
from gateway.bridges.session import SessionBridge
from gateway.bridges.surface import SurfaceBridge


class SmeCoreBridge(SessionBridge, NexusDatabaseBridge, SemanticGraphBridge, SurfaceBridge):
    """
    Composes SessionBridge, NexusDatabaseBridge, SemanticGraphBridge, and SurfaceBridge.

    Implements NexusAPI for extensions while decoupling individual functional areas.
    """

    def __init__(self, session_id: str | None = None) -> None:
        SessionBridge.__init__(self, session_id=session_id)
        NexusDatabaseBridge.__init__(self)
        SurfaceBridge.__init__(self)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_nexus"] = None
        return state
