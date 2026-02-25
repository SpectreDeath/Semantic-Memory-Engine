"""
gateway/routers/intelligence.py
================================
Higher-order intelligence tools: document clustering, network detection,
cross-author comparison, knowledge-graph construction, intelligence report
generation, rolling delta analysis, batch processing, deep analysis,
red-team auditing, and evidence harvesting.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from gateway.routers.shared import (
    RedTeamRequest,
    HarvestRequest,
    make_safe_tool_call,
    serialize_result,
)

logger = logging.getLogger("lawnmower.intelligence")


def register(
    mcp: Any,
    sme_core: Any,
    registry: Any,
    session_manager: Any,
    metrics_manager: Any,
    epistemic_tool: Any,          # Injected from forensic.register()
) -> None:
    """Register intelligence and advanced analysis tools with the FastMCP instance."""

    safe_tool_call = make_safe_tool_call(registry, metrics_manager)

    @mcp.tool()
    def cluster_documents(
        documents: List[str],
        algorithm: str = "kmeans",
        session_id: Optional[str] = None,
    ) -> str:
        """Cluster a list of documents by semantic similarity."""
        logger.info(f"cluster_documents called: count={len(documents)} algo={algorithm}")
        result = safe_tool_call("cluster_documents", "cluster", documents, algorithm=algorithm)
        session = session_manager.get_session(session_id)
        session.add_history("cluster_documents", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def build_knowledge_graph(
        concepts: List[str], session_id: Optional[str] = None
    ) -> str:
        """Build a semantic graph from a list of concepts and their relationships."""
        logger.info(f"build_knowledge_graph called: count={len(concepts)}")
        result = safe_tool_call("build_knowledge_graph", "build", concepts)
        session = session_manager.get_session(session_id)
        session.add_history("build_knowledge_graph", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def verify_facts(claim: str, session_id: Optional[str] = None) -> str:
        """Verify a claim against the evidence in the knowledge base."""
        logger.info(f"verify_facts called: claim='{claim[:50]}...'")
        result = safe_tool_call("verify_facts", "verify", claim)
        session = session_manager.get_session(session_id)
        session.add_history("verify_facts", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def detect_networks(
        authors: List[str], session_id: Optional[str] = None
    ) -> str:
        """Detect coordinated sockpuppet networks or behavioral clusters among authors."""
        logger.info(f"detect_networks called: authors_count={len(authors)}")
        result = safe_tool_call("detect_networks", "analyze", authors)
        session = session_manager.get_session(session_id)
        session.add_history("detect_networks", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def generate_intelligence_report(
        subject: str, findings: List[str], session_id: Optional[str] = None
    ) -> str:
        """Aggregate forensic findings into a structured intelligence report."""
        logger.info(f"generate_intelligence_report: subject='{subject}' findings={len(findings)}")
        result = safe_tool_call(
            "generate_intelligence_report", "generate", subject, findings=findings
        )
        session = session_manager.get_session(session_id)
        result["session_id"] = session.session_id

        report_claim = (
            f"Forensic report for {subject} based on {len(findings)} primary findings."
        )
        epistemic_res = epistemic_tool.evaluate_claim(
            report_claim,
            [{"id": "Audit_DB_Main", "context": "Structured report generation"}],
        )
        result["epistemic_audit"] = epistemic_res
        result["certainty_quotient"] = epistemic_res["certainty_quotient"]
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def discover_overlap(
        author_ids: List[str], session_id: Optional[str] = None
    ) -> str:
        """Find shared rhetorical signals and style overlaps between multiple authors."""
        logger.info(f"discover_overlap called: count={len(author_ids)}")
        result = safe_tool_call("discover_overlap", "discover", author_ids)
        session = session_manager.get_session(session_id)
        session.add_history("discover_overlap", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def analyze_rolling_delta(
        text: str, window_size: int = 1000, session_id: Optional[str] = None
    ) -> str:
        """Perform temporal stylometric analysis to see how writing style evolves."""
        logger.info(f"analyze_rolling_delta: text_len={len(text)} window={window_size}")
        result = safe_tool_call("analyze_rolling_delta", "analyze", text, window_size=window_size)
        session = session_manager.get_session(session_id)
        session.add_history("analyze_rolling_delta", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def cross_author_comparison(
        texts: List[Dict[str, str]], session_id: Optional[str] = None
    ) -> str:
        """
        Compare multiple authors/texts to find commonalities and discrepancies.

        Args:
            texts: List of dicts with {"text": "...", "author_id": "..."}
        """
        logger.info(f"cross_author_comparison called: count={len(texts)}")

        results: dict = {
            "timestamp": datetime.now().isoformat(),
            "comparison_count": len(texts),
            "individual_fingerprints": [],
            "group_metrics": {},
        }

        author_ids = []
        for item in texts:
            text = item.get("text", "")
            aid = item.get("author_id", "unknown")
            author_ids.append(aid)
            fingerprint = safe_tool_call(
                "analyze_authorship", "extract_linguistic_fingerprint", text, author_id=aid
            )
            results["individual_fingerprints"].append({"author_id": aid, "fingerprint": fingerprint})

        results["group_metrics"]["overlap"] = safe_tool_call(
            "discover_overlap", "discover", author_ids
        )
        results["group_metrics"]["networks"] = safe_tool_call(
            "detect_networks", "analyze", author_ids
        )

        session = session_manager.get_session(session_id)
        session.add_history("cross_author_comparison", results)
        results["session_id"] = session.session_id
        return json.dumps(results, indent=2, default=str)

    @mcp.tool()
    def process_batch(
        tool_name: str, inputs: List[Any], session_id: Optional[str] = None
    ) -> str:
        """
        Execute a tool against multiple inputs in a single batch.

        Args:
            tool_name: Name of the tool to run
            inputs: List of inputs for the tool
            session_id: Optional session identifier
        """
        logger.info(f"process_batch called: tool={tool_name} count={len(inputs)}")

        results: dict = {
            "tool": tool_name,
            "batch_size": len(inputs),
            "timestamp": datetime.now().isoformat(),
            "results": [],
        }

        session = session_manager.get_session(session_id)

        method_map = {
            "authorship": "extract_linguistic_fingerprint",
            "search": "search",
            "query": "search",
            "save": "consolidate",
            "entities": "link_entities",
            "summarize": "summarize",
        }

        for idx, item in enumerate(inputs):
            try:
                registry_tool = registry.get_tool_info(tool_name)
                if not registry_tool:
                    res = {"index": idx, "error": f"Tool {tool_name} not found in registry"}
                else:
                    method = next(
                        (v for k, v in method_map.items() if k in tool_name), "analyze"
                    )
                    res = safe_tool_call(tool_name, method, item)
                    res["index"] = idx
                results["results"].append(res)
            except Exception as e:
                results["results"].append({"index": idx, "error": str(e)})

        session.add_history("process_batch", results)
        return json.dumps(results, indent=2, default=str)

    @mcp.tool()
    def deep_analyze(text: str, session_id: Optional[str] = None) -> str:
        """
        Perform comprehensive forensic analysis combining authorship, sentiment,
        entity extraction, and epistemic audit in a single call.

        Args:
            text: Text to analyze (minimum 100 characters)
            session_id: Optional session identifier
        """
        logger.info(f"deep_analyze called: text_len={len(text)}")

        if len(text) < 100:
            return json.dumps({
                "error": "Text too short for deep analysis",
                "minimum_chars": 100,
                "provided_chars": len(text),
            })

        results: dict = {
            "timestamp": datetime.now().isoformat(),
            "text_length": len(text),
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "analyses": {},
        }

        for name, tool_name, method, *args in [
            ("authorship", "analyze_authorship", "extract_linguistic_fingerprint", text),
            ("sentiment", "analyze_sentiment", "analyze", text),
            ("entities", "link_entities", "link_entities", text),
        ]:
            try:
                results["analyses"][name] = safe_tool_call(tool_name, method, *args)
            except Exception as e:
                results["analyses"][name] = {"error": str(e)}

        if len(text) > 200:
            try:
                results["analyses"]["summary"] = safe_tool_call(
                    "summarize_text", "summarize", text, ratio=0.3
                )
            except Exception as e:
                results["analyses"]["summary"] = {"error": str(e)}

        lead_claim = f"Fingerprint analysis of {len(text)} chars indicates specific authorship matches."
        epistemic_res = epistemic_tool.evaluate_claim(
            lead_claim,
            [{"id": "System_Audit", "context": "Automatic deep analysis triggered"}],
        )
        results["epistemic_audit"] = epistemic_res
        results["certainty_quotient"] = epistemic_res["certainty_quotient"]

        session = session_manager.get_session(session_id)
        session.add_history("deep_analyze", results)
        results["session_id"] = session.session_id
        return json.dumps(results, indent=2, default=str)

    @mcp.tool()
    def red_team_audit(
        request: RedTeamRequest, session_id: Optional[str] = None
    ) -> str:
        """
        Stress-test the authorship engine using adversarial mimicry samples.
        Returns recommended thresholds for CQ gating.
        """
        from gateway.scripts.red_team import AdversarialGenerator, ThresholdTuner

        # Import the authorship_pro tool's underlying function via the registry
        authorship_pro_reg = registry.get_tool("analyze_authorship_pro")
        analyze_fn = authorship_pro_reg.analyze_authorship_pro if authorship_pro_reg else None

        gen = AdversarialGenerator()
        tuner = ThresholdTuner(analyze_fn)

        attacks = [
            gen.generate_mimicry(request.text, intensity=i / 10.0)
            for i in range(1, request.iterations + 1)
        ]
        recommended = tuner.tune_threshold(request.text, attacks, session_id=session_id)

        result = {
            "baseline_text": request.text[:100] + "...",
            "iterations": request.iterations,
            "recommended_threshold": recommended,
            "status": "Red-Team Stress Test Complete",
            "timestamp": datetime.now().isoformat(),
        }

        if session_id:
            session = session_manager.get_session(session_id)
            session._log_to_db("red_team_audit", result)

        return json.dumps(result, indent=2)

    @mcp.tool()
    def harvest_suspect_baseline(
        request: HarvestRequest, session_id: Optional[str] = None
    ) -> str:
        """
        Recursively harvest text from a path, redact it, and create a stylometric
        suspect profile. Stores the profile in the unified Nexus database.
        """
        from gateway.harvester import EvidenceHarvester
        from gateway.nexus_db import get_nexus

        harvester = EvidenceHarvester()
        nexus = get_nexus()

        try:
            fingerprint = harvester.harvest(request.path)
        except Exception as e:
            return json.dumps({"error": f"Harvest failed: {str(e)}", "path": request.path})

        nexus.execute("""
            CREATE TABLE IF NOT EXISTS lab.suspect_baselines (
                suspect_id TEXT PRIMARY KEY,
                total_tokens INTEGER,
                vocabulary_size INTEGER,
                fingerprint_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        nexus.execute("""
            INSERT OR REPLACE INTO lab.suspect_baselines
                (suspect_id, total_tokens, vocabulary_size, fingerprint_json)
            VALUES (?, ?, ?, ?)
        """, (
            request.suspect_id,
            fingerprint["total_tokens"],
            fingerprint["vocabulary_size"],
            json.dumps(fingerprint),
        ))

        result = {
            "suspect_id": request.suspect_id,
            "total_tokens_harvested": fingerprint["total_tokens"],
            "vocabulary_size": fingerprint["vocabulary_size"],
            "status": "Baseline Harvested & Vaulted in Nexus",
            "timestamp": datetime.now().isoformat(),
        }

        if session_id:
            session = session_manager.get_session(session_id)
            session.update_scratchpad(f"Baseline_{request.suspect_id}", result)
            session._log_to_db("harvest_suspect_baseline", result)

        return json.dumps(result, indent=2)
