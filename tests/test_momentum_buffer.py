"""
Unit Tests for MomentumBuffer & MultiStageValidationFilter (Phase 2)
======================================================================
Tests momentum-smoothed textual gradient refinement and 4-stage validation checks.
"""

from __future__ import annotations

import pytest

from gateway.momentum_buffer import MomentumBuffer, MultiStageValidationFilter
from src.logic.textual_gradient import LocalGradient


class TestMomentumBufferAndValidation:
    """Test MomentumBuffer and MultiStageValidationFilter."""

    def test_momentum_buffer_smoothing(self):
        buffer = MomentumBuffer(alpha=0.7)

        g0 = LocalGradient(
            layer_index=1,
            loss_score=1.0,
            prompt_suggestions={"n1": "prompt_0"},
        )
        res0 = buffer.apply_momentum(layer_index=1, current_gradient=g0)
        assert res0.loss_score == 1.0

        g1 = LocalGradient(
            layer_index=1,
            loss_score=0.0,
            prompt_suggestions={"n1": "prompt_1"},
        )
        res1 = buffer.apply_momentum(layer_index=1, current_gradient=g1)

        # 0.7 * 0.0 + 0.3 * 1.0 = 0.3
        assert res1.loss_score == 0.3

    def test_validation_filter_node_failure(self):
        val = MultiStageValidationFilter()
        invalid_block = {
            "block_id": "b1",
            "nodes": {"n1": {"prompt": ""}},  # Empty prompt
        }
        res = val.validate_candidate_block(invalid_block)

        assert not res["is_valid"]
        assert res["failed_stage"] == "node"

    def test_validation_filter_edge_failure(self):
        val = MultiStageValidationFilter()
        invalid_block = {
            "block_id": "b1",
            "nodes": {"n1": {"prompt": "Valid prompt"}},
            "edges": [["undefined_node", "n1"]],
        }
        res = val.validate_candidate_block(invalid_block)

        assert not res["is_valid"]
        assert res["failed_stage"] == "edge"

    def test_validation_filter_duplicate_structure(self):
        val = MultiStageValidationFilter()
        block = {
            "block_id": "dup_block",
            "nodes": {"n1": {"prompt": "Valid prompt"}},
            "edges": [],
        }
        pool = [{"block_id": "dup_block"}]

        res = val.validate_candidate_block(block, existing_pool=pool)

        assert not res["is_valid"]
        assert res["failed_stage"] == "structure"

    def test_validation_filter_success(self):
        val = MultiStageValidationFilter()
        block = {
            "block_id": "valid_block",
            "nodes": {"n1": {"prompt": "Valid prompt"}},
            "edges": [["n1", "n1"]],
            "loss_score": 0.2,
        }

        res = val.validate_candidate_block(block, baseline_performance=0.5)

        assert res["is_valid"]
        assert res["failed_stage"] is None
