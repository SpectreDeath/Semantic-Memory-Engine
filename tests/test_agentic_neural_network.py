"""
E2E Integration Test Suite for Agentic Neural Network (ANN) Framework
=======================================================================
Tests the complete closed-loop optimization and inference pipeline:
1. Trajectory execution & recording (AuditEngine)
2. Global & local textual backpropagation (TextualGradientEngine)
3. Momentum smoothing & multi-stage validation (MomentumBuffer & MultiStageValidationFilter)
4. Candidate pool persistence (CandidatePoolStorage)
5. Forward-only dynamic team selection & inference (TrafficRouter & EmCubedWorkflowBridge)
"""

from __future__ import annotations

import pytest

from gateway.candidate_pool import CandidatePoolStorage
from gateway.em_cubed_bridge import EmCubedWorkflowBridge
from gateway.momentum_buffer import MomentumBuffer, MultiStageValidationFilter
from gateway.traffic_router import RULE_EM_CUBED_WORKFLOW, TrafficRouter
from src.logic.audit_engine import AuditEngine
from src.logic.textual_gradient import TextualGradientEngine


class TestAgenticNeuralNetworkE2E:
    """Complete end-to-end integration test for the ANN framework."""

    def test_full_ann_training_and_inference_loop(self, tmp_path):
        db_file = str(tmp_path / "test_ann.db")

        # 1. Forward Execution Failure Trajectory Simulation
        trajectory = [
            {
                "task_id": "step_0",
                "skill_id": "python_surface",
                "status": "success",
                "output": {"result": "Extracted text payload"},
            },
            {
                "task_id": "step_1",
                "skill_id": "graph_transform",
                "status": "error",
                "error": "KeyError: 'triplet' mapping missing in step_1 input",
            },
        ]

        # Log trajectory to AuditEngine
        audit = AuditEngine()
        for step in trajectory:
            audit.log_event(
                event_type="ann_step_execution",
                actor="test_runner",
                payload=step,
            )

        assert audit.verify_integrity()

        # 2. Backward Pass: Compute Textual Gradients
        engine = TextualGradientEngine()
        g_global = engine.compute_global_gradient(trajectory, target_objective="graph_synthesis")
        assert g_global.loss_score == 0.5
        assert g_global.failed_layers == [1]

        initial_block = {
            "block_id": "layer1_block_init",
            "nodes": {
                "agent_transform": {
                    "agent": "graph_transformer",
                    "prompt": "Transform input text to semantic graph.",
                }
            },
            "edges": [["entry_point", "agent_transform"]],
        }

        g_local = engine.compute_local_gradient(
            layer_index=1,
            team_block=initial_block,
            global_gradient=g_global,
            trajectory=trajectory,
        )

        candidate_block = engine.apply_textual_gradient(initial_block, g_local)

        # 3. Momentum Velocity Smoothing & Multi-Stage Validation
        buffer = MomentumBuffer(alpha=0.7)
        smoothed_g_local = buffer.apply_momentum(layer_index=1, current_gradient=g_local)
        assert smoothed_g_local.loss_score == 0.75

        validator = MultiStageValidationFilter()
        val_res = validator.validate_candidate_block(
            candidate_block, baseline_performance=1.0
        )
        assert val_res["is_valid"]

        # 4. Candidate Pool Storage Persistence
        pool_storage = CandidatePoolStorage(db_path=db_file)
        assert pool_storage.save_block(layer_index=1, block=candidate_block)

        pool = pool_storage.get_pool(layer_index=1)
        assert len(pool) == 1
        assert pool[0]["block_id"] == candidate_block["block_id"]

        # 5. Forward-Only Inference: Dynamic Routing & Execution
        optimal_team = pool_storage.select_optimal_team(layer_index=1)
        assert optimal_team is not None
        assert "agent_transform" in optimal_team["nodes"]

        router = TrafficRouter()
        inference_specs = [
            {
                "task_id": "inf_step_0",
                "skill_id": "python_surface",
                "input_data": {"code": "'ann_inference_success'"},
            }
        ]

        infer_res = router.dispatch_workload(
            tool_name="execute_distributed_workflow",
            payload={"workflow_id": "ann_inf_wf", "tasks_spec": inference_specs},
            mode=RULE_EM_CUBED_WORKFLOW,
        )

        assert infer_res["status"] == "completed"
        assert infer_res["final_context"]["inf_step_0"] == "ann_inference_success"
