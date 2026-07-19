"""
Unit Tests for Cryptographic Merkle Tree Audit Engine
======================================================
Tests claim drift analysis, Merkle hash chaining, integrity verification, and tamper detection.
"""

from __future__ import annotations

import pytest

from src.logic.audit_engine import AuditEngine


class TestAuditEngineDriftAnalysis:
    """Test claim drift analysis."""

    def test_drift_analysis_missing_file_returns_anomalies(self):
        engine = AuditEngine(h5_path="non_existent_file.h5")
        claims = [{"subject": "A", "predicate": "is", "object": "B"}]

        res = engine.analyze_drift(claims)
        assert res["drift_score"] == 1.0
        assert len(res["anomalies"]) == 1


class TestMerkleAuditTrail:
    """Test cryptographic Merkle tree audit logging."""

    def test_log_event_creates_hash_chain(self):
        engine = AuditEngine()

        e1 = engine.log_event(
            event_type="TOOL_CALL", actor="operator", payload={"tool": "verify_system"}
        )
        e2 = engine.log_event(
            event_type="SURFACE_EXEC", actor="surface_bridge", payload={"code": "2+2"}
        )

        assert e1["index"] == 0
        assert e2["index"] == 1
        assert e2["prev_hash"] == e1["hash"]

    def test_verify_integrity_valid_chain(self):
        engine = AuditEngine()

        engine.log_event(event_type="INGEST", actor="crawler", payload={"url": "https://sme.local"})
        engine.log_event(
            event_type="QUERY", actor="user", payload={"query": "find connections"}
        )

        status = engine.verify_integrity()
        assert status["valid"] is True
        assert status["total_events"] == 2
        assert status["merkle_root"] != "0" * 64

    def test_verify_integrity_detects_tampering(self):
        engine = AuditEngine()

        engine.log_event(event_type="AUTH", actor="user1", payload={"action": "login"})
        engine.log_event(
            event_type="DELETE", actor="admin", payload={"target": "record_123"}
        )

        assert engine.verify_integrity()["valid"] is True

        # Tamper with event payload in history
        engine.audit_records[0].payload["action"] = "unauthorized_escalation"

        # Integrity check should fail
        status = engine.verify_integrity()
        assert status["valid"] is False
        assert status["corrupted_index"] == 0
        assert "Tampered" in status["reason"]
