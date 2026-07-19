"""
Unit Tests for TextualGradientEngine (ANN Textual Backpropagation)
=====================================================================
Tests global loss signal computation, local layerwise textual gradient extraction,
and candidate block (f'_ℓ) generation.
"""

from __future__ import annotations

import pytest

from src.logic.textual_gradient import GlobalGradient, LocalGradient, TextualGradientEngine


class TestTextualGradientEngine:
    """Test global and local textual backpropagation."""

    def test_compute_global_gradient_successful_trajectory(self):
        engine = TextualGradientEngine()
        trajectory = [
            {"task_id": "step_0", "status": "success", "output": {"result": 42}},
            {"task_id": "step_1", "status": "completed", "output": {"result": "done"}},
        ]

        g_global = engine.compute_global_gradient(trajectory)
        assert g_global.loss_score == 0.0
        assert len(g_global.failed_layers) == 0

    def test_compute_global_gradient_failed_trajectory(self):
        engine = TextualGradientEngine()
        trajectory = [
            {"task_id": "step_0", "status": "success"},
            {"task_id": "step_1", "status": "error", "error": "SyntaxError in surface"},
        ]

        g_global = engine.compute_global_gradient(trajectory)
        assert g_global.loss_score == 0.5
        assert g_global.failed_layers == [1]
        assert len(g_global.structural_suggestions) == 1

    def test_compute_local_gradient_and_apply(self):
        engine = TextualGradientEngine()
        g_global = GlobalGradient(loss_score=0.5, failed_layers=[1])

        team_block = {
            "block_id": "review_block_1",
            "nodes": {
                "agent_review": {"agent": "reviewer", "prompt": "Review code carefully."}
            },
            "edges": [["agent_review", "end_node"]],
        }

        g_local = engine.compute_local_gradient(
            layer_index=1,
            team_block=team_block,
            global_gradient=g_global,
            trajectory=[],
        )

        assert g_local.layer_index == 1
        assert g_local.loss_score > 0.0
        assert "agent_review" in g_local.prompt_suggestions

        updated_block = engine.apply_textual_gradient(team_block, g_local)
        assert updated_block["block_id"] != team_block["block_id"]
        assert "agent_review_validator" in updated_block["nodes"]
        assert "Optimization" in updated_block["nodes"]["agent_review"]["prompt"]
