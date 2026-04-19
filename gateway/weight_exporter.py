"""
Weight-to-GML Exporter - Exports model activations to GraphML/CSV for Gephi.

This is Step 2.1 of Phase 2 - exports model activations into .graphml or .csv
(Edge List) for Gephi visualization.
"""

from __future__ import annotations

import csv
import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("lawnmower.weight_exporter")

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not installed - using basic export")


@dataclass
class ActivationNode:
    """Represents a neuron activation node."""

    id: str
    layer: int
    neuron_idx: int
    activation_value: float
    concept: str = ""
    node_type: str = "neuron"


@dataclass
class ActivationEdge:
    """Represents a connection between activations."""

    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "connects"


@dataclass
class ActivationGraph:
    """Graph of model activations."""

    nodes: list[ActivationNode] = field(default_factory=list)
    edges: list[ActivationEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class WeightToGMLExporter:
    """
    Exports model activations to GraphML/CSV for Gephi visualization.

    Takes activations from FeatureProber and exports them in formats
    that Gephi can visualize to show the neural topology.
    """

    def __init__(self):
        self.graph = ActivationGraph()
        self.node_id_counter = 0

    def add_layer_activations(
        self, layer_idx: int, activations: dict[str, float], concept: str = ""
    ):
        """Add activations from a specific layer."""
        for neur_idx, act_value in activations.items():
            node_id = f"L{layer_idx}_N{neur_idx}"

            self.graph.nodes.append(
                ActivationNode(
                    id=node_id,
                    layer=layer_idx,
                    neuron_idx=int(neur_idx) if isinstance(neur_idx, int) else 0,
                    activation_value=act_value,
                    concept=concept,
                )
            )

            self.node_id_counter += 1

    def add_triplet_graph(self, triplets: list[dict], trust_scores: dict[str, float] | None = None):
        """Add a graph from extracted triplets (Entity-Relation-Target)."""
        entity_nodes: dict[str, str] = {}

        for i, triple in enumerate(triplets):
            sub_id = f"entity_{triple.get('subject', f'subj_{i}')}"
            obj_id = f"entity_{triple.get('target', f'obj_{i}')}"

            if sub_id not in entity_nodes:
                self.graph.nodes.append(
                    ActivationNode(
                        id=sub_id,
                        layer=0,
                        neuron_idx=i,
                        activation_value=trust_scores.get(sub_id, 1.0) if trust_scores else 1.0,
                        concept=triple.get("subject", ""),
                        node_type="entity",
                    )
                )
                entity_nodes[sub_id] = sub_id

            if obj_id not in entity_nodes:
                self.graph.nodes.append(
                    ActivationNode(
                        id=obj_id,
                        layer=0,
                        neuron_idx=i,
                        activation_value=trust_scores.get(obj_id, 1.0) if trust_scores else 1.0,
                        concept=triple.get("target", ""),
                        node_type="entity",
                    )
                )
                entity_nodes[obj_id] = obj_id

            self.graph.edges.append(
                ActivationEdge(
                    source=sub_id,
                    target=obj_id,
                    weight=triple.get("confidence", 0.8),
                    edge_type=triple.get("relation", "related_to"),
                )
            )

    def add_stylometric_profile(self, author_id: str, fingerprint: dict[str, Any]):
        """Add a stylometric profile as a graph cluster."""
        cluster_id = f"cluster_{author_id}"

        self.graph.nodes.append(
            ActivationNode(
                id=cluster_id,
                layer=-1,
                neuron_idx=0,
                activation_value=1.0,
                concept=author_id,
                node_type="profile",
            )
        )

        metrics = [
            ("avg_sentence_length", fingerprint.get("avg_sentence_length", 0)),
            ("lexical_diversity", fingerprint.get("lexical_diversity", 0)),
            ("passive_voice_ratio", fingerprint.get("passive_voice_ratio", 0)),
        ]

        for metric_name, metric_value in metrics:
            metric_id = f"{cluster_id}_{metric_name}"
            self.graph.nodes.append(
                ActivationNode(
                    id=metric_id,
                    layer=-1,
                    neuron_idx=0,
                    activation_value=metric_value,
                    concept=metric_name,
                    node_type="metric",
                )
            )
            self.graph.edges.append(
                ActivationEdge(
                    source=cluster_id,
                    target=metric_id,
                    weight=1.0,
                    edge_type="has_metric",
                )
            )

    def export_graphml(self, output_path: str) -> str:
        """
        Export to GraphML format.

        Args:
            output_path: Path for output file

        Returns:
            Status message
        """
        if not NETWORKX_AVAILABLE:
            return self._export_graphml_basic(output_path)

        G = nx.DiGraph()

        for node in self.graph.nodes:
            G.add_node(
                node.id,
                layer=node.layer,
                neuron_idx=node.neuron_idx,
                activation=node.activation_value,
                concept=node.concept,
                node_type=node.node_type,
            )

        for edge in self.graph.edges:
            G.add_edge(
                edge.source,
                edge.target,
                weight=edge.weight,
                edge_type=edge.edge_type,
            )

        nx.write_graphml(G, output_path)

        self.graph.metadata["export_format"] = "graphml"
        self.graph.metadata["node_count"] = len(self.graph.nodes)
        self.graph.metadata["edge_count"] = len(self.graph.edges)

        logger.info(
            f"Exported {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges to {output_path}"
        )

        return f"Exported {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges to {output_path}"

    def _export_graphml_basic(self, output_path: str) -> str:
        """Basic GraphML export without networkx."""
        root = ET.Element("graphml")
        root.set("xmlns", "http://graphml.graphdrawing.org/ns")

        for node in self.graph.nodes:
            ET.SubElement(
                root,
                "node",
                {
                    "id": node.id,
                    "layer": str(node.layer),
                    "activation": str(node.activation_value),
                    "concept": node.concept,
                },
            )

        for edge in self.graph.edges:
            ET.SubElement(
                root,
                "edge",
                {
                    "source": edge.source,
                    "target": edge.target,
                    "weight": str(edge.weight),
                },
            )

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        return f"Exported {len(self.graph.nodes)} nodes to {output_path}"

    def export_csv_edge_list(self, output_path: str) -> str:
        """
        Export to CSV edge list format.

        Args:
            output_path: Path for output file

        Returns:
            Status message
        """
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "weight", "edge_type"])

            for edge in self.graph.edges:
                writer.writerow(
                    [
                        edge.source,
                        edge.target,
                        edge.weight,
                        edge.edge_type,
                    ]
                )

        logger.info(f"Exported {len(self.graph.edges)} edges to {output_path}")

        self.graph.metadata["export_format"] = "csv"
        self.graph.metadata["edge_count"] = len(self.graph.edges)

        return f"Exported {len(self.graph.edges)} edges to {output_path}"

    def export_csv_node_list(self, output_path: str) -> str:
        """
        Export to CSV node list format.

        Args:
            output_path: Path for output file

        Returns:
            Status message
        """
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "layer", "neuron_idx", "activation", "concept", "node_type"])

            for node in self.graph.nodes:
                writer.writerow(
                    [
                        node.id,
                        node.layer,
                        node.neuron_idx,
                        node.activation_value,
                        node.concept,
                        node.node_type,
                    ]
                )

        logger.info(f"Exported {len(self.graph.nodes)} nodes to {output_path}")

        self.graph.metadata["export_format"] = "csv_nodes"
        self.graph.metadata["node_count"] = len(self.graph.nodes)

        return f"Exported {len(self.graph.nodes)} nodes to {output_path}"

    def export_gexf(self, output_path: str) -> str:
        """Export to GEXF format (for Gephi)."""
        if not NETWORKX_AVAILABLE:
            return self._export_graphml_basic(output_path.replace(".gexf", ".graphml"))

        G = nx.DiGraph()

        for node in self.graph.nodes:
            G.add_node(
                node.id,
                layer=node.layer,
                neuron_idx=node.neuron_idx,
                activation=node.activation_value,
                concept=node.concept,
                node_type=node.node_type,
            )

        for edge in self.graph.edges:
            G.add_edge(
                edge.source,
                edge.target,
                weight=edge.weight,
                edge_type=edge.edge_type,
            )

        nx.write_gexf(G, output_path)

        self.graph.metadata["export_format"] = "gexf"
        self.graph.metadata["node_count"] = len(self.graph.nodes)
        self.graph.metadata["edge_count"] = len(self.graph.edges)

        return f"Exported {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges to {output_path}"

    def get_graph_summary(self) -> dict[str, Any]:
        """Get summary of the current graph."""
        layers: dict[int, int] = {}
        node_types: dict[str, int] = {}

        for node in self.graph.nodes:
            layers[node.layer] = layers.get(node.layer, 0) + 1
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1

        edge_types: dict[str, int] = {}
        for edge in self.graph.edges:
            edge_types[edge.edge_type] = edge_types.get(edge.edge_type, 0) + 1

        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "nodes_by_layer": layers,
            "node_types": node_types,
            "edge_types": edge_types,
            "metadata": self.graph.metadata,
        }


def export_activations_tool(
    activations: list[dict], output_path: str, format: str = "graphml"
) -> dict[str, Any]:
    """MCP Tool: Export activations to GraphML/CSV."""
    try:
        exporter = WeightToGMLExporter()

        for act in activations:
            layer = act.get("layer", 0)
            values = act.get("values", {})
            concept = act.get("concept", "")
            exporter.add_layer_activations(layer, values, concept)

        if format == "graphml":
            result = exporter.export_graphml(output_path)
        elif format == "gexf":
            result = exporter.export_gexf(output_path)
        elif format == "csv_edges":
            result = exporter.export_csv_edge_list(output_path)
        elif format == "csv_nodes":
            result = exporter.export_csv_node_list(output_path)
        else:
            return {"status": "error", "error": f"Unknown format: {format}"}

        return {
            "status": "success",
            "message": result,
            "summary": exporter.get_graph_summary(),
        }

    except Exception as e:
        logger.exception(f"Export failed: {e}")
        return {"status": "error", "error": str(e)}


def export_triplets_tool(
    triplets: list[dict],
    output_path: str,
    format: str = "graphml",
    trust_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    """MCP Tool: Export triplets to graph format."""
    try:
        exporter = WeightToGMLExporter()
        exporter.add_triplet_graph(triplets, trust_scores)

        if format == "graphml":
            result = exporter.export_graphml(output_path)
        elif format == "gexf":
            result = exporter.export_gexf(output_path)
        elif format == "csv_edges":
            result = exporter.export_csv_edge_list(output_path)
        else:
            return {"status": "error", "error": f"Unknown format: {format}"}

        return {
            "status": "success",
            "message": result,
            "summary": exporter.get_graph_summary(),
        }

    except Exception as e:
        logger.exception(f"Export failed: {e}")
        return {"status": "error", "error": str(e)}
