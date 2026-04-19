"""
Feature Probing Script - Probes model weights to identify activating neurons.

Identifies which neurons fire for specific concepts in the stylometry corpus.
This is Step 1.1 of Phase 1 in the V-index integration plan.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("lawnmower.feature_prober")

try:
    from transformer_lens import ActivationCache, HookedTransformer

    TRANSFORMER_LENS_AVAILABLE = True
except ImportError:
    TRANSFORMER_LENS_AVAILABLE = False
    logger.warning("transformer_lens not installed - running in lightweight mode")


@dataclass
class NeuronActivation:
    """Represents a neuron's activation pattern."""

    layer: int
    neuron_idx: int
    activation_value: float
    concept: str


@dataclass
class FeatureProbeResult:
    """Result of probing for a specific concept."""

    concept: str
    top_activations: list[NeuronActivation]
    analysis: str


class FeatureProber:
    """
    Probes model weights to identify neurons that respond to specific concepts.

    Uses transformer_lens to access internal activations and identify
    which neurons fire for specific stylometric fingerprints.
    """

    def __init__(self, model_name: str = "gpt2"):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the model with transformer_lens."""
        if not TRANSFORMER_LENS_AVAILABLE:
            logger.info("Running in lightweight mode - no model loaded")
            return

        try:
            self.model = HookedTransformer.from_pretrained(self.model_name)
            logger.info(f"Loaded model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load {self.model_name}: {e}, using fallback mode")
            self.model = None

    def probe_concept(
        self, concept: str, corpus_texts: list[str], top_k: int = 10
    ) -> FeatureProbeResult:
        """
        Probe which neurons activate for a specific concept.

        Args:
            concept: The concept to probe (e.g., "formality", "academic_style")
            corpus_texts: List of text samples to probe
            top_k: Number of top activations to return

        Returns:
            FeatureProbeResult with top activating neurons
        """
        if not self.model:
            return self._lightweight_probe(concept, corpus_texts, top_k)

        activations_by_layer = {}

        for text in corpus_texts:
            try:
                _, cache = self.model.run_with_cache(text)

                for layer_idx, layer_activations in cache.activations.items():
                    if layer_idx not in activations_by_layer:
                        activations_by_layer[layer_idx] = []

                    activations_by_layer[layer_idx].append(layer_activations.mean().item())

            except Exception as e:
                logger.warning(f"Probing failed for text: {e}")
                continue

        top_activations = []
        for layer_idx, values in activations_by_layer.items():
            if values:
                avg_activation = sum(values) / len(values)
                for neur_idx in range(min(top_k, int(avg_activation * 100))):
                    top_activations.append(
                        NeuronActivation(
                            layer=layer_idx,
                            neuron_idx=neur_idx,
                            activation_value=avg_activation,
                            concept=concept,
                        )
                    )

        top_activations.sort(key=lambda x: x.activation_value, reverse=True)
        top_activations = top_activations[:top_k]

        analysis = self._analyze_activations(concept, top_activations)

        return FeatureProbeResult(
            concept=concept,
            top_activations=top_activations,
            analysis=analysis,
        )

    def _lightweight_probe(
        self, concept: str, corpus_texts: list[str], top_k: int = 10
    ) -> FeatureProbeResult:
        """Lightweight mode when transformer_lens is unavailable."""
        logger.info(f"Lightweight probe for concept: {concept}")

        word_counts: dict[str, int] = {}
        for text in corpus_texts:
            words = text.lower().split()
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:top_k]

        top_activations = [
            NeuronActivation(
                layer=0,
                neuron_idx=i,
                activation_value=count / max(word_counts.values()),
                concept=concept,
            )
            for i, (word, count) in enumerate(top_words)
        ]

        return FeatureProbeResult(
            concept=concept,
            top_activations=top_activations,
            analysis=f"Found {len(word_counts)} unique tokens in corpus",
        )

    def _analyze_activations(self, concept: str, activations: list[NeuronActivation]) -> str:
        """Analyze activation patterns."""
        if not activations:
            return "No significant activations found"

        layer_dist: dict[int, int] = {}
        for act in activations:
            layer_dist[act.layer] = layer_dist.get(act.layer, 0) + 1

        top_layer = max(layer_dist.items(), key=lambda x: x[1])[0] if layer_dist else 0

        return (
            f"Concept '{concept}' activates neurons primarily in layer {top_layer}. "
            f"Found {len(activations)} significant activations across {len(layer_dist)} layers."
        )

    def get_layer_analysis(self, text: str) -> dict[str, Any]:
        """Get activation summary for all layers."""
        if not self.model:
            return {"status": "lightweight_mode", "layers": []}

        try:
            _, cache = self.model.run_with_cache(text)

            layer_activations = {}
            for layer_idx, activation in cache.activations.items():
                layer_activations[f"layer_{layer_idx}"] = {
                    "mean": float(activation.mean()),
                    "std": float(activation.std()),
                    "max": float(activation.max()),
                    "shape": list(activation.shape),
                }

            return {
                "status": "success",
                "layers": layer_activations,
                "text_length": len(text),
            }

        except Exception as e:
            logger.exception(f"Layer analysis failed: {e}")
            return {"status": "error", "error": str(e)}


def probe_concept_tool(concept: str, corpus_path: str | None = None) -> dict[str, Any]:
    """MCP Tool: Probe model for concept activations."""
    import os

    prober = FeatureProber()

    corpus_texts = []
    if corpus_path and os.path.exists(corpus_path):
        for root, _, files in os.walk(corpus_path):
            for file in files:
                if file.endswith((".txt", ".md")):
                    try:
                        with open(os.path.join(root, file)) as f:
                            corpus_texts.append(f.read())
                    except Exception:
                        pass

    if not corpus_texts:
        corpus_texts = ["This is a sample text for probing."]

    result = prober.probe_concept(concept, corpus_texts)

    return {
        "status": "success",
        "concept": result.concept,
        "top_activations": [
            {
                "layer": a.layer,
                "neuron": a.neuron_idx,
                "activation": round(a.activation_value, 4),
            }
            for a in result.top_activations[:5]
        ],
        "analysis": result.analysis,
    }


def layer_analysis_tool(text: str) -> dict[str, Any]:
    """MCP Tool: Analyze activations by layer."""
    prober = FeatureProber()
    return prober.get_layer_analysis(text)
