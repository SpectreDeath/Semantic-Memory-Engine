"""
Unit tests for gateway.bridges package
========================================
Validates that SessionBridge, SemanticGraphBridge, NexusDatabaseBridge, SurfaceBridge,
and SmeCoreBridge function correctly when imported from gateway.bridges.
"""

from __future__ import annotations

import pytest

from gateway.bridges import (
    NexusDatabaseBridge,
    SemanticGraphBridge,
    SessionBridge,
    SmeCoreBridge,
    SurfaceBridge,
)


def test_bridge_imports():
    """Verify that all bridges are importable from gateway.bridges package."""
    assert SessionBridge is not None
    assert SemanticGraphBridge is not None
    assert NexusDatabaseBridge is not None
    assert SurfaceBridge is not None
    assert SmeCoreBridge is not None


def test_session_bridge_instantiation():
    """Verify SessionBridge behavior without session_id."""
    sb = SessionBridge()
    assert sb.session_id is None
    assert sb.get_session_entry("key") is None
    assert sb.get_session() is None

    sb2 = SessionBridge(session_id="dummy_session_123")
    assert sb2.session_id == "dummy_session_123"


def test_semantic_graph_bridge_triples():
    """Verify SemanticGraphBridge.get_ego_triples fallback."""
    triples = SemanticGraphBridge.get_ego_triples("NonExistentEntity123")
    assert isinstance(triples, list)
    assert len(triples) > 0


def test_nexus_database_bridge_instantiation():
    """Verify NexusDatabaseBridge instantiation."""
    db = NexusDatabaseBridge()
    assert db._nexus is None


def test_sme_core_bridge_composition():
    """Verify SmeCoreBridge inherits from all four component bridges."""
    core = SmeCoreBridge(session_id="test_session")
    assert isinstance(core, SessionBridge)
    assert isinstance(core, NexusDatabaseBridge)
    assert isinstance(core, SemanticGraphBridge)
    assert isinstance(core, SurfaceBridge)
    assert core.session_id == "test_session"
