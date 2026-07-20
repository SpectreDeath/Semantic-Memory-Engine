"""
Unit Tests for GatewayClusterSync
=================================
Tests GatewayClusterSync peer registration, Merkle root sync, candidate broadcasting, and REST API.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gateway.cluster_sync import GatewayClusterSync
from src.api.main import app


class TestGatewayClusterSync:
    """Test GatewayClusterSync cluster synchronization engine."""

    def test_cluster_sync_methods(self):
        sync = GatewayClusterSync(node_id="node_test_01", peers=["http://peer1:8000"])

        assert len(sync.peers) == 1
        sync.register_peer("http://peer2:8000")
        assert len(sync.peers) == 2

        sync_res = sync.sync_merkle_roots()
        assert sync_res["peers_checked"] == 2
        assert "http://peer1:8000" in sync_res["results"]

        b_res = sync.broadcast_candidate_block(
            layer_index=1,
            block={"block_id": "test_block_01", "nodes": {}, "edges": []},
        )
        assert b_res["status"] == "success"
        assert b_res["peers_notified"] == 2

        status = sync.get_cluster_status()
        assert status["local_node_id"] == "node_test_01"
        assert status["total_peers"] == 2

    def test_cluster_sync_rest_endpoint(self):
        client = TestClient(app)

        response = client.post(
            "/api/v1/cluster/sync",
            json={"peers": ["http://node1:8000", "http://node2:8000"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sync_details" in data
        assert "cluster_status" in data
        assert data["cluster_status"]["total_peers"] == 2
