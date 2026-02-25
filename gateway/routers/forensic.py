"""
gateway/routers/forensic.py
============================
Authorship, math, file-integrity, behavior, graph, signal, entropy,
crawler, and scorer tools — plus the autonomous audit pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from gateway.routers.shared import (
    AuthorshipProRequest,
    InfluenceRequest,
    JustifyRequest,
    WitnessStatementRequest,
    AutonomousAuditRequest,
    make_safe_tool_call,
    serialize_result,
)
from gateway.tool_registry import (
    ScribeAuthorshipTool,
    ScribeProTool,
    InfluenceTool,
    EpistemicValidator,
    ForensicMathTool,
    ForensicFilesTool,
    ForensicBehaviorTool,
    ForensicGraphTool,
    ForensicSignalTool,
    ForensicEntropyTool,
    ForensicCrawlerTool,
    ForensicScorerTool,
)
from gateway.scripts.report_generator import ReportGenerator
from gateway.scripts.forensic_planner import ForensicPlanner

logger = logging.getLogger("lawnmower.forensic")


def register(
    mcp: Any,
    sme_core: Any,
    registry: Any,
    session_manager: Any,
    metrics_manager: Any,
) -> EpistemicValidator:
    """
    Register all forensic tools with the FastMCP instance.

    Returns the instantiated EpistemicValidator so the intelligence router
    can reference it for cross-domain epistemic auditing.
    """
    safe_tool_call = make_safe_tool_call(registry, metrics_manager)

    # --- Instantiate tool objects ---
    scribe_tool = ScribeAuthorshipTool(sme_core)
    scribe_pro_tool = ScribeProTool(sme_core)
    influence_tool = InfluenceTool(sme_core)
    epistemic_tool = EpistemicValidator(sme_core)
    math_tool = ForensicMathTool(sme_core)
    files_tool = ForensicFilesTool(sme_core)
    behavior_tool = ForensicBehaviorTool(sme_core)
    graph_tool = ForensicGraphTool(sme_core)
    signal_tool = ForensicSignalTool(sme_core)
    entropy_tool = ForensicEntropyTool(sme_core)
    crawler_tool = ForensicCrawlerTool(sme_core)
    scorer_tool = ForensicScorerTool(sme_core)

    # --- Register in ToolRegistry for safe_tool_call look-ups ---
    registry.add_tool(
        "analyze_authorship", scribe_tool,
        description="Performs stylometric fingerprinting using Burrows' Delta logic.",
        parameters={"text": "str", "suspect_vector_id": "str"},
    )
    registry.add_tool(
        "analyze_authorship_pro", scribe_pro_tool,
        description="Advanced probabilistic forensic matching using faststylometry.",
        parameters=AuthorshipProRequest.model_json_schema(),
    )
    registry.add_tool(
        "get_influence_score", influence_tool,
        description="Calculate graph centrality for an entity in the knowledge graph.",
        parameters=InfluenceRequest.model_json_schema(),
    )
    registry.add_tool(
        "justify_claim", epistemic_tool,
        description="Audit a forensic lead using Epistemic Reliabilism and source provenance.",
        parameters=JustifyRequest.model_json_schema(),
    )
    registry.add_tool(
        "calculate_cosine_similarity", math_tool,
        description="Vectorized cosine similarity comparison of two frequency dictionaries.",
        parameters={"freq_dict_1": "dict", "freq_dict_2": "dict"},
    )
    registry.add_tool(
        "calculate_typo_distance", math_tool,
        description="Identify fuzzy word matches using optimized Levenshtein distance.",
        parameters={"word1": "str", "word2": "str"},
    )
    registry.add_tool(
        "calculate_set_overlap", math_tool,
        description="Calculate Jaccard Similarity (Set Overlap) between token lists.",
        parameters={"tokens1": "list", "tokens2": "list"},
    )
    registry.add_tool(
        "calculate_tfidf", math_tool,
        description="Calculate term significance (TF-IDF) across a corpus of documents.",
        parameters={"tokenized_docs": "list"},
    )
    registry.add_tool(
        "calculate_kl_divergence", math_tool,
        description="Measure relative entropy (KL Divergence) between two distributions.",
        parameters={"p": "list", "q": "list"},
    )
    registry.add_tool(
        "calculate_phonetic_hash", math_tool,
        description="Phonetic hashing using Double Metaphone for alias discovery.",
        parameters={"word": "str"},
    )
    registry.add_tool(
        "audit_benford_distribution", math_tool,
        description="Fraud detection using Benford's Law distribution analysis.",
        parameters={"data": "list"},
    )
    registry.add_tool(
        "calculate_simhash", math_tool,
        description="Locality Sensitive Hashing (SimHash) for near-duplicate detection.",
        parameters={"tokens": "list", "hash_size": "int"},
    )
    registry.add_tool(
        "calculate_entropy_divergence", math_tool,
        description="Measure relative entropy (Data Drift) between two distributions.",
        parameters={"p": "list", "q": "list"},
    )
    registry.add_tool(
        "verify_file_signature", files_tool,
        description="Verify file integrity by checking magic numbers.",
        parameters={"file_path": "str"},
    )
    registry.add_tool(
        "calculate_structural_complexity", files_tool,
        description="Calculate compression ratio as a proxy for structural entropy.",
        parameters={"file_path": "str"},
    )
    registry.add_tool(
        "calculate_burstiness", behavior_tool,
        description="Calculate temporal burstiness score from a list of timestamps.",
        parameters={"timestamps": "list"},
    )
    registry.add_tool(
        "validate_luhn_checksum", behavior_tool,
        description="Detect PII leakage (Cards/SSNs) using Luhn algorithm validation.",
        parameters={"numeric_string": "str"},
    )
    registry.add_tool(
        "calculate_node_path", graph_tool,
        description="Find the shortest path between nodes in a relationship graph.",
        parameters={"graph": "dict", "start_node": "str", "end_node": "str"},
    )
    registry.add_tool(
        "identify_central_hubs", graph_tool,
        description="Identify influential nodes using Eigenvector Centrality.",
        parameters={"adjacency_matrix": "list", "node_labels": "list"},
    )
    registry.add_tool(
        "calculate_sequence_similarity", signal_tool,
        description="Find similarity between time-series sequences using DTW.",
        parameters={"seq1": "list", "seq2": "list"},
    )
    registry.add_tool(
        "detect_event_periodicity", signal_tool,
        description="Identify dominant periodicities in numerical event logs using DFT.",
        parameters={"data": "list"},
    )
    registry.add_tool(
        "map_stream_entropy", entropy_tool,
        description="Map Shannon entropy across a byte-stream using a sliding window.",
        parameters={"stream": "list", "window_size": "int"},
    )
    registry.add_tool(
        "analyze_obfuscation_score", entropy_tool,
        description="Detect obfuscated scripts using Hamming Weight and Compression complexity.",
        parameters={"content": "str"},
    )
    registry.add_tool(
        "ingest_forensic_target", crawler_tool,
        description="Fetch a URL, extract clean prose, and generate stylometric fingerprints.",
        parameters={"url": "str"},
    )
    registry.add_tool(
        "get_forensic_report", scorer_tool,
        description="Generate a high-fidelity forensic credibility report with visualization data.",
        parameters={"target_text": "str"},
    )

    # ======================================================================
    # MCP Tool Registrations
    # ======================================================================

    @mcp.tool()
    def analyze_authorship(
        text: str,
        suspect_vector_id: str = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Extract linguistic fingerprint for authorship attribution using Burrows' Delta.

        Args:
            text: The text sample to analyze
            suspect_vector_id: Optional ID of a suspect fingerprint in the scratchpad
            session_id: Optional session identifier
        """
        logger.info(f"analyze_authorship called (session={session_id})")
        scribe_tool.core.session_id = session_id
        result = scribe_tool.analyze_authorship(text, suspect_vector_id)
        session = session_manager.get_session(session_id)
        session.add_history("analyze_authorship", result)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def analyze_authorship_pro(
        request: AuthorshipProRequest, session_id: Optional[str] = None
    ) -> str:
        """Advanced probabilistic forensic matching using faststylometry."""
        if isinstance(request, dict):
            request = AuthorshipProRequest(**request)
        logger.info(f"analyze_authorship_pro called (session={session_id})")
        scribe_pro_tool.core.session_id = session_id
        result = scribe_pro_tool.analyze_authorship_pro(request.text, request.comparison_id)
        session = session_manager.get_session(session_id)
        session.add_history("analyze_authorship_pro", result)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def get_influence_score(
        request: InfluenceRequest, session_id: Optional[str] = None
    ) -> str:
        """Calculate graph centrality for an entity in the knowledge graph."""
        if isinstance(request, dict):
            request = InfluenceRequest(**request)
        logger.info(f"get_influence_score called for: {request.entity_name}")
        influence_tool.core.session_id = session_id
        result = influence_tool.get_influence_score(request.entity_name)
        session = session_manager.get_session(session_id)
        session.add_history("get_influence_score", result)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def justify_claim(
        request: JustifyRequest, session_id: Optional[str] = None
    ) -> str:
        """Perform an Epistemological Audit of a forensic claim."""
        if isinstance(request, dict):
            request = JustifyRequest(**request)
        logger.info(f"justify_claim called for: {request.claim[:50]}...")
        epistemic_tool.core.session_id = session_id
        result = epistemic_tool.evaluate_claim(request.claim, request.evidence_sources)
        session = session_manager.get_session(session_id)
        session.add_history("justify_claim", result)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def generate_witness_statement(
        request: WitnessStatementRequest, session_id: Optional[str] = None
    ) -> str:
        """Generate a formal Digital Forensic Witness Statement (Markdown)."""
        if isinstance(request, dict):
            request = WitnessStatementRequest(**request)
        logger.info(f"generate_witness_statement called for case: {request.case_id}")
        sme_core.session_id = session_id
        generator = ReportGenerator(session_id, sme_core, epistemic_tool)
        result = generator.generate(case_id=request.case_id)
        session = session_manager.get_session(session_id)
        session.add_history("generate_witness_statement", result)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def autonomous_audit(
        request: AutonomousAuditRequest, session_id: Optional[str] = None
    ) -> str:
        """Run an end-to-end automated forensic investigation."""
        logger.info(f"autonomous_audit called for case: {request.case_id}")
        sme_core.session_id = session_id
        # Pass .fn references to the planner so it can call them directly
        mcp_tools = {
            "analyze_authorship_pro": analyze_authorship_pro.fn,
            "get_influence_score": get_influence_score.fn,
            "justify_claim": justify_claim.fn,
            "generate_witness_statement": generate_witness_statement.fn,
        }
        planner = ForensicPlanner(mcp_tools, session_manager)
        result = planner.run_investigation(request.text, request.case_id, session_id)
        return json.dumps(result, indent=2)

    # --- Math tools ---

    @mcp.tool()
    def calculate_cosine_similarity(
        freq_dict_1: Dict[str, float],
        freq_dict_2: Dict[str, float],
        session_id: Optional[str] = None,
    ) -> str:
        """Vectorized cosine similarity comparison of two frequency dictionaries."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_cosine_similarity(freq_dict_1, freq_dict_2), indent=2)

    @mcp.tool()
    def calculate_typo_distance(
        word1: str, word2: str, session_id: Optional[str] = None
    ) -> str:
        """Identify fuzzy word matches using optimized Levenshtein distance."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_typo_distance(word1, word2), indent=2)

    @mcp.tool()
    def calculate_set_overlap(
        tokens1: List[str], tokens2: List[str], session_id: Optional[str] = None
    ) -> str:
        """Calculate Jaccard Similarity (Set Overlap) between token lists."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_set_overlap(tokens1, tokens2), indent=2)

    @mcp.tool()
    def calculate_tfidf(
        tokenized_docs: List[List[str]], session_id: Optional[str] = None
    ) -> str:
        """Calculate term significance (TF-IDF) across a corpus of documents."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_tfidf(tokenized_docs), indent=2)

    @mcp.tool()
    def calculate_kl_divergence(
        p: List[float], q: List[float], session_id: Optional[str] = None
    ) -> str:
        """Measure relative entropy (KL Divergence) between two distributions."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_kl_divergence(p, q), indent=2)

    @mcp.tool()
    def calculate_phonetic_hash(word: str, session_id: Optional[str] = None) -> str:
        """Phonetic hashing using Double Metaphone for alias discovery."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_phonetic_hash(word), indent=2)

    @mcp.tool()
    def audit_benford_distribution(
        data: List[float], session_id: Optional[str] = None
    ) -> str:
        """Fraud detection using Benford's Law distribution analysis."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.audit_benford_distribution(data), indent=2)

    @mcp.tool()
    def calculate_simhash(
        tokens: List[str], hash_size: int = 64, session_id: Optional[str] = None
    ) -> str:
        """Locality Sensitive Hashing (SimHash) for near-duplicate detection."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_simhash(tokens, hash_size), indent=2)

    @mcp.tool()
    def calculate_entropy_divergence(
        p: List[float], q: List[float], session_id: Optional[str] = None
    ) -> str:
        """Measure relative entropy (Data Drift) between two distributions."""
        math_tool.core.session_id = session_id
        return json.dumps(math_tool.calculate_entropy_divergence(p, q), indent=2)

    # --- File tools ---

    @mcp.tool()
    def verify_file_signature(file_path: str, session_id: Optional[str] = None) -> str:
        """Verify file integrity by checking magic numbers."""
        files_tool.core.session_id = session_id
        return json.dumps(files_tool.verify_file_signature(file_path), indent=2)

    @mcp.tool()
    def calculate_structural_complexity(
        file_path: str, session_id: Optional[str] = None
    ) -> str:
        """Calculate compression ratio as structural entropy proxy."""
        files_tool.core.session_id = session_id
        return json.dumps(files_tool.calculate_structural_complexity(file_path), indent=2)

    # --- Behavior tools ---

    @mcp.tool()
    def calculate_burstiness(
        timestamps: List[float], session_id: Optional[str] = None
    ) -> str:
        """Calculate temporal burstiness score."""
        behavior_tool.core.session_id = session_id
        return json.dumps(behavior_tool.calculate_burstiness(timestamps), indent=2)

    @mcp.tool()
    def validate_luhn_checksum(
        numeric_string: str, session_id: Optional[str] = None
    ) -> str:
        """Validate numeric leakage via Luhn algorithm."""
        behavior_tool.core.session_id = session_id
        return json.dumps(behavior_tool.validate_luhn_checksum(numeric_string), indent=2)

    # --- Graph tools ---

    @mcp.tool()
    def calculate_node_path(
        graph: dict,
        start_node: str,
        end_node: str,
        session_id: Optional[str] = None,
    ) -> str:
        """Find the shortest path between nodes in a relationship graph."""
        graph_tool.core.session_id = session_id
        return json.dumps(graph_tool.calculate_node_path(graph, start_node, end_node), indent=2)

    @mcp.tool()
    def identify_central_hubs(
        adjacency_matrix: List[List[float]],
        node_labels: List[str],
        session_id: Optional[str] = None,
    ) -> str:
        """Identify influential nodes using Eigenvector Centrality."""
        graph_tool.core.session_id = session_id
        return json.dumps(graph_tool.identify_central_hubs(adjacency_matrix, node_labels), indent=2)

    # --- Signal tools ---

    @mcp.tool()
    def calculate_sequence_similarity(
        seq1: List[float], seq2: List[float], session_id: Optional[str] = None
    ) -> str:
        """Find similarity between time-series sequences using DTW."""
        signal_tool.core.session_id = session_id
        return json.dumps(signal_tool.calculate_sequence_similarity(seq1, seq2), indent=2)

    @mcp.tool()
    def detect_event_periodicity(
        data: List[float], session_id: Optional[str] = None
    ) -> str:
        """Identify dominant periodicities via DFT."""
        signal_tool.core.session_id = session_id
        return json.dumps(signal_tool.detect_event_periodicity(data), indent=2)

    # --- Entropy tools ---

    @mcp.tool()
    def map_stream_entropy(
        stream: List[int], window_size: int = 256, session_id: Optional[str] = None
    ) -> str:
        """Map Shannon entropy across a byte-stream using a sliding window."""
        entropy_tool.core.session_id = session_id
        return json.dumps(entropy_tool.map_stream_entropy(stream, window_size), indent=2)

    @mcp.tool()
    def analyze_obfuscation_score(
        content: str, session_id: Optional[str] = None
    ) -> str:
        """Detect obfuscated scripts using Hamming Weight and Compression complexity."""
        entropy_tool.core.session_id = session_id
        return json.dumps(entropy_tool.analyze_obfuscation_score(content), indent=2)

    # --- Crawler + Scorer ---

    @mcp.tool()
    async def ingest_forensic_target(url: str, session_id: Optional[str] = None) -> str:
        """Fetch a URL, extract clean prose, and generate stylometric fingerprints."""
        crawler_tool.core.session_id = session_id
        result = await crawler_tool.ingest_forensic_target(url)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def get_forensic_report(target_text: str, session_id: Optional[str] = None) -> str:
        """Generate a high-fidelity forensic credibility report with visualization data."""
        scorer_tool.core.session_id = session_id
        return json.dumps(scorer_tool.get_forensic_report(target_text), indent=2)

    # Return epistemic_tool so other routers can reference it
    return epistemic_tool
