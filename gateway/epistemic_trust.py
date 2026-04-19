"""
Epistemic Trust Validation - Trust-scored knowledge retrieval.

This is Step 3.2 of Phase 3 - integrates SME Trust Scores. If a "Graph Walk" hits
a node with low trust (noise), the system forces backtracking to avoid hallucination.

Tuned thresholds for SME forensic use cases:
- Higher default threshold (0.6) for accuracy-critical tasks
- Configurable weights for source diversity vs citation vs recency
- Hallucination blocking at trust < 0.25
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger("lawnmower.epistemic_trust")

TRUST_LEVELS = {
    "verified": 1.0,  # Fully verified, multi-source
    "high": 0.8,  # High confidence, single strong source
    "medium": 0.6,  # Medium confidence
    "low": 0.4,  # Low confidence, needs verification
    "noise": 0.2,  # Likely hallucination
}

# Tuned thresholds for SME forensic tasks
DEFAULT_TRUST_THRESHOLD = 0.6  # Higher for accuracy
HALLUCINATION_BLOCK_THRESHOLD = 0.25  # Block below this

# Trust calculation weights (tuned for forensic accuracy)
TRUST_WEIGHTS = {
    "source_diversity": 0.30,  # Multiple independent sources
    "source_type": 0.25,  # Verified/official sources weighted higher
    "citation": 0.20,  # Citations indicate reliability
    "recency": 0.15,  # Recent info preferred
    "verification": 0.10,  # Manual verification status
}


@dataclass
class TrustScore:
    """A trust score for a knowledge node."""

    node_id: str
    score: float
    level: str
    factors: dict[str, float] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class TrustEvaluation:
    """Result of trust evaluation."""

    trusted: bool
    trust_score: float
    level: str
    recommendation: str
    reasoning: str = ""
    alternative_paths: list[dict[str, Any]] = field(default_factory=list)


class EpistemicTrustValidator:
    """
    Validates knowledge nodes using trust scores.

    Integrates with Graph Walk to filter low-trust nodes
    and guide backtracking when trust is insufficient.
    """

    def __init__(self, trust_threshold: float = DEFAULT_TRUST_THRESHOLD, min_source_count: int = 2):
        self.trust_threshold = trust_threshold
        self.min_source_count = min_source_count
        self.trust_cache: dict[str, TrustScore] = {}

    def calculate_trust(
        self,
        node_id: str,
        source_count: int = 1,
        source_types: list[str] | None = None,
        citation_count: int = 0,
        recency_score: float = 0.5,
        verification_status: str = "unverified",
    ) -> TrustScore:
        """
        Calculate trust score for a node.

        Args:
            node_id: The node to evaluate
            source_count: Number of independent sources
            source_types: Types of sources (e.g., ["academic", "official"])
            citation_count: Number of citations/references
            recency_score: How recent the information is (0-1)
            verification_status: "verified", "high", "medium", "low", "unverified"

        Returns:
            TrustScore with level and reasoning
        """
        factors = {}

        factors["source_diversity"] = min(source_count / 3, 1.0) * 0.3

        if source_types:
            verified_types = sum(
                1 for t in source_types if t in ["official", "academic", "primary"]
            )
            factors["source_type"] = (verified_types / len(source_types)) * 0.25
        else:
            factors["source_type"] = 0.0

        factors["citation"] = min(citation_count / 10, 1.0) * 0.2

        factors["recency"] = recency_score * 0.15

        if verification_status == "verified":
            factors["verification"] = 1.0 * 0.1
        elif verification_status == "high":
            factors["verification"] = 0.8 * 0.1
        else:
            factors["verification"] = 0.3 * 0.1

        total_score = sum(factors.values())

        if total_score >= 0.8:
            level = "verified"
        elif total_score >= 0.6:
            level = "high"
        elif total_score >= 0.4:
            level = "medium"
        elif total_score >= 0.25:
            level = "low"
        else:
            level = "noise"

        reasoning = self._generate_reasoning(factors, level, source_count)

        trust_score = TrustScore(
            node_id=node_id,
            score=total_score,
            level=level,
            factors=factors,
            reasoning=reasoning,
        )

        self.trust_cache[node_id] = trust_score

        return trust_score

    def _generate_reasoning(self, factors: dict[str, float], level: str, source_count: int) -> str:
        """Generate reasoning for trust score."""
        parts = []

        if factors.get("source_diversity", 0) >= 0.2:
            parts.append(f"Multi-source ({source_count} sources)")

        if factors.get("source_type", 0) >= 0.15:
            parts.append("Verified source type")

        if factors.get("citation", 0) >= 0.1:
            parts.append("Well-cited")

        if factors.get("recency", 0) >= 0.1:
            parts.append("Recent")

        if level == "noise":
            parts.append("Requires verification")

        return "; ".join(parts) if parts else f"Single-source, {level} confidence"

    def evaluate_node(self, node: dict[str, Any]) -> TrustEvaluation:
        """
        Evaluate a knowledge node for trust.

        Args:
            node: Node dictionary with trust-relevant fields

        Returns:
            TrustEvaluation with recommendation
        """
        source_count = node.get("source_count", 1)
        source_types = node.get("source_types", [])
        citation_count = node.get("citation_count", 0)
        recency = node.get("recency_score", 0.5)
        verification = node.get("verification_status", "unverified")

        trust = self.calculate_trust(
            node_id=node.get("node_id", ""),
            source_count=source_count,
            source_types=source_types,
            citation_count=citation_count,
            recency_score=recency,
            verification_status=verification,
        )

        trusted = trust.score >= self.trust_threshold

        if trusted:
            recommendation = "use"
            alternative_paths = []
        else:
            recommendation = self._suggest_alternatives(node)
            alternative_paths = [node]

        return TrustEvaluation(
            trusted=trusted,
            trust_score=trust.score,
            level=trust.level,
            recommendation=recommendation + " (" + trust.reasoning + ")"
            if trust.reasoning
            else recommendation,
            reasoning=trust.reasoning,
            alternative_paths=alternative_paths,
        )

    def _suggest_alternatives(self, node: dict[str, Any]) -> str:
        """Suggest how to handle low-trust node."""
        current_confidence = node.get("confidence", 0)

        if current_confidence < 0.2:
            return "discard - confidence too low"

        if node.get("source_count", 1) < self.min_source_count:
            return "backtrack - seek additional sources"

        return "verify before use"

    def filter_by_trust(
        self, nodes: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Filter nodes by trust threshold.

        Args:
            nodes: List of nodes to filter

        Returns:
            (trusted_nodes, rejected_nodes)
        """
        trusted = []
        rejected = []

        for node in nodes:
            evaluation = self.evaluate_node(node)

            if evaluation.trusted:
                node["trust_evaluation"] = {
                    "level": evaluation.level,
                    "score": evaluation.trust_score,
                    "reasoning": evaluation.reasoning,
                }
                trusted.append(node)
            else:
                node["trust_evaluation"] = {
                    "level": evaluation.level,
                    "score": evaluation.trust_score,
                    "recommendation": evaluation.recommendation,
                    "reasoning": evaluation.reasoning,
                }
                rejected.append(node)

        return trusted, rejected

    def validate_walk_results(self, walk_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate graph walk results with trust scoring.

        Args:
            walk_results: Results from GraphWalkKNNOps

        Returns:
            Validated results with trust filtering
        """
        if not walk_results:
            return {
                "status": "no_results",
                "trusted": [],
                "rejected": [],
                "summary": "No results to validate",
            }

        trusted, rejected = self.filter_by_trust(walk_results)

        avg_trust = np.mean([r["trust_score"] for r in walk_results]) if walk_results else 0

        blocked_hallucination = any(r["trust_score"] < 0.25 for r in walk_results)

        return {
            "status": "validated",
            "trusted": trusted,
            "rejected": rejected,
            "total_input": len(walk_results),
            "trusted_count": len(trusted),
            "rejected_count": len(rejected),
            "avg_trust_score": round(avg_trust, 4),
            "blocked_hallucination": blocked_hallucination,
            "recommendation": "proceed" if trusted else "fallback",
        }

    def get_trust_stats(self) -> dict[str, Any]:
        """Get trust validation statistics."""
        level_counts: dict[str, int] = {}

        for trust in self.trust_cache.values():
            level_counts[trust.level] = level_counts.get(trust.level, 0) + 1

        avg_score = np.mean([t.score for t in self.trust_cache.values()]) if self.trust_cache else 0

        return {
            "total_evaluated": len(self.trust_cache),
            "level_distribution": level_counts,
            "avg_trust_score": round(avg_score, 4),
            "trust_threshold": self.trust_threshold,
        }


class HallucinationBlocker:
    """
    Blocks halluncination by enforcing trust thresholds.

    When integrated with Graph Walk, forces backtracking
    when low-trust nodes are encountered.

    Tuned for SME forensic accuracy:
    - Default block at trust < 0.25 (hallucination threshold)
    - Fallback at trust < 0.6 (accuracy threshold)
    - Auto-tune based on false positive rate
    """

    def __init__(
        self,
        validator: EpistemicTrustValidator | None = None,
        block_threshold: float = HALLUCINATION_BLOCK_THRESHOLD,
        accuracy_threshold: float = DEFAULT_TRUST_THRESHOLD,
    ):
        self.validator = validator or EpistemicTrustValidator()
        self.block_threshold = block_threshold
        self.accuracy_threshold = accuracy_threshold
        self._auto_tune_history: list[bool] = []

    def auto_tune_threshold(self, feedback: bool | None = None):
        """
        Auto-tune thresholds based on feedback.

        Args:
            feedback: True if blocked result was correct, False if false positive
        """
        if feedback is not None:
            self._auto_tune_history.append(feedback)
            if len(self._auto_tune_history) > 100:
                self._auto_tune_history = self._auto_tune_history[-100:]

        if len(self._auto_tune_history) >= 20:
            fp_rate = sum(1 for x in self._auto_tune_history if not x) / len(
                self._auto_tune_history
            )

            if fp_rate > 0.3:
                self.block_threshold += 0.05
                logger.info(f"Auto-tune: increased block_threshold to {self.block_threshold}")
            elif fp_rate < 0.1 and self.block_threshold > 0.15:
                self.block_threshold -= 0.02
                logger.info(f"Auto-tune: decreased block_threshold to {self.block_threshold}")

    def check_and_block(self, graph_walk_results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Check results and block low-trust hallucination.

        Args:
            graph_walk_results: Results from Graph Walk

        Returns:
            Filtered results or block notification
        """
        if not graph_walk_results:
            return {
                "blocked": True,
                "reason": "no_results",
                "action": "fallback_to_model",
            }

        validation = self.validator.validate_walk_results(graph_walk_results)

        if validation["blocked_hallucination"]:
            return {
                "blocked": True,
                "reason": "low_trust_detected",
                "confidence": validation["avg_trust_score"],
                "action": "force_backtrack",
                "details": validation,
            }

        if not validation["trusted"]:
            return {
                "blocked": True,
                "reason": "trust_below_threshold",
                "avg_trust": validation["avg_trust_score"],
                "action": "fallback_to_model",
                "details": validation,
            }

        return {
            "blocked": False,
            "action": "proceed_with_trusted",
            "trusted_results": validation["trusted"],
            "details": validation,
        }


def trust_evaluate_tool(node: dict[str, Any]) -> dict[str, Any]:
    """MCP Tool: Evaluate a node's trust score."""
    try:
        validator = EpistemicTrustValidator()
        evaluation = validator.evaluate_node(node)

        return {
            "status": "success",
            "trusted": evaluation.trusted,
            "trust_score": round(evaluation.trust_score, 4),
            "level": evaluation.level,
            "recommendation": evaluation.recommendation,
            "reasoning": evaluation.reasoning,
        }

    except Exception as e:
        logger.exception(f"Trust evaluation failed: {e}")
        return {"status": "error", "error": str(e)}


def trust_filter_tool(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """MCP Tool: Filter nodes by trust."""
    try:
        validator = EpistemicTrustValidator()
        trusted, rejected = validator.filter_by_trust(nodes)

        return {
            "status": "success",
            "trusted": trusted,
            "rejected": rejected,
            "trusted_count": len(trusted),
            "rejected_count": len(rejected),
        }

    except Exception as e:
        logger.exception(f"Trust filter failed: {e}")
        return {"status": "error", "error": str(e)}


def hallucination_block_tool(walk_results: list[dict[str, Any]]) -> dict[str, Any]:
    """MCP Tool: Check and block hallucination."""
    try:
        blocker = HallucinationBlocker()
        result = blocker.check_and_block(walk_results)

        return result

    except Exception as e:
        logger.exception(f"Hallucination check failed: {e}")
        return {"status": "error", "error": str(e)}
