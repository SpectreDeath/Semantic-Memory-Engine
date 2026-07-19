"""
TextualGradientEngine - Agentic Neural Network (ANN) Textual Backpropagation
=============================================================================
Implements global and local textual gradients (∇text) for multi-agent workflows,
mirroring backpropagation in neural networks to optimize prompts, agent roles,
and edge topologies.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("lawnmower.textual_gradient")


@dataclass
class GlobalGradient:
    """Represents global loss feedback and inter-layer structural updates."""

    loss_score: float
    failed_layers: list[int] = field(default_factory=list)
    structural_suggestions: list[str] = field(default_factory=list)
    inter_layer_flow_updates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "loss_score": self.loss_score,
            "failed_layers": self.failed_layers,
            "structural_suggestions": self.structural_suggestions,
            "inter_layer_flow_updates": self.inter_layer_flow_updates,
        }


@dataclass
class LocalGradient:
    """Represents local layerwise node, edge, and prompt updates."""

    layer_index: int
    loss_score: float
    prompt_suggestions: dict[str, str] = field(default_factory=dict)
    node_updates: list[dict[str, Any]] = field(default_factory=list)
    edge_updates: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer_index": self.layer_index,
            "loss_score": self.loss_score,
            "prompt_suggestions": self.prompt_suggestions,
            "node_updates": self.node_updates,
            "edge_updates": self.edge_updates,
        }


class TextualGradientEngine:
    """
    Computes global and local textual gradients from execution trajectories.
    """

    def compute_global_gradient(
        self, trajectory: list[dict[str, Any]], target_objective: str = "execution_success"
    ) -> GlobalGradient:
        """
        Analyze multi-step execution trajectory to compute global loss signal (G_global).
        """
        if not trajectory:
            return GlobalGradient(loss_score=0.0)

        total_steps = len(trajectory)
        failed_layers: list[int] = []
        suggestions: list[str] = []
        flow_updates: list[str] = []

        for idx, step in enumerate(trajectory):
            status = step.get("status") or step.get("output", {}).get("status")
            error = step.get("error") or step.get("output", {}).get("error")

            if status in ("error", "failed") or error:
                failed_layers.append(idx)
                suggestions.append(f"Layer {idx} failed during step '{step.get('task_id', idx)}': {error}")
                flow_updates.append(f"Rewire layer {idx} inputs to isolate failure in '{step.get('skill_id')}'")

        loss_score = len(failed_layers) / total_steps if total_steps > 0 else 0.0

        if loss_score == 0.0 and target_objective != "execution_success":
            suggestions.append("Execution succeeded; optimize for concise prompt templates.")

        logger.info(
            f"TextualGradientEngine: Computed G_global (loss: {round(loss_score, 2)}, failed layers: {failed_layers})"
        )

        return GlobalGradient(
            loss_score=round(loss_score, 4),
            failed_layers=failed_layers,
            structural_suggestions=suggestions,
            inter_layer_flow_updates=flow_updates,
        )

    def compute_local_gradient(
        self,
        layer_index: int,
        team_block: dict[str, Any],
        global_gradient: GlobalGradient,
        trajectory: list[dict[str, Any]],
        beta: float = 0.5,
    ) -> LocalGradient:
        """
        Compute local layerwise gradient (G_local,ℓ) combining global feedback and local analysis.
        """
        nodes = team_block.get("nodes", {})
        edges = team_block.get("edges", [])

        prompt_suggestions: dict[str, str] = {}
        node_updates: list[dict[str, Any]] = []
        edge_updates: list[list[str]] = list(edges)

        is_failed = layer_index in global_gradient.failed_layers
        local_loss = 1.0 if is_failed else 0.0
        combined_loss = round(beta * global_gradient.loss_score + (1.0 - beta) * local_loss, 4)

        for node_id in nodes:
            if is_failed:
                prompt_suggestions[node_id] = (
                    f"Refine prompt for node '{node_id}': Add explicit output schema constraints and error checks."
                )
                node_updates.append(
                    {
                        "action": "add_validator_node",
                        "target_node": f"{node_id}_validator",
                        "agent": "agent_static_analysis",
                    }
                )
            else:
                prompt_suggestions[node_id] = (
                    f"Optimize prompt for node '{node_id}': Maintain logical consistency."
                )

        logger.info(
            f"TextualGradientEngine: Computed G_local for layer {layer_index} (combined loss: {combined_loss})"
        )

        return LocalGradient(
            layer_index=layer_index,
            loss_score=combined_loss,
            prompt_suggestions=prompt_suggestions,
            node_updates=node_updates,
            edge_updates=edge_updates,
        )

    def apply_textual_gradient(
        self, team_block: dict[str, Any], local_gradient: LocalGradient
    ) -> dict[str, Any]:
        """
        Apply local textual gradient updates to construct a new candidate team block (f'_ℓ).
        """
        updated_block = copy.deepcopy(team_block)
        updated_block["block_id"] = f"{team_block.get('block_id', 'block')}_v{int(local_gradient.loss_score * 100)}"

        nodes = updated_block.setdefault("nodes", {})
        for node_id, suggestion in local_gradient.prompt_suggestions.items():
            if node_id in nodes:
                orig_prompt = nodes[node_id].get("prompt", "")
                nodes[node_id]["prompt"] = f"{orig_prompt}\n# Optimization: {suggestion}".strip()

        for update in local_gradient.node_updates:
            if update.get("action") == "add_validator_node":
                new_node_id = update["target_node"]
                nodes[new_node_id] = {
                    "agent": update.get("agent", "validator"),
                    "prompt": f"Validate execution output for layer {local_gradient.layer_index}",
                }

        updated_block["edges"] = list(local_gradient.edge_updates)
        return updated_block
