"""
Semantic Graph Bridge - WordNet & Topos Modal Truth Interfaces
================================================================
Handles semantic graph queries, WordNet relationship extraction, and modal truth state mapping.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("lawnmower.bridges.semantic_graph")


class SemanticGraphBridge:
    """Handles semantic graph queries and WordNet relationship extraction."""

    @staticmethod
    def get_ego_triples(entity_name: str) -> list[tuple]:
        """
        Live ego-graph discovery from the SemanticGraph (WordNet).
        Queries real semantic relationships to build the entity's network.
        """
        from src.core.factory import ToolFactory

        try:
            sg = ToolFactory.create_semantic_graph()
            meaning = sg.explore_meaning(entity_name)

            if not meaning:
                return [(entity_name, "is_a", "Concept"), (entity_name, "status", "unresolved")]

            triples = []
            if meaning.definitions:
                triples.append((entity_name, "definition", meaning.definitions[0]))

            for syn in meaning.synonyms[:3]:
                triples.append((entity_name, "synonym", syn))

            for hyper in meaning.hypernyms[:2]:
                triples.append((entity_name, "is_a", hyper))

            for hypo in meaning.hyponyms[:2]:
                triples.append((hypo, "is_a", entity_name))

            return triples

        except Exception as e:
            logger.exception(f"Ego-graph discovery error: {e}")
            return [(entity_name, "error", str(e))]

    def execute_graph_surface(
        self,
        entity_name: str,
        transformation_code: str,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Extract entity ego-triples and execute a graph transformation surface against them.
        """
        from gateway.surface_bridge import SurfaceBridge

        triples = self.get_ego_triples(entity_name)
        surface_bridge = SurfaceBridge()
        inputs = {"entity": entity_name, "triples": triples}
        return surface_bridge.execute_surface(
            code=transformation_code,
            inputs=inputs,
            schema=schema,
        )

    def get_topos_modal_truth(self, trust_score: float) -> str:
        """Bridge 3: Map continuous float Epistemic Trust Scores (0.0 to 1.0) into Topos Subobject Classifier (Ω) modal truth states.

        Returns NECESSARY, POSSIBLE, CONTINGENT, or IMPOSSIBLE.
        """
        try:
            from em_cubed.ontology.topos import SubobjectClassifier

            tv = SubobjectClassifier.evaluate_confidence(trust_score)
            return f"ToposModalTruth({tv.modal_type.value}, score={tv.score:.2f})"
        except Exception as err:
            logger.warning("Failed to resolve Topos modal truth via Em-Cubed: %s", err)
            return "ToposModalTruth(POSSIBLE, score=0.50)"
