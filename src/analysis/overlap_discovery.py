"""
Overlap Discovery Module
========================

Phase 6 component for detecting semantic overlaps across different context IDs.
Uses SemanticMemory (ChromaDB) to find similar concepts across the database.

Features:
- Cross-context semantic similarity search
- Identification of "hidden connections" between documents
- Clustered view of related concepts from different sources
- Connection strength scoring
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from src.core.factory import ToolFactory

logger = logging.getLogger(__name__)


@dataclass
class SemanticConnection:
    """Represents a semantic link between two documents/contexts."""
    source_context: str
    target_context: str
    similarity_score: float
    overlapping_concepts: List[str]
    sample_text: str


class OverlapDiscovery:
    """
    Discovers semantic overlaps and hidden connections across the laboratory memory.
    """
    
    def __init__(self):
        """Initialize with semantic memory."""
        self.semantic_db = ToolFactory.create_semantic_db()
        logger.info("OverlapDiscovery engine initialized")

    def find_connections(self, context_id: str, limit: int = 5) -> List[SemanticConnection]:
        """
        Find other contexts that overlap semantically with the given context.
        
        Args:
            context_id: The context to search around
            limit: Max number of connections to return
        """
        if not self.semantic_db:
            logger.warning("Semantic DB not available for overlap discovery")
            return []

        # 1. Get representative embeddings for the source context
        source_data = self.semantic_db.get_by_context(context_id)
        if not source_data or not source_data.get('documents'):
            logger.info(f"No data found for context {context_id}")
            return []

        # 2. Search for similar documents in other contexts
        # We take a sample of documents from the source to query with
        connections = []
        seen_contexts = {context_id}
        
        for doc_text in source_data['documents'][:3]: # Sample 3 documents
            results = self.semantic_db.search(doc_text, limit=limit * 2)
            
            for i, target_doc in enumerate(results.get('documents', [[]])[0]):
                target_meta = results.get('metadatas', [[]])[0][i]
                target_context = target_meta.get('context_id', 'unknown')
                distance = results.get('distances', [[]])[0][i]
                
                # Convert distance to similarity (simplified)
                similarity = 1.0 - (distance / 2.0)
                
                if target_context not in seen_contexts and similarity > 0.7:
                    connections.append(SemanticConnection(
                        source_context=context_id,
                        target_context=target_context,
                        similarity_score=similarity,
                        overlapping_concepts=target_meta.get('keywords', []),
                        sample_text=target_doc[:100] + "..."
                    ))
                    seen_contexts.add(target_context)
                    
                if len(connections) >= limit:
                    break
            
            if len(connections) >= limit:
                break
                
        return sorted(connections, key=lambda x: x.similarity_score, reverse=True)

    def discover_all_hubs(self) -> Dict[str, List[str]]:
        """
        Find 'hubs' - contexts that have many connections to others.
        (Conceptual implementation)
        """
        # In a real implementation, this would iterate through popular keywords
        # and see which contexts share them most frequently.
        return {"hubs_discovery": "experimental"}
