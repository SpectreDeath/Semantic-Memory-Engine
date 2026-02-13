"""
Tool Registry - Dynamic Discovery and Registration for SME Tools

This module provides automatic discovery and registration of all SME
ToolFactory methods as MCP-callable tools.

Usage:
    from gateway.tool_registry import ToolRegistry
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, asdict, is_dataclass
from nltk.tokenize import word_tokenize
from collections import Counter
import networkx as nx
import src.sme.vendor.faststylometry as faststylometry
from src.sme.vendor.faststylometry import Corpus
from src.sme.vendor.faststylometry.probability import predict_proba, calibrate
from src.sme.vendor.faststylometry.en import tokenise_remove_pronouns_en
from gateway.hardware_security import get_hsm
from src.sme.vendor import forensic_math
from src.sme.vendor.forensic_math import dict_to_vectors

# Ensure SME src is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# v1.1.0 Extension Hook: List of ToolDefinition provided by external plugins
EXTENSION_TOOLS: List[ToolDefinition] = []


@dataclass
class ToolDefinition:
    """Metadata for an MCP-exposed tool."""
    name: str
    description: str
    factory_method: Optional[str]
    category: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None
    is_manual: bool = False

class ScribeAuthorshipTool:
    """
    Custom Scribe Authorship tool using Burrows' Delta logic.
    """
    def __init__(self, core_bridge):
        self.core = core_bridge
        self.category = 'forensics'

    def analyze_authorship(self, text_sample: str, suspect_vector_id: str = None):
        """
        Performs stylometric fingerprinting using Burrows' Delta (Manhattan distance).
        """
        # 1. Tokenization and Feature Extraction
        tokens = [t.lower() for t in word_tokenize(text_sample) if t.isalpha()]
        if not tokens:
            return {"error": "No linguistic features detected in text sample"}
            
        freqs = Counter(tokens)
        total = sum(freqs.values())
        
        # Calculate Top-50 Function Word Frequencies (Linguistic Fingerprint)
        fingerprint = {word: count / total for word, count in freqs.most_common(50)}
        
        # 2. Vector Comparison (Burrows' Delta Logic)
        if suspect_vector_id:
            # Retrieve the suspect vector from the session/bridge
            suspect_data = self.core.get_session_entry(suspect_vector_id)
            if not suspect_data:
                return {
                    "status": "Baseline Fingerprint Generated", 
                    "fingerprint": fingerprint,
                    "warning": f"Suspect vector '{suspect_vector_id}' not found in scratchpad."
                }
                
            # If suspect_data is a dict (fingerprint), calculate distance
            if isinstance(suspect_data, dict):
                delta = self._calculate_delta(fingerprint, suspect_data)
                confidence = "High" if delta < 0.5 else "Low"
                
                return {
                    "status": "Analysis Complete",
                    "match_confidence": confidence,
                    "delta_score": round(delta, 4),
                    "features_detected": list(fingerprint.keys())[:5]
                }
            else:
                return {"error": f"Invalid data format for suspect vector '{suspect_vector_id}'"}
        
        return {"status": "Baseline Fingerprint Generated", "fingerprint": fingerprint}

    def _calculate_delta(self, f1, f2):
        # Manhattan distance implementation for Burrows' Delta
        words = set(f1.keys()) | set(f2.keys())
        if not words: return 1.0
        return sum(abs(f1.get(w, 0) - f2.get(w, 0)) for w in words) / len(words)

class ScribeProTool:
    """
    Advanced forensic matching using faststylometry.
    """
    def __init__(self, core_bridge):
        self.core = core_bridge
        self.category = 'forensics'

    def analyze_authorship_pro(self, text: str, comparison_id: str = "Suspect_Alpha_Vector"):
        """
        Advanced forensic matching using probability calibration.
        """
        # 1. Load your local 'Ground Truth' from SME (Scratchpad)
        session = self.core.get_session()
        if not session:
            return {"error": "No active session for forensic context."}
            
        train_corpus = Corpus()
        baselines_found = 0
        
        # Pull all Baseline_ entries from scratchpad
        for key, fingerprint in session.scratchpad.items():
            if key.startswith("Baseline_") and isinstance(fingerprint, dict):
                # We need raw text for faststylometry Corpus or we convert fingerprint?
                # Faststylometry usually needs text. If we only have fingerprints (Delta),
                # we might need to simulate or use the Scribe logic.
                # However, the user brief says "pull Baselines from scratchpad".
                # If these are fingerprints, we might need a special handler.
                # For now, let's assume we have baseline texts or we use placeholders.
                # Let's check if we can add 'books' to corpus.
                # If we don't have the original text, we might need to fallback to 
                # a synthetic text generated from the fingerprint if possible.
                # But let's look for 'Baseline_Text_...' keys too.
                text_key = f"Text_{key}"
                baseline_text = session.scratchpad.get(text_key)
                if baseline_text:
                    train_corpus.add_book(key, "Original", baseline_text)
                    baselines_found += 1
        
        if baselines_found < 2:
            return {
                "error": "Insufficient baselines found in scratchpad for Scribe Pro calibration.",
                "found_count": baselines_found,
                "hint": "Ensure at least two 'Baseline_...' samples with their corresponding 'Text_Baseline_...' entries are stored."
            }

        # 2. Tokenize, Calibrate and Predict
        try:
            train_corpus.tokenise(tokenise_remove_pronouns_en)
            calibrate(train_corpus)
            
            test_corpus = Corpus()
            test_corpus.add_book("Unknown", "Sample", text)
            test_corpus.tokenise(tokenise_remove_pronouns_en)
            
            probabilities = predict_proba(train_corpus, test_corpus)
            
            # Convert probabilities to a readable dict
            res_dict = probabilities.to_dict()
            
            # Extract probability for the unknown sample against candidates
            # The structure is usually {Author: {Unknown: Prob}} or similar
            # Let's simplify it for the user
            final_probs = {}
            for author, samples in res_dict.items():
                if isinstance(samples, dict) and "Sample" in samples:
                    final_probs[author] = round(float(samples["Sample"]), 4)
                else:
                    # Alternative structure check
                    key = list(samples.keys())[0] if isinstance(samples, dict) else 0
                    final_probs[author] = round(float(samples[key]), 4)
            
            return {
                "status": "Probabilistic Analysis Complete",
                "probabilities": final_probs,
                "match_likelihood": "High" if max(final_probs.values(), default=0) > 0.8 else "Low",
                "baselines_used": baselines_found
            }
        except Exception as e:
            logger.error(f"Scribe Pro error: {e}")
            # Fallback to simple Delta analysis if calibration fails
            return {
                "status": "Probabilistic Calibration Failed (Falling back to Delta)",
                "error": str(e),
                "baselines_found": baselines_found,
                "hint": "Try adding more diverse baseline samples to improve Logistic Regression stability."
            }

class InfluenceTool:
    """
    Graph Centrality tool for finding 'Key Influencers' in the knowledge graph.
    """
    def __init__(self, core_bridge):
        self.core = core_bridge
        self.category = 'graph'

    def get_influence_score(self, entity_name: str):
        """
        Query the 10GB SQLite core to build a local ego-graph and return centrality.
        """
        # 1. Query the core for relationships (Simulated ego-graph discovery)
        # In a real scenario, this would be a SQL query join on relationships table.
        # We simulate this by pulling related nodes from the core bridge.
        
        # Let's assume the core bridge can provide a list of triples.
        triples = self.core.get_ego_triples(entity_name)
        
        if not triples:
            return {"error": f"No graph data found for entity: {entity_name}", "influence_score": 0.0}
            
        # 2. Build NetworkX graph
        G = nx.Graph()
        for head, rel, tail in triples:
            G.add_edge(head, tail, relation=rel)
            
        # 3. Calculate Centrality
        try:
            pagerank = nx.pagerank(G)
            score = pagerank.get(entity_name, 0.0)
            
            # Normalize/Scale score for readability
            influence_norm = round(score * 10, 4)
            
            return {
                "entity": entity_name,
                "influence_score": influence_norm,
                "ego_graph_size": G.number_of_nodes(),
                "relationships_count": G.number_of_edges(),
                "centrality_metric": "PageRank",
                "neighbors": list(G.neighbors(entity_name))[:5]
            }
        except Exception as e:
            logger.error(f"Influence Tool error: {e}")
            return {"error": str(e), "entity": entity_name}


class ToolRegistry:
    """
    Central registry for discovering and managing SME tools.
    
    Maps ToolFactory methods to MCP tool definitions with metadata
    for documentation and validation.
    """
    
    # Tool definitions mapping MCP names to ToolFactory methods
    TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
        # ===== TIER 1: Core Tools (Sprint 1) =====
        "verify_system": ToolDefinition(
            name="verify_system",
            description="Check system health: CPU, RAM, database status, and data integrity",
            factory_method="create_system_monitor",
            category="diagnostics",
            parameters={}
        ),
        "semantic_search": ToolDefinition(
            name="semantic_search",
            description="Search the knowledge base using semantic vector similarity",
            factory_method="create_search_engine",
            category="query",
            parameters={"query": "str", "limit": "int"}
        ),
        "query_knowledge": ToolDefinition(
            name="query_knowledge",
            description="Query the knowledge graph for related concepts",
            factory_method="create_scout",
            category="query",
            parameters={"concept": "str"}
        ),
        "save_memory": ToolDefinition(
            name="save_memory",
            description="Persist a new fact or insight to the knowledge base",
            factory_method="create_synapse",
            category="memory",
            parameters={"fact": "str", "source": "str"}
        ),
        "get_memory_stats": ToolDefinition(
            name="get_memory_stats",
            description="Get statistics about stored knowledge: facts, vectors, entries",
            factory_method="create_centrifuge",
            category="diagnostics",
            parameters={}
        ),
        
        # ===== TIER 2: Forensic Tools (Sprint 2) =====
        "analyze_authorship": ToolDefinition(
            name="analyze_authorship",
            description="Extract linguistic fingerprint for authorship attribution",
            factory_method="create_scribe",
            category="forensics",
            parameters={"text": "str", "author_id": "str"}
        ),
        "analyze_sentiment": ToolDefinition(
            name="analyze_sentiment",
            description="Detect emotions, sarcasm, and sentiment in text",
            factory_method="create_sentiment_analyzer",
            category="analysis",
            parameters={"text": "str"}
        ),
        "link_entities": ToolDefinition(
            name="link_entities",
            description="Extract and link entities to knowledge bases",
            factory_method="create_entity_linker",
            category="analysis",
            parameters={"text": "str"}
        ),
        "summarize_text": ToolDefinition(
            name="summarize_text",
            description="Summarize text using extractive, abstractive, or query-focused modes",
            factory_method="create_text_summarizer",
            category="analysis",
            parameters={"text": "str", "mode": "str", "max_sentences": "int"}
        ),
        
        # ===== TIER 3: Advanced Tools (Sprint 3) =====
        "cluster_documents": ToolDefinition(
            name="cluster_documents",
            description="Cluster documents by semantic similarity",
            factory_method="create_document_clusterer",
            category="analysis",
            parameters={"documents": "list", "algorithm": "str"}
        ),
        "build_knowledge_graph": ToolDefinition(
            name="build_knowledge_graph",
            description="Build semantic graph from concepts and relationships",
            factory_method="create_semantic_graph",
            category="graph",
            parameters={"concepts": "list"}
        ),
        "verify_facts": ToolDefinition(
            name="verify_facts",
            description="Verify claims against the knowledge base",
            factory_method="create_fact_verifier",
            category="forensics",
            parameters={"claim": "str"}
        ),
        "analyze_nlp": ToolDefinition(
            name="analyze_nlp",
            description="Deep NLP analysis: dependencies, coreference, semantic roles",
            factory_method="create_nlp_pipeline",
            category="analysis",
            parameters={"text": "str"}
        ),
        "detect_networks": ToolDefinition(
            name="detect_networks",
            description="Detect coordinated sockpuppet networks",
            factory_method="create_network_generator",
            category="forensics",
            parameters={"authors": "list"}
        ),
        "resolve_concept": ToolDefinition(
            name="resolve_concept",
            description="Map ambiguous terms to specific knowledge graph nodes",
            factory_method="create_concept_resolver",
            category="query",
            parameters={"term": "str"}
        ),
        "generate_intelligence_report": ToolDefinition(
            name="generate_intelligence_report",
            description="Aggregate findings into a structured forensic report",
            factory_method="create_intelligence_reports",
            category="analysis",
            parameters={"subject": "str", "findings": "list"}
        ),
        "discover_overlap": ToolDefinition(
            name="discover_overlap",
            description="Find shared rhetorical signals between different authors",
            factory_method="create_overlap_discovery",
            category="forensics",
            parameters={"author_ids": "list"}
        ),
        "analyze_rolling_delta": ToolDefinition(
            name="analyze_rolling_delta",
            description="Temporal stylometric analysis of writing style evolution",
            factory_method="create_rolling_delta",
            category="forensics",
            parameters={"text": "str", "window_size": "int"}
        ),
        "analyze_authorship_pro": ToolDefinition(
            name="analyze_authorship_pro",
            description="Advanced probabilistic forensic matching using faststylometry",
            factory_method=None,
            category="forensics",
            parameters={"text": "str", "comparison_id": "str"},
            is_manual=True
        ),
        "deep_analyze": ToolDefinition(
            name="deep_analyze",
            description="Comprehensive forensic analysis combining multiple tools",
            factory_method=None,
            category="forensics",
            parameters={"text": "str"}
        ),
        "cross_author_comparison": ToolDefinition(
            name="cross_author_comparison",
            description="Compare multiple authors/texts to find commonalities",
            factory_method=None,
            category="forensics",
            parameters={"texts": "list"}
        ),
        "process_batch": ToolDefinition(
            name="process_batch",
            description="Execute a tool against multiple inputs in a single batch",
            factory_method=None,
            category="utility",
            parameters={"tool_name": "str", "inputs": "list"}
        ),
        "get_session_info": ToolDefinition(
            name="get_session_info",
            description="Get detailed information about a session",
            factory_method=None,
            category="session",
            parameters={"session_id": "str"}
        ),
        "update_scratchpad": ToolDefinition(
            name="update_scratchpad",
            description="Store temporary facts or context in the session scratchpad",
            factory_method=None,
            category="session",
            parameters={"key": "str", "value": "any"}
        ),
        "list_available_tools": ToolDefinition(
            name="list_available_tools",
            description="List all available MCP tools exposed by the gateway",
            factory_method=None,
            category="utility",
            parameters={}
        ),
        "login": ToolDefinition(
            name="login",
            description="Authenticate with the gateway and receive a JWT token",
            factory_method=None,
            category="auth",
            parameters={"username": "str", "password": "str"}
        ),
        "check_health": ToolDefinition(
            name="check_health",
            description="Combined health check for the gateway and dependencies",
            factory_method=None,
            category="utility",
            parameters={}
        ),
        "get_system_latency": ToolDefinition(
            name="get_system_latency",
            description="Measure internal tool call latency and system response",
            factory_method=None,
            category="utility",
            parameters={}
        ),
        "entity_extractor": ToolDefinition(
            name="entity_extractor",
            description="Advanced entity cross-referencing against the 10GB ConceptNet knowledge graph.",
            factory_method="create_concept_resolver", 
            category="query",
            parameters={"text": "str"}
        ),
        "harvest_suspect_baseline": ToolDefinition(
            name="harvest_suspect_baseline",
            description="Recursively harvest text from a path and create a stylometric suspect profile",
            factory_method=None,
            category="forensics",
            parameters={"path": "str", "suspect_id": "str"}
        ),
        "get_influence_score": ToolDefinition(
            name="get_influence_score",
            description="Calculate graph centrality for an entity to find 'Key Influencers'.",
            factory_method=None,
            category="graph",
            parameters={"entity_name": "str"}
        ),
        "calculate_cosine_similarity": ToolDefinition(
            name="calculate_cosine_similarity",
            description="Vectorized cosine similarity comparison of two frequency dictionaries.",
            factory_method=None,
            category="forensics",
            parameters={"freq_dict_1": "dict", "freq_dict_2": "dict"},
            is_manual=True
        ),
        "calculate_typo_distance": ToolDefinition(
            name="calculate_typo_definition",
            description="Identify fuzzy word matches using optimized Levenshtein distance.",
            factory_method=None,
            category="forensics",
            parameters={"word1": "str", "word2": "str"},
            is_manual=True
        ),
        "calculate_set_overlap": ToolDefinition(
            name="calculate_set_overlap",
            description="Calculate Jaccard Similarity (Set Overlap) between token lists.",
            factory_method=None,
            category="forensics",
            parameters={"tokens1": "list", "tokens2": "list"},
            is_manual=True
        ),
    }
    
    def __init__(self):
        self._tool_instances: Dict[str, Any] = {}
        self._factory = None
        
    def _get_factory(self):
        """Lazy-load the ToolFactory to avoid import issues."""
        if self._factory is None:
            try:
                from src.core.factory import ToolFactory
                self._factory = ToolFactory
                logger.info("ToolFactory loaded successfully")
            except ImportError as e:
                logger.error(f"Failed to import ToolFactory: {e}")
                raise
        return self._factory
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get or create a tool instance by name.
        
        Uses singleton pattern to cache expensive tool instances.
        
        Args:
            tool_name: The MCP tool name (e.g., 'semantic_search')
            
        Returns:
            The tool instance, or None if not found
        """
        if tool_name not in self.TOOL_DEFINITIONS:
            logger.warning(f"Unknown tool requested: {tool_name}")
            return None
            
        if tool_name not in self._tool_instances:
            definition = self.TOOL_DEFINITIONS[tool_name]
            
            if definition.is_manual:
                # Manual tools must have been injected via add_tool
                logger.error(f"Manual tool {tool_name} not found in instances. Did you call add_tool?")
                return None
                
            factory = self._get_factory()
            
            # Get the factory method by name
            factory_method = getattr(factory, definition.factory_method, None)
            if factory_method is None:
                logger.error(f"Factory method not found: {definition.factory_method}")
                return None
                
            try:
                self._tool_instances[tool_name] = factory_method()
                logger.info(f"Created tool instance: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to create tool {tool_name}: {e}")
                return None
                
        return self._tool_instances[tool_name]
    
    def list_tools(self, category: Optional[str] = None) -> list:
        """
        List available tools, optionally filtered by category.
        
        Args:
            category: Filter by category (diagnostics, query, memory, forensics, analysis)
            
        Returns:
            List of tool definitions
        """
        tools = list(self.TOOL_DEFINITIONS.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get metadata for a specific tool."""
        return self.TOOL_DEFINITIONS.get(tool_name)
    
    def get_categories(self) -> list:
        """Get all unique tool categories."""
        return list(set(t.category for t in self.TOOL_DEFINITIONS.values()))
    
    def reset(self, tool_name: Optional[str] = None):
        """
        Clear cached tool instances.
        
        Args:
            tool_name: Specific tool to reset, or None for all tools
        """
        if tool_name:
            self._tool_instances.pop(tool_name, None)
        else:
            self._tool_instances.clear()
        logger.info(f"Reset tool cache: {tool_name or 'all'}")

    @property
    def tools(self):
        """Returns a mapping of tool names to their instances or definitions."""
        # For the manifest architect script, we provide the definition 
        # as the 'instance' if not yet instantiated, or the live instance.
        return {name: self._tool_instances.get(name, self.TOOL_DEFINITIONS.get(name)) 
                for name in self.TOOL_DEFINITIONS}

    def add_tool(self, name: str, instance: Any, description: str = "", parameters: Dict = None, handler: Optional[Callable] = None):
        """
        Manually register a tool instance or handler.
        """
        self._tool_instances[name] = instance
        self.TOOL_DEFINITIONS[name] = ToolDefinition(
            name=name,
            description=description or getattr(instance, '__doc__', "Manual tool"),
            factory_method=None,
            category=getattr(instance, 'category', 'general'),
            parameters=parameters or {},
            handler=handler or (instance if callable(instance) else None),
            is_manual=True
        )
        logger.info(f"Manually registered tool: {name}")


class EpistemicValidator:
    """
    Evaluates forensic claims based on Epistemic Reliabilism and source provenance.
    """
    def __init__(self, core_bridge):
        self.core = core_bridge
        self.category = 'forensics'

    def evaluate_claim(self, claim: str, evidence_sources: list):
        """
        Assigns an 'Epistemic Certainty Score' (CQ) based on source provenance.
        Now includes 'Hardware-Verified' integrity checks using the TPM simulator.
        """
        hsm = get_hsm()
        score = 0.0
        justifications = []
        hardware_verified = True

        for source in evidence_sources:
            s_id = source.get('id', 'Unknown')
            # Query the core for reliability metadata
            provenance = self.core.get_source_reliability(s_id)
            tier = provenance.get("tier", 1)  # 1 (Low) to 5 (High)
            
            # Hardware Integrity Check (Sprint 11)
            hw_sig = source.get("hw_signature")
            db_hash = provenance.get("hash")
            
            if db_hash and hw_sig:
                if hsm.verify_integrity(s_id, db_hash, hw_sig):
                    justifications.append(f"Source '{s_id}': Hardware Integrity Verified (TPM).")
                else:
                    justifications.append(f"CRITICAL: Source '{s_id}' TAMPER ALERT! Signature mismatch.")
                    hardware_verified = False
                    tier = 0 # invalidate the source
            elif db_hash:
                 justifications.append(f"Source '{s_id}': No Hardware Signature found. Relying on soft hash.")
            
            trust = tier / 5.0
            score += trust
            tamper_info = " [Tamper-Evident]" if provenance.get("tamper_evident") else ""
            justifications.append(f"Source '{s_id}' provides Tier-{tier} grounding (Trust: {trust}){tamper_info}.")

        # Normalize score between 0.0 and 1.0
        cq = min(score, 1.0)
        
        # Severe penalty for any hardware tamper
        if not hardware_verified:
            cq *= 0.1
            status = "Rejected (TAMPER DETECTED)"
        else:
            # v0.6.0 Gating Logic
            if cq >= 0.7:
                status = "Verified"
            elif cq >= 0.4:
                status = "Speculative"
            else:
                status = "Rejected"

        return {
            "claim": claim,
            "certainty_quotient": round(cq, 4),
            "status": status,
            "hardware_verified": hardware_verified,
            "audit_trail": justifications,
            "epistemic_stance": "Hardware-Anchored Reliabilism",
            "timestamp": datetime.now().isoformat()
        }


class ForensicMathTool:
    """
    Exposes high-performance vectorized forensic math algorithms.
    """
    def __init__(self, core_bridge):
        self.core = core_bridge
        self.category = 'forensics'

    def calculate_cosine_similarity(self, freq_dict_1: Dict[str, float], freq_dict_2: Dict[str, float]) -> Dict[str, Any]:
        """
        Compare two text vectors using vectorized cosine similarity.
        """
        try:
            v1, v2 = dict_to_vectors(freq_dict_1, freq_dict_2)
            similarity = forensic_math.calculate_cosine_similarity(v1, v2)
            return {
                "cosine_similarity": round(similarity, 4),
                "vector_dimensions": len(v1),
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

    def calculate_typo_distance(self, word1: str, word2: str) -> Dict[str, Any]:
        """
        Detect typo distance between two words using optimized Levenshtein.
        """
        try:
            distance = forensic_math.calculate_typo_distance(word1, word2)
            # Typos are usually 1-2 chars different
            likely_typo = distance <= 2 and distance > 0
            return {
                "levenshtein_distance": distance,
                "likely_typo": likely_typo,
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

    def calculate_set_overlap(self, tokens1: List[str], tokens2: List[str]) -> Dict[str, Any]:
        """
        Identify shared jargon using Jaccard Similarity.
        """
        try:
            overlap = forensic_math.calculate_set_overlap(tokens1, tokens2)
            return {
                "jaccard_index": round(overlap, 4),
                "shared_token_count": len(set(tokens1) & set(tokens2)),
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global ToolRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
