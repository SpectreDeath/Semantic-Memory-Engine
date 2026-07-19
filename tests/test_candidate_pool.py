"""
Unit Tests for CandidatePoolStorage & Dynamic Routing (Phase 3)
================================================================
Tests candidate block persistence, pool retrieval, and dynamic team selection.
"""

from __future__ import annotations

import pytest

from gateway.candidate_pool import CandidatePoolStorage
from gateway.em_cubed_bridge import EmCubedWorkflowBridge


class TestCandidatePoolStorage:
    """Test candidate team pool storage and dynamic team selection."""

    def test_save_and_retrieve_candidate_pool(self):
        storage = CandidatePoolStorage(db_path=":memory:")

        b1 = {"block_id": "block_1", "loss_score": 0.4, "nodes": {"n1": {"prompt": "p1"}}}
        b2 = {"block_id": "block_2", "loss_score": 0.1, "nodes": {"n2": {"prompt": "p2"}}}

        assert storage.save_block(layer_index=0, block=b1)
        assert storage.save_block(layer_index=0, block=b2)

        pool = storage.get_pool(layer_index=0)
        assert len(pool) == 2
        # Lowest loss_score first
        assert pool[0]["block_id"] == "block_2"

    def test_dynamic_routing_select(self):
        storage = CandidatePoolStorage(db_path=":memory:")

        b1 = {"block_id": "team_a", "loss_score": 0.8}
        b2 = {"block_id": "team_b", "loss_score": 0.05}

        storage.save_block(layer_index=1, block=b1)
        storage.save_block(layer_index=1, block=b2)

        optimal = storage.select_optimal_team(layer_index=1)
        assert optimal is not None
        assert optimal["block_id"] == "team_b"

    def test_em_cubed_bridge_integration(self):
        bridge = EmCubedWorkflowBridge()
        specs = [
            {
                "task_id": "t0",
                "skill_id": "python_surface",
                "input_data": {"code": "100"},
            }
        ]

        res = bridge.execute_workflow_dag(workflow_id="cp_test_wf", tasks_spec=specs)
        assert res["status"] == "completed"
        assert res["final_context"]["t0"] == 100
