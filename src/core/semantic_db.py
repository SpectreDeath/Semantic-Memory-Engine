import chromadb
from chromadb.utils import embedding_functions
from src.core.utils import get_path
from src.core.semantic_graph import SemanticGraph
from src.core.tenancy import get_tenant_collection_name
import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SemanticMemory:
    def __init__(self, collection_name="laboratory_memories"):
        self.db_path = get_path('storage', 'base_dir') + "/chroma_db"
        self.client = chromadb.PersistentClient(path=self.db_path)
        # Using a default local embedding function
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        # Get tenant-specific collection name
        tenant_collection = get_tenant_collection_name(collection_name)
        
        self.collection = self.client.get_or_create_collection(
            name=tenant_collection, 
            embedding_function=self.ef
        )
        
        # Initialize semantic graph for enhanced relationships
        self.semantic_graph = SemanticGraph()
        self._fact_index: Set[str] = set()  # Track stored facts

    def add_fact(self, fact_id: str, fact_text: str, metadata: Optional[Dict] = None):
        """Adds a fact to the vector database."""
        self.collection.add(
            documents=[fact_text],
            metadatas=[metadata or {}],
            ids=[fact_id]
        )
        self._fact_index.add(fact_id)

    def add_fact_with_semantics(
        self,
        fact_id: str,
        fact_text: str,
        extract_variants: bool = True,
        metadata: Optional[Dict] = None
    ):
        """
        Add a fact and automatically include its semantic variants.
        
        This enriches the memory by adding synonyms and related concepts,
        making future searches more effective through semantic connections.
        
        Args:
            fact_id: Unique identifier for the fact
            fact_text: The fact content
            extract_variants: Whether to extract and add semantic variants
            metadata: Optional metadata dictionary
        """
        # Add the main fact
        self.add_fact(fact_id, fact_text, metadata)
        
        if not extract_variants or not self.semantic_graph.is_available():
            return
        
        # Extract key terms and add semantic variants
        key_terms = self._extract_key_terms(fact_text)
        
        for term_idx, term in enumerate(key_terms):
            meaning = self.semantic_graph.explore_meaning(term)
            if not meaning:
                continue
            
            # Add synonyms with metadata
            for syn_idx, synonym in enumerate(meaning.synonyms[:3]):
                variant_id = f"{fact_id}_syn_{term_idx}_{syn_idx}"
                variant_text = f"Semantic variant of '{term}': {synonym}. From: {fact_text[:100]}..."
                self.add_fact(
                    variant_id,
                    variant_text,
                    metadata={
                        **(metadata or {}),
                        'related_to': fact_id,
                        'relation_type': 'synonym',
                        'original_term': term,
                        'variant': synonym
                    }
                )
            
            # Add hypernyms (broader concepts) with metadata
            for hyp_idx, hypernym in enumerate(meaning.hypernyms[:2]):
                variant_id = f"{fact_id}_hyp_{term_idx}_{hyp_idx}"
                variant_text = f"Broader concept of '{term}': {hypernym}. From: {fact_text[:100]}..."
                self.add_fact(
                    variant_id,
                    variant_text,
                    metadata={
                        **(metadata or {}),
                        'related_to': fact_id,
                        'relation_type': 'hypernym',
                        'original_term': term,
                        'broader_concept': hypernym
                    }
                )

    def search(self, query: str, n_results: int = 5) -> Dict:
        """Performs semantic search."""
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
    
    def search_with_semantic_expansion(
        self,
        query: str,
        n_results: int = 5,
        include_variants: bool = True
    ) -> Dict:
        """
        Perform semantic search with automatic query expansion.
        
        Automatically finds synonyms and related terms for the query,
        improving recall by searching for semantic variants.
        
        Args:
            query: The search query
            n_results: Number of results to return
            include_variants: Whether to expand query with variants
        
        Returns:
            Search results with enhanced relevance
        """
        results = self.search(query, n_results)
        
        if not include_variants or not self.semantic_graph.is_available():
            return results
        
        # Expand query with semantic variants
        expanded_queries = [query]
        
        # Extract key terms and find synonyms
        key_terms = self._extract_key_terms(query)
        for term in key_terms:
            meaning = self.semantic_graph.explore_meaning(term)
            if meaning:
                expanded_queries.extend(meaning.synonyms[:2])
        
        # Search with expanded queries and merge results
        all_results = results.copy()
        for expanded_query in expanded_queries[1:]:  # Skip original
            variant_results = self.search(expanded_query, n_results)
            # Merge results (simple deduplication)
            if 'ids' in variant_results and variant_results['ids']:
                for idx, doc_id in enumerate(variant_results['ids'][0]):
                    if doc_id not in all_results.get('ids', [[]])[0]:
                        all_results['ids'][0].append(doc_id)
                        if 'documents' in variant_results:
                            all_results['documents'][0].append(
                                variant_results['documents'][0][idx]
                            )
        
        # Limit to n_results
        if 'ids' in all_results and all_results['ids']:
            all_results['ids'][0] = all_results['ids'][0][:n_results]
            if 'documents' in all_results:
                all_results['documents'][0] = all_results['documents'][0][:n_results]
        
        return all_results

    def get_by_context(self, context_id: str) -> Dict:
        """
        Retrieve all documents associated with a specific context_id.
        """
        return self.collection.get(
            where={"context_id": context_id}
        )

    def find_clusters(self, threshold: float = 0.1) -> Dict:
        """
        Finds potential clusters (basic implementation via distance).
        
        Note: High-level abstraction for the 'Synapse' layer to use.
        In a real implementation, we'd use collection.get() and perform clustering.
        """
        # TODO: Implement clustering with semantic graph awareness
        pass
    
    def detect_semantic_gaps(
        self,
        central_concept: str,
        existing_facts: Optional[Set[str]] = None
    ) -> List[Dict]:
        """
        Detect knowledge gaps in memory by analyzing semantic relationships.
        
        Uses the semantic graph to find related concepts that haven't been
        stored yet, helping the system identify what information is missing.
        
        Args:
            central_concept: The main concept to analyze
            existing_facts: Set of fact IDs already in memory
        
        Returns:
            List of suggested gap fillers with priorities
        """
        if not self.semantic_graph.is_available():
            return []
        
        # Use existing facts or scan collection
        if existing_facts is None:
            existing_facts = self._fact_index
        
        # Get semantic gaps
        gaps = self.semantic_graph.detect_semantic_gaps(
            central_concept,
            existing_facts
        )
        
        return gaps
    
    def get_semantic_neighbors(
        self,
        concept: str,
        relation_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get all semantically related concepts for a given term.
        
        Args:
            concept: The concept to find neighbors for
            relation_type: Filter by type ('synonym', 'hypernym', 'hyponym', 'antonym')
        
        Returns:
            Dictionary of related concepts organized by relation type
        """
        if not self.semantic_graph.is_available():
            return {}
        
        variants = self.semantic_graph.find_semantic_variants(concept)
        
        if relation_type:
            return {relation_type: variants.get(relation_type, [])}
        
        return variants
    
    @staticmethod
    def _extract_key_terms(text: str) -> List[str]:
        """Extract key terms from text (simple noun extraction)."""
        # Simple approach: split and filter
        # In production, use POS tagging for better results
        words = text.lower().split()
        # Filter out common words and short terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are'}
        key_terms = [w.strip('.,!?;:') for w in words 
                     if w.lower() not in stop_words and len(w) > 3]
        return list(set(key_terms))  # Remove duplicates
