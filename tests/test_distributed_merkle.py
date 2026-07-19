"""
Unit Tests for Pillar 4: Distributed Merkle Consensus & Audit Verification
==========================================================================
Tests AuditEngine Merkle root computation, consensus verification, and REST endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.logic.audit_engine import AuditEngine


class TestDistributedMerkleConsensus:
    """Test distributed Merkle tree root consensus and audit endpoints."""

    def test_compute_and_verify_merkle_root(self):
        engine = AuditEngine()
        root_initial = engine.compute_merkle_root()

        engine.log_event("test_event", actor="unit_test", payload={"key": "val"})
        root_after = engine.compute_merkle_root()

        assert root_after != root_initial

        res_same = engine.verify_remote_merkle_root(root_after)
        assert res_same["consensus"] is True

        res_different = engine.verify_remote_merkle_root("tampered_hash_root")
        assert res_different["consensus"] is False

    def test_merkle_root_rest_endpoints(self):
        client = TestClient(app)

        res_root = client.get("/api/v1/audit/merkle-root")
        assert res_root.status_code == 200
        data_root = res_root.json()
        assert "merkle_root" in data_root

        root = data_root["merkle_root"]
        res_verify = client.get(f"/api/v1/audit/verify?remote_root={root}")
        assert res_verify.status_code == 200
        data_verify = res_verify.json()
        assert data_verify["consensus"] is True
