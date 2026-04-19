"""
V-Index Overlay - Patch system that intercepts LLM calls and injects triples.

This is Step 1.3 of Phase 1 - the "Mock V-Index Overlay" that intercepts
LLM calls and injects (Entity, Relation, Target) triples into prompt context
via hidden "Actuator" tokens.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from gateway.triplet_harvester import TripletHarvester

logger = logging.getLogger("lawnmower.vindex_overlay")

ACTUATOR_TOKEN = "[V-INDEX]"
ACTUATOR_PREFIX = f"{ACTUATOR_TOKEN} Facts:"


@dataclass
class VIndexTriple:
    """A triple ready for injection."""

    subject: str
    relation: str
    target: str
    weight: float = 1.0

    def to_injection(self) -> str:
        return f"{self.subject} --{self.relation}--> {self.target}"


@dataclass
class VIndexConfig:
    """Configuration for V-Index injection."""

    max_triplets: int = 10
    min_confidence: float = 0.5
    use_actuator_tokens: bool = True
    include_source: bool = False


class VIndexOverlay:
    """
    Overlay system that patches LLM calls with extracted triples.

    Intercepts prompts and injects (Entity, Relation, Target) triples
    from the SME knowledge base to provide "Physical" facts.
    """

    def __init__(
        self,
        config: VIndexConfig | None = None,
        triplet_harvester: TripletHarvester | None = None,
    ):
        self.config = config or VIndexConfig()
        self.harvester = triplet_harvester or TripletHarvester()
        self.triple_store: list[VIndexTriple] = []
        self.injection_count = 0

    def add_triplets(self, text: str, min_confidence: float = 0.5):
        """Extract and store triples from text."""
        raw_triplets = self.harvester.extract_triplets(text)

        for t in raw_triplets:
            if t.confidence >= min_confidence:
                self.triple_store.append(
                    VIndexTriple(
                        subject=t.subject,
                        relation=t.relation,
                        target=t.target,
                        weight=t.confidence,
                    )
                )

        logger.info(f"Added {len(raw_triplets)} triplets to V-Index store")

    def build_injection_prompt(self, context: str) -> str:
        """
        Build the injection prompt with relevant triples.

        Args:
            context: The context/query to match triplets against

        Returns:
            Formatted injection string
        """
        if not self.triple_store:
            return ""

        relevant = self._find_relevant_triplets(context)
        relevant = relevant[: self.config.max_triplets]

        if not relevant:
            return ""

        lines = [ACTUATOR_PREFIX] if self.config.use_actuator_tokens else []

        for triple in relevant:
            lines.append(triple.to_injection())

        self.injection_count = len(relevant)

        return "\n".join(lines)

    def _find_relevant_triplets(self, context: str) -> list[VIndexTriple]:
        """Find triplets relevant to the query context."""
        context_lower = context.lower()
        context_words = set(context_lower.split())

        scored_triplets = []

        for triple in self.triple_store:
            score = 0.0

            if triple.subject.lower() in context_lower:
                score += 1.0
            if triple.target.lower() in context_lower:
                score += 1.0

            triple_words = set(triple.subject.lower().split()) | set(triple.target.lower().split())
            overlap = len(context_words & triple_words)
            score += overlap * 0.2

            score *= triple.weight

            scored_triplets.append((score, triple))

        scored_triplets.sort(key=lambda x: x[0], reverse=True)

        return [t for _, t in scored_triplets if _ > 0]

    def patch_prompt(self, original_prompt: str, context_text: str | None = None) -> str:
        """
        Patch a prompt with V-Index triples.

        Args:
            original_prompt: The original prompt to patch
            context_text: Optional context to extract new triples from

        Returns:
            Patched prompt with triples injected
        """
        if context_text:
            self.add_triplets(context_text)

        injection = self.build_injection_prompt(original_prompt)

        if not injection:
            return original_prompt

        return f"{original_prompt}\n\n{injection}"

    def clear_store(self):
        """Clear the triple store."""
        self.triple_store.clear()
        self.injection_count = 0
        logger.info("V-Index store cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get overlay statistics."""
        relation_dist: dict[str, int] = {}
        for t in self.triple_store:
            relation_dist[t.relation] = relation_dist.get(t.relation, 0) + 1

        return {
            "total_triplets": len(self.triple_store),
            "injections_made": self.injection_count,
            "relation_distribution": relation_dist,
            "config": {
                "max_triplets": self.config.max_triplets,
                "min_confidence": self.config.min_confidence,
                "use_actuator_tokens": self.config.use_actuator_tokens,
            },
        }


class VIndexMiddleware:
    """
    Middleware to patch LLM calls with V-Index triples.

    Can be integrated with the Operator to intercept calls.
    """

    def __init__(self, overlay: VIndexOverlay | None = None):
        self.overlay = overlay or VIndexOverlay()

    def inject(self, prompt: str, knowledge_base: str | None = None) -> str:
        """
        Inject V-Index triples into a prompt.

        Args:
            prompt: The user's prompt
            knowledge_base: Optional text to extract triples from

        Returns:
            Patched prompt
        """
        if knowledge_base:
            self.overlay.add_triplets(knowledge_base)

        return self.overlay.patch_prompt(prompt)

    def wrap_provider(self, provider_fn: Callable[[str], str]) -> Callable[[str, str | None], str]:
        """
        Wrap an LLM provider function with V-Index injection.

        Returns a wrapped function that automatically injects triples.
        """

        def wrapped(prompt: str, knowledge_base: str | None = None) -> str:
            patched = self.inject(prompt, knowledge_base)
            return provider_fn(patched)

        return wrapped


def vindex_inject_tool(prompt: str, knowledge_base: str | None = None) -> dict[str, Any]:
    """MCP Tool: Inject V-Index triples into prompt."""
    try:
        overlay = VIndexOverlay()

        if knowledge_base:
            overlay.add_triplets(knowledge_base)

        patched = overlay.patch_prompt(prompt)

        return {
            "status": "success",
            "original_prompt": prompt,
            "patched_prompt": patched,
            "injections_made": overlay.injection_count,
            "stats": overlay.get_stats(),
        }

    except Exception as e:
        logger.exception(f"V-Index injection failed: {e}")
        return {"status": "error", "error": str(e)}


def vindex_stats_tool() -> dict[str, Any]:
    """MCP Tool: Get V-Index statistics."""
    try:
        overlay = VIndexOverlay()
        return {"status": "success", "stats": overlay.get_stats()}

    except Exception as e:
        logger.exception(f"Stats failed: {e}")
        return {"status": "error", "error": str(e)}
