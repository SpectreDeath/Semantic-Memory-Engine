"""
MomentumBuffer & Multi-Stage Validation Filter
===============================================
Implements momentum-smoothed textual gradient refinement and a 4-stage
validation filter (Node, Edge, Structure, Performance) for Agentic Neural Networks (ANN).
"""

from __future__ import annotations

import logging
from typing import Any

from src.logic.textual_gradient import LocalGradient

logger = logging.getLogger("lawnmower.momentum_buffer")


class MomentumBuffer:
    """
    Maintains update velocity history across iterations to smooth textual gradients.
    """

    def __init__(self, alpha: float = 0.7) -> None:
        self.alpha = alpha
        self._history: dict[int, list[LocalGradient]] = {}

    def apply_momentum(
        self, layer_index: int, current_gradient: LocalGradient
    ) -> LocalGradient:
        """
        Apply momentum smoothing: G'_local,ℓ = α G_local,ℓ + (1-α) G^{t-1}_local,ℓ.
        """
        history = self._history.setdefault(layer_index, [])

        if not history:
            history.append(current_gradient)
            return current_gradient

        prev = history[-1]
        smoothed_loss = round(
            self.alpha * current_gradient.loss_score + (1.0 - self.alpha) * prev.loss_score,
            4,
        )

        merged_prompts = {**prev.prompt_suggestions, **current_gradient.prompt_suggestions}

        smoothed_gradient = LocalGradient(
            layer_index=layer_index,
            loss_score=smoothed_loss,
            prompt_suggestions=merged_prompts,
            node_updates=current_gradient.node_updates or prev.node_updates,
            edge_updates=current_gradient.edge_updates or prev.edge_updates,
        )

        history.append(smoothed_gradient)
        logger.info(
            f"MomentumBuffer: Smoothed G_local for layer {layer_index} (loss: {prev.loss_score} -> {smoothed_loss})"
        )
        return smoothed_gradient


class MultiStageValidationFilter:
    """
    4-stage validation pipeline for candidate agent team blocks.
    """

    def validate_candidate_block(
        self,
        candidate_block: dict[str, Any],
        existing_pool: list[dict[str, Any]] | None = None,
        baseline_performance: float = 1.0,
    ) -> dict[str, Any]:
        """
        Validate candidate block across 4 stages.
        """
        pool = existing_pool or []

        node_valid, node_msg = self._validate_nodes(candidate_block)
        if not node_valid:
            return {"is_valid": False, "failed_stage": "node", "reason": node_msg}

        edge_valid, edge_msg = self._validate_edges(candidate_block)
        if not edge_valid:
            return {"is_valid": False, "failed_stage": "edge", "reason": edge_msg}

        struct_valid, struct_msg = self._validate_structure(candidate_block, pool)
        if not struct_valid:
            return {"is_valid": False, "failed_stage": "structure", "reason": struct_msg}

        perf_valid, perf_msg = self._validate_performance(candidate_block, baseline_performance)
        if not perf_valid:
            return {"is_valid": False, "failed_stage": "performance", "reason": perf_msg}

        return {"is_valid": True, "failed_stage": None, "reason": "Passed all validation checks"}

    def _validate_nodes(self, block: dict[str, Any]) -> tuple[bool, str]:
        nodes = block.get("nodes")
        if not nodes or not isinstance(nodes, dict):
            return False, "Node validation failed: 'nodes' must be a non-empty dict"

        for node_id, node_info in nodes.items():
            if not isinstance(node_info, dict):
                return False, f"Node validation failed: node '{node_id}' is not a dict"
            if "prompt" not in node_info or not node_info["prompt"].strip():
                return False, f"Node validation failed: node '{node_id}' missing prompt"

        return True, "Node validation passed"

    def _validate_edges(self, block: dict[str, Any]) -> tuple[bool, str]:
        nodes = set(block.get("nodes", {}).keys())
        edges = block.get("edges", [])

        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                return False, f"Edge validation failed: malformed edge {edge}"
            src = edge[0]
            if src not in nodes and src != "entry_point":
                return False, f"Edge validation failed: source node '{src}' not defined in nodes"

        return True, "Edge validation passed"

    def _validate_structure(
        self, block: dict[str, Any], pool: list[dict[str, Any]]
    ) -> tuple[bool, str]:
        block_id = block.get("block_id")
        for existing in pool:
            if existing.get("block_id") == block_id:
                return False, f"Structure validation failed: duplicate block_id '{block_id}'"

        return True, "Structure validation passed"

    def _validate_performance(
        self, block: dict[str, Any], baseline_performance: float
    ) -> tuple[bool, str]:
        loss_score = block.get("loss_score", 0.0)
        if loss_score > baseline_performance:
            return False, f"Performance validation failed: loss score ({loss_score}) higher than baseline ({baseline_performance})"

        return True, "Performance validation passed"
