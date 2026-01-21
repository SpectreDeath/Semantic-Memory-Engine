"""
Knowledge Graph Engine
======================

Phase 6 component for building and visualizing semantic networks from text.
Integrates EntityLinker and SemanticGraph to create high-level knowledge representations.

Features:
- Entity-relation extraction from multi-document sources
- Semantic enrichment using WordNet (via SemanticGraph)
- Graph visualization exports (Mermaid, JSON/D3)
- Density and central entity analysis
"""

import logging
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict

from src.core.factory import ToolFactory
from src.core.entity_linker import LinkedEntity, EntityLink, EntityType

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]
    weight: float = 1.0


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""
    source: str
    target: str
    relation: str
    confidence: float
    metadata: Dict[str, Any]


class KnowledgeGraph:
    """
    Engine for building and managing semantic knowledge graphs.
    
    Orchestrates lower-level tools to synthesize entities and relations
    into a cohesive graph structure.
    """
    
    def __init__(self):
        """Initialize KnowledgeGraph with required tools."""
        self.entity_linker = ToolFactory.create_entity_linker()
        self.semantic_graph = ToolFactory.create_semantic_graph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        
        logger.info("KnowledgeGraph engine initialized")
    
    def clear(self):
        """Clear the current graph state."""
        self.nodes.clear()
        self.edges.clear()
        logger.debug("Knowledge graph cleared")

    def build_from_text(self, text: str, context_id: str = "default"):
        """
        Build or update the graph from a text blob.
        
        Args:
            text: Input text to process
            context_id: Identifier for the source context
        """
        result = self.entity_linker.link_entities(text)
        
        # Add entities as nodes
        for linked in result.linked_entities:
            node_id = linked.kb_id
            if node_id not in self.nodes:
                self.nodes[node_id] = GraphNode(
                    id=node_id,
                    label=linked.entity.text,
                    type=linked.entity.entity_type.value,
                    properties=linked.properties
                )
            else:
                self.nodes[node_id].weight += 0.5  # Increase weight on co-occurrence
                
        # Add relationships as edges
        for link in result.entity_links:
            self.add_edge(
                source=link.source.kb_id,
                target=link.target.kb_id,
                relation=link.relation_type,
                confidence=link.confidence,
                metadata={"context": context_id}
            )
            
        # Semantic enrichment
        if self.semantic_graph.is_available():
            self._enrich_semantically(result.linked_entities)

    def add_edge(self, source: str, target: str, relation: str, 
                 confidence: float = 1.0, metadata: Dict[str, Any] = None):
        """Add a directed edge to the graph if it doesn't already exist."""
        # Avoid duplicate edges with same relation
        for edge in self.edges:
            if edge.source == source and edge.target == target and edge.relation == relation:
                return
        
        self.edges.append(GraphEdge(
            source=source,
            target=target,
            relation=relation,
            confidence=confidence,
            metadata=metadata or {}
        ))

    def _enrich_semantically(self, linked_entities: List[LinkedEntity]):
        """Enrich the graph by finding semantic relations between entity concepts."""
        for i, ent1 in enumerate(linked_entities):
            for ent2 in linked_entities[i+1:]:
                # Check for WordNet similarity
                similarity = self.semantic_graph.calculate_semantic_similarity(
                    ent1.entity.text, ent2.entity.text
                )
                
                if similarity > 0.7:  # High semantic relation
                    self.add_edge(
                        source=ent1.kb_id,
                        target=ent2.kb_id,
                        relation="semantically_similar",
                        confidence=similarity,
                        metadata={"source": "wordnet"}
                    )

    def to_mermaid(self, direction: str = "LR") -> str:
        """Export graph as a Mermaid diagram string."""
        lines = [f"graph {direction}"]
        
        # Node definitions with types (using Mermaid styles)
        for node in self.nodes.values():
            safe_label = node.label.replace('"', "'")
            # Style nodes by type
            bracket_open, bracket_close = ("[", "]")
            if node.type == EntityType.PERSON.value:
                bracket_open, bracket_close = ("(", ")")
            elif node.type == EntityType.ORGANIZATION.value:
                bracket_open, bracket_close = ("[[", "]]")
            
            lines.append(f'    {node.id}{bracket_open}"{safe_label}"{bracket_close}')
            
        # Edge definitions
        for edge in self.edges:
            lines.append(f'    {edge.source} -- "{edge.relation}" --> {edge.target}')
            
        return "\n".join(lines)

    def to_json(self) -> str:
        """Export graph as JSON (D3 format)."""
        data = {
            "nodes": [asdict(n) for n in self.nodes.values()],
            "links": [asdict(e) for e in self.edges]
        }
        return json.dumps(data, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level graph statistics."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "node_types": self._get_type_distribution(),
            "central_entities": self._get_central_entities()
        }

    def _get_type_distribution(self) -> Dict[str, int]:
        dist = {}
        for node in self.nodes.values():
            dist[node.type] = dist.get(node.type, 0) + 1
        return dist

    def _get_central_entities(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Calculate degree centrality (simple count of edges per node)."""
        counts = {}
        for edge in self.edges:
            counts[edge.source] = counts.get(edge.source, 0) + 1
            counts[edge.target] = counts.get(edge.target, 0) + 1
            
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:top_n]
