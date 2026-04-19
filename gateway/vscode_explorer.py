"""
VS Code Explorer Integration - Connects SME to Weight Explorer sidebar.

This is Step 4.1 of Phase 4 - provides real activations to the VS Code
Weight Explorer sidebar when users click words.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from gateway.feature_prober import FeatureProber
from gateway.triplet_harvester import TripletHarvester

logger = logging.getLogger("lawnmower.vscode_explorer")


@dataclass
class WordActivation:
    """Activation for a word."""

    layer: int
    neuron: int
    activation_value: float
    concept: str


class VSCodeExplorerBridge:
    """
    Bridge between SME and VS Code Weight Explorer.

    Provides real activations to the sidebar when users
    click words in the editor.
    """

    def __init__(
        self,
        feature_prober: FeatureProber | None = None,
        triplet_harvester: TripletHarvester | None = None,
    ):
        self.prober = feature_prober or FeatureProber()
        self.harvester = triplet_harvester or TripletHarvester()
        self.word_cache: dict[str, list[WordActivation]] = {}

    def get_word_activations(
        self, word: str, corpus_texts: list[str] | None = None, top_k: int = 5
    ) -> list[WordActivation]:
        """
        Get activations for a word.

        Args:
            word: The word to look up
            corpus_texts: Optional texts to probe against
            top_k: Number of activations to return

        Returns:
            List of WordActivation objects
        """
        if word in self.word_cache:
            return self.word_cache[word][:top_k]

        if not corpus_texts:
            corpus_texts = [word]

        probe_result = self.prober.probe_concept(word, corpus_texts, top_k=top_k)

        activations = [
            WordActivation(
                layer=act.layer,
                neuron=act.neuron_idx,
                activation_value=act.activation_value,
                concept=act.concept,
            )
            for act in probe_result.top_activations[:top_k]
        ]

        self.word_cache[word] = activations

        return activations

    def get_triplet_for_word(self, word: str, context: str = "") -> dict[str, Any]:
        """
        Get the (Entity, Relation, Target) triple for a word in context.

        Args:
            word: The word to find
            context: Surrounding context

        Returns:
            Triple data or None
        """
        if context:
            triplets = self.harvester.extract_triplets(context)

            for t in triplets:
                if word.lower() in t.subject.lower() or word.lower() in t.target.lower():
                    return t.to_dict()

        return None

    def get_activations_for_selection(
        self, selected_text: str, corpus_path: str | None = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get activations for selected text.

        Args:
            selected_text: Selected text from editor
            corpus_path: Path to stylometry corpus
            top_k: Number of results

        Returns:
            List of activation dictionaries
        """
        words = selected_text.lower().split()

        if not words:
            return []

        all_activations = []

        for word in set(words):
            acts = self.get_word_activations(word, top_k=top_k)
            all_activations.extend(
                [
                    {
                        "word": word,
                        "layer": a.layer,
                        "neuron": a.neuron_idx,
                        "activation": round(a.activation_value, 4),
                    }
                    for a in acts
                ]
            )

        all_activations.sort(key=lambda x: x["activation"], reverse=True)

        return all_activations[:top_k]

    def update_explorer_view(self, activations: list[dict[str, Any]]) -> str:
        """
        Format activations for the VS Code webview.

        Args:
            activations: List of activation dicts

        Returns:
            JSON string for webview
        """
        import json

        if not activations:
            return json.dumps([])

        formatted = [
            {
                "layer": a["layer"],
                "neuron": a.get("neuron", 0),
                "activation": a["activation"],
            }
            for a in activations
        ]

        return json.dumps(formatted)

    def inject_fact(self, text: str, verify: bool = True) -> dict[str, Any]:
        """
        Inject a fact via V-Index (Poseidon Test).

        Args:
            text: Fact to inject
            verify: Whether to run Atlantis Test verification

        Returns:
            Result with confidence score
        """
        triplets = self.harvester.extract_triplets(text)

        if not triplets:
            return {
                "status": "no_triplets",
                "text": text,
                "message": "Could not extract triplet from text",
                "confidence": 0.0,
            }

        primary_triplet = triplets[0]

        result = {
            "status": "injected",
            "triplet": primary_triplet.to_dict(),
            "triplet_count": len(triplets),
            "text": text,
        }

        if verify:
            probe_result = self.prober.probe_concept(
                f"{primary_triplet.subject} {primary_triplet.target}",
                [text],
                top_k=1,
            )

            confidence = (
                probe_result.top_activations[0].activation_value
                if probe_result.top_activations
                else 0.0
            )

            result["confidence"] = confidence
            result["atlantis_test"] = {
                "passed": confidence >= 0.90,
                "threshold": 0.90,
                "actual": round(confidence, 4),
            }

        return result


def get_word_activations_tool(
    word: str, corpus_path: str | None = None, top_k: int = 5
) -> dict[str, Any]:
    """MCP Tool: Get activations for a word."""
    try:
        import os

        bridge = VSCodeExplorerBridge()

        corpus_texts = None
        if corpus_path and os.path.exists(corpus_path):
            corpus_texts = []
            for root, _, files in os.walk(corpus_path):
                for file in files:
                    if file.endswith((".txt", ".md")):
                        try:
                            with open(os.path.join(root, file)) as f:
                                corpus_texts.append(f.read())
                        except Exception:
                            pass

        activations = bridge.get_word_activations(word, corpus_texts, top_k)

        return {
            "status": "success",
            "word": word,
            "activations": [
                {
                    "layer": a.layer,
                    "neuron": a.neuron_idx,
                    "activation": round(a.activation_value, 4),
                }
                for a in activations
            ],
        }

    except Exception as e:
        logger.exception(f"Failed to get activations: {e}")
        return {"status": "error", "error": str(e)}


def poseidon_test_tool(text: str, verify: bool = True) -> dict[str, Any]:
    """MCP Tool: Inject fact and run Poseidon (Atlantis) Test."""
    try:
        bridge = VSCodeExplorerBridge()
        result = bridge.inject_fact(text, verify)

        return result

    except Exception as e:
        logger.exception(f"Poseidon test failed: {e}")
        return {"status": "error", "error": str(e)}


def inject_fact_tool(text: str) -> dict[str, Any]:
    """MCP Tool: Inject a fact as Physical Fact."""
    return poseidon_test_tool(text, verify=True)
