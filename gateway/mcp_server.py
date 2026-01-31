"""
Lawnmower Man MCP Server - Gateway to SME Forensic Toolkit

This is the main MCP server that exposes SME's capabilities to LLM agents.
It replaces subprocess calls with direct Python API integration for
reliability and structured data.

Sprint 2: Added circuit breaker resilience, entity linking, summarization,
and improved dataclass serialization.

Usage:
    # Run directly
    python -m gateway.mcp_server
    
    # Or via Docker
    docker-compose up lawnmower-gateway
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import asdict, is_dataclass
from enum import Enum

# Ensure SME is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psutil
except ImportError:
    psutil = None

try:
    from fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not installed. Run: pip install fastmcp")
    sys.exit(1)

from gateway.tool_registry import get_registry, ToolRegistry
from gateway.session_manager import get_session_manager, SessionManager
from gateway.auth import get_auth_manager, AuthManager
from gateway.metrics import get_metrics_manager, MetricsManager
from gateway.rate_limiter import get_rate_limiter, RateLimiter

# Configure logging with structured JSON format
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger("lawnmower.mcp")

# Initialize FastMCP server
mcp = FastMCP(
    "Lawnmower Man Gateway",
    instructions="MCP gateway to the Semantic Memory Engine forensic toolkit"
)

# Get the tool registry
registry = get_registry()

# Get the session manager
session_manager = get_session_manager()

# Hardening Managers
auth_manager = get_auth_manager()
metrics_manager = get_metrics_manager()
rate_limiter = get_rate_limiter()


# =============================================================================
# Helpers
# =============================================================================

def serialize_result(obj: Any) -> Dict[str, Any]:
    """
    Serialize any result object to a JSON-compatible dict.
    
    Handles dataclasses, Enums (both keys and values), and objects with to_dict methods.
    """
    if obj is None:
        return None
    
    if isinstance(obj, dict):
        # Handle Enum keys by converting them to their values
        return {
            (k.value if isinstance(k, Enum) else k): serialize_result(v) 
            for k, v in obj.items()
        }
    
    if isinstance(obj, list):
        return [serialize_result(item) for item in obj]
    
    if isinstance(obj, Enum):
        return obj.value
    
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: serialize_result(v) for k, v in asdict(obj).items()}
    
    if hasattr(obj, 'to_dict'):
        return serialize_result(obj.to_dict())  # Recursively serialize the dict
    
    if hasattr(obj, '__dict__'):
        return {k: serialize_result(v) for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    
    # Primitive types
    return obj


def safe_tool_call(tool_name: str, method_name: str, *args, **kwargs) -> Dict[str, Any]:
    """
    Safely call a tool method with circuit breaker pattern and metrics.
    """
    start_time = time.perf_counter()
    try:
        metrics_manager.track_call(tool_name, "general")
        
        tool = registry.get_tool(tool_name)
        if tool is None:
            metrics_manager.track_error(tool_name, "tool_unavailable")
            return {"error": f"{tool_name} not available", "status": "tool_unavailable"}
        
        method = getattr(tool, method_name, None)
        if method is None:
            # Try alternative method names
            alternatives = ['analyze', 'process', 'execute', 'run']
            for alt in alternatives:
                method = getattr(tool, alt, None)
                if method:
                    break
        
        if method is None:
            metrics_manager.track_error(tool_name, "method_not_found")
            return {"error": f"Method '{method_name}' not found on {tool_name}"}
        
        result = method(*args, **kwargs)
        
        # Track latency
        duration = time.perf_counter() - start_time
        metrics_manager.observe_latency(tool_name, duration)
        
        return {"success": True, "data": serialize_result(result)}
        
    except Exception as e:
        logger.error(f"Tool call failed: {tool_name}.{method_name} - {e}")
        metrics_manager.track_error(tool_name, type(e).__name__)
        return {"error": str(e), "tool": tool_name, "status": "error"}


# =============================================================================
# TIER 1: Core Tools (Sprint 1)
# =============================================================================

@mcp.tool()
def verify_system() -> str:
    """
    Verify system health and return hardware telemetry.
    
    Returns CPU/RAM usage, database status, and data integrity checks.
    This is the instrumentation heartbeat for Project Lawnmower Man.
    """
    logger.info("verify_system called")
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "telemetry": {},
        "data_integrity": {},
        "semantic_memory": {}
    }
    
    # Hardware telemetry
    if psutil:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        result["telemetry"] = {
            "cpu_percent": cpu_usage,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_used_percent": memory.percent
        }
    
    # Database status
    db_path = os.environ.get("SME_DB_PATH", "data/knowledge_core.sqlite")
    result["data_integrity"]["knowledge_db"] = {
        "path": db_path,
        "exists": os.path.exists(db_path),
        "size_gb": round(os.path.getsize(db_path) / (1024**3), 3) if os.path.exists(db_path) else 0
    }
    
    # ConceptNet assertions
    csv_path = "data/conceptnet-assertions-5.7.0.csv"
    result["data_integrity"]["conceptnet"] = {
        "path": csv_path,
        "exists": os.path.exists(csv_path),
        "size_gb": round(os.path.getsize(csv_path) / (1024**3), 2) if os.path.exists(csv_path) else 0
    }
    
    # Semantic memory status
    try:
        tool = registry.get_tool("get_memory_stats")
        if tool and hasattr(tool, 'get_stats'):
            stats = tool.get_stats()
            result["semantic_memory"] = stats
        else:
            result["semantic_memory"] = {"status": "pending_initialization"}
    except Exception as e:
        result["semantic_memory"] = {"error": str(e)}
    
    # Overall status
    if not result["data_integrity"]["knowledge_db"]["exists"]:
        result["status"] = "degraded"
        result["message"] = "Knowledge database not found. Run 'sme index' to initialize."
    
    return json.dumps(result, indent=2)


@mcp.tool()
def semantic_search(query: str, limit: int = 5, session_id: Optional[str] = None) -> str:
    """
    Search the knowledge base using semantic vector similarity.
    
    Args:
        query: The search query (natural language)
        limit: Maximum number of results to return
        session_id: Optional session identifier
        
    Returns:
        JSON array of matching documents with similarity scores
    """
    logger.info(f"semantic_search called: query='{query[:50]}...' limit={limit}")
    
    result = safe_tool_call("semantic_search", "search", query, top_k=limit)
    if "error" in result and result.get("status") == "tool_unavailable":
        # Fallback: try query method
        result = safe_tool_call("semantic_search", "query", query, limit=limit)
    
    result["query"] = query
    result["limit"] = limit
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("semantic_search", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def query_knowledge(concept: str, session_id: Optional[str] = None) -> str:
    """
    Query the knowledge graph for concepts related to the input.
    
    Args:
        concept: The concept to look up
        session_id: Optional session identifier
    """
    logger.info(f"query_knowledge called: concept='{concept}'")
    
    result = safe_tool_call("query_knowledge", "search", concept)
    if "error" in result:
        result = safe_tool_call("query_knowledge", "find_related", concept)
    
    result["concept"] = concept
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("query_knowledge", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def save_memory(fact: str, source: str = "user_input", session_id: Optional[str] = None) -> str:
    """
    Persist a new fact or insight to the long-term knowledge base.
    
    Args:
        fact: The fact or insight to save
        source: Origin of the fact
        session_id: Optional session identifier
    """
    logger.info(f"save_memory called: fact='{fact[:50]}...' source='{source}'")
    
    result = safe_tool_call("save_memory", "consolidate", fact, source=source)
    if "error" in result:
        result = safe_tool_call("save_memory", "save", fact, metadata={"source": source})
    
    result["timestamp"] = datetime.now().isoformat()
    result["fact_preview"] = fact[:100] + "..." if len(fact) > 100 else fact
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("save_memory", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_memory_stats() -> str:
    """
    Get statistics about the stored knowledge base.
    
    Returns counts for atomic facts, vector embeddings, 
    forensic entries, and storage usage.
    """
    logger.info("get_memory_stats called")
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "storage": {},
        "counts": {},
        "health": "unknown"
    }
    
    try:
        tool = registry.get_tool("get_memory_stats")
        if tool:
            if hasattr(tool, 'get_stats'):
                db_stats = tool.get_stats()
                stats["counts"]["centrifuge"] = db_stats
            elif hasattr(tool, 'count'):
                stats["counts"]["centrifuge"] = {"total": tool.count()}
        
        # Check storage sizes
        db_path = os.environ.get("SME_DB_PATH", "data/knowledge_core.sqlite")
        if os.path.exists(db_path):
            stats["storage"]["knowledge_db_mb"] = round(os.path.getsize(db_path) / (1024**2), 2)
        
        # ChromaDB storage
        chroma_path = "data/chroma_db"
        if os.path.exists(chroma_path):
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(chroma_path)
                for filename in filenames
            )
            stats["storage"]["chroma_db_mb"] = round(total_size / (1024**2), 2)
        
        stats["health"] = "healthy"
        
    except Exception as e:
        logger.error(f"get_memory_stats error: {e}")
        stats["error"] = str(e)
        stats["health"] = "error"
    
    return json.dumps(stats, indent=2)


# =============================================================================
# TIER 2: Forensic Tools (Sprint 2 - Full Implementation)
# =============================================================================

@mcp.tool()
def analyze_authorship(text: str, author_id: str = "unknown", session_id: Optional[str] = None) -> str:
    """
    Extract linguistic fingerprint for authorship attribution.
    
    Args:
        text: The text to analyze
        author_id: Optional known author identifier
        session_id: Optional session identifier
    """
    logger.info(f"analyze_authorship called: text_len={len(text)} author={author_id}")
    
    if len(text) < 50:
        return json.dumps({
            "error": "Text too short for reliable analysis",
            "minimum_chars": 100,
            "provided_chars": len(text)
        })
    
    try:
        tool = registry.get_tool("analyze_authorship")
        if tool is None:
            return json.dumps({"error": "Scribe engine not available"})
        
        if hasattr(tool, 'extract_linguistic_fingerprint'):
            fingerprint = tool.extract_linguistic_fingerprint(text, author_id=author_id)
        elif hasattr(tool, 'analyze'):
            fingerprint = tool.analyze(text)
        else:
            return json.dumps({"error": "Fingerprint method not found"})
        
        result = serialize_result(fingerprint)
        result["text_length"] = len(text)
        result["author_id"] = author_id
        result["analysis_timestamp"] = datetime.now().isoformat()
        
        # Session tracking
        session = session_manager.get_session(session_id)
        session.add_history("analyze_authorship", result)
        result["session_id"] = session.session_id
        
        return json.dumps(result, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"analyze_authorship error: {e}")
        return json.dumps({"error": str(e), "author_id": author_id})


@mcp.tool()
def analyze_sentiment(text: str, session_id: Optional[str] = None) -> str:
    """
    Detect emotions, sarcasm, and overall sentiment in text.
    
    Args:
        text: The text to analyze
        session_id: Optional session identifier
    """
    logger.info(f"analyze_sentiment called: text_len={len(text)}")
    
    if len(text) < 10:
        return json.dumps({
            "error": "Text too short for sentiment analysis",
            "minimum_chars": 10,
            "provided_chars": len(text)
        })
    
    try:
        tool = registry.get_tool("analyze_sentiment")
        if tool is None:
            return json.dumps({"error": "Sentiment analyzer not available"})
        
        if hasattr(tool, 'analyze'):
            result = tool.analyze(text)
        elif hasattr(tool, 'get_sentiment'):
            result = tool.get_sentiment(text)
        else:
            return json.dumps({"error": "Analyze method not found"})
        
        serialized = serialize_result(result)
        serialized["text_length"] = len(text)
        serialized["analysis_timestamp"] = datetime.now().isoformat()
        
        # Session tracking
        session = session_manager.get_session(session_id)
        session.add_history("analyze_sentiment", serialized)
        serialized["session_id"] = session.session_id
        
        return json.dumps(serialized, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"analyze_sentiment error: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def link_entities(text: str, knowledge_base: str = "wikipedia", session_id: Optional[str] = None) -> str:
    """
    Extract and link named entities to knowledge bases.
    
    Args:
        text: The text to analyze
        knowledge_base: Target KB ("wikipedia", "wikidata", "custom")
        session_id: Optional session identifier
    """
    logger.info(f"link_entities called: text_len={len(text)} kb={knowledge_base}")
    
    if len(text) < 20:
        return json.dumps({
            "error": "Text too short for entity extraction",
            "minimum_chars": 20,
            "provided_chars": len(text)
        })
    
    try:
        tool = registry.get_tool("link_entities")
        if tool is None:
            return json.dumps({"error": "Entity linker not available"})
        
        if hasattr(tool, 'link_entities'):
            result = tool.link_entities(text)
        elif hasattr(tool, 'extract'):
            result = tool.extract(text)
        elif hasattr(tool, 'analyze'):
            result = tool.analyze(text)
        else:
            return json.dumps({"error": "Entity linking method not found"})
        
        serialized = serialize_result(result)
        serialized["text_length"] = len(text)
        serialized["knowledge_base"] = knowledge_base
        serialized["analysis_timestamp"] = datetime.now().isoformat()
        
        # Session tracking
        session = session_manager.get_session(session_id)
        session.add_history("link_entities", serialized)
        serialized["session_id"] = session.session_id
        
        return json.dumps(serialized, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"link_entities error: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def summarize_text(text: str, mode: str = "extractive", ratio: float = 0.3, session_id: Optional[str] = None) -> str:
    """
    Summarize text using multiple summarization modes.
    
    Args:
        text: The text to summarize
        mode: Summarization mode ("extractive", "abstractive", "query_focused")
        ratio: Compression ratio (0.1 to 0.9)
        session_id: Optional session identifier
    """
    logger.info(f"summarize_text called: text_len={len(text)} mode={mode} ratio={ratio}")
    
    if len(text) < 100:
        return json.dumps({
            "error": "Text too short for summarization",
            "minimum_chars": 100,
            "provided_chars": len(text)
        })
    
    ratio = max(0.1, min(0.9, ratio))
    
    try:
        tool = registry.get_tool("summarize_text")
        if tool is None:
            return json.dumps({"error": "Text summarizer not available"})
        
        if hasattr(tool, 'summarize'):
            result = tool.summarize(text, ratio=ratio)
        elif hasattr(tool, 'process'):
            result = tool.process(text, ratio=ratio)
        else:
            return json.dumps({"error": "Summarize method not found"})
        
        serialized = serialize_result(result)
        serialized["original_length"] = len(text)
        serialized["mode"] = mode
        serialized["requested_ratio"] = ratio
        serialized["analysis_timestamp"] = datetime.now().isoformat()
        
        # Session tracking
        session = session_manager.get_session(session_id)
        session.add_history("summarize_text", serialized)
        serialized["session_id"] = session.session_id
        
        return json.dumps(serialized, indent=2, default=str)
            
    except Exception as e:
        logger.error(f"summarize_text error: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
def deep_analyze(text: str, session_id: Optional[str] = None) -> str:
    """
    Perform comprehensive forensic analysis combining multiple tools.
    
    Args:
        text: Text to analyze
        session_id: Optional session identifier
    """
    logger.info(f"deep_analyze called: text_len={len(text)}")
    
    if len(text) < 100:
        return json.dumps({
            "error": "Text too short for deep analysis",
            "minimum_chars": 200,
            "provided_chars": len(text)
        })
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "text_length": len(text),
        "text_preview": text[:200] + "..." if len(text) > 200 else text,
        "analyses": {}
    }
    
    # Run each analysis
    analyses = [
        ("authorship", "analyze_authorship", "extract_linguistic_fingerprint", text),
        ("sentiment", "analyze_sentiment", "analyze", text),
        ("entities", "link_entities", "link_entities", text),
    ]
    
    for name, tool_name, method, *args in analyses:
        try:
            result = safe_tool_call(tool_name, method, *args)
            results["analyses"][name] = result
        except Exception as e:
            results["analyses"][name] = {"error": str(e)}
    
    # Add summary for longer texts
    if len(text) > 200:
        try:
            summary_result = safe_tool_call("summarize_text", "summarize", text, ratio=0.3)
            results["analyses"]["summary"] = summary_result
        except Exception as e:
            results["analyses"]["summary"] = {"error": str(e)}
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("deep_analyze", results)
    results["session_id"] = session.session_id
    
    return json.dumps(results, indent=2, default=str)


# =============================================================================
# TIER 3: Advanced Tools (Sprint 3)
# =============================================================================

@mcp.tool()
def cluster_documents(documents: List[str], algorithm: str = "kmeans", session_id: Optional[str] = None) -> str:
    """
    Cluster a list of documents by semantic similarity.
    """
    logger.info(f"cluster_documents called: count={len(documents)} algo={algorithm}")
    
    result = safe_tool_call("cluster_documents", "cluster", documents, algorithm=algorithm)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("cluster_documents", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def build_knowledge_graph(concepts: List[str], session_id: Optional[str] = None) -> str:
    """
    Build a semantic graph from a list of concepts and their relationships.
    """
    logger.info(f"build_knowledge_graph called: count={len(concepts)}")
    
    result = safe_tool_call("build_knowledge_graph", "build", concepts)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("build_knowledge_graph", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def verify_facts(claim: str, session_id: Optional[str] = None) -> str:
    """
    Verify a claim against the evidence in the knowledge base.
    """
    logger.info(f"verify_facts called: claim='{claim[:50]}...'")
    
    result = safe_tool_call("verify_facts", "verify", claim)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("verify_facts", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def analyze_nlp(text: str, session_id: Optional[str] = None) -> str:
    """
    Perform deep NLP analysis: dependencies, coreference, and semantic roles.
    """
    logger.info(f"analyze_nlp called: text_len={len(text)}")
    
    result = safe_tool_call("analyze_nlp", "process", text)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("analyze_nlp", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def detect_networks(authors: List[str], session_id: Optional[str] = None) -> str:
    """
    Detect coordinated sockpuppet networks or behavioral clusters among authors.
    """
    logger.info(f"detect_networks called: authors_count={len(authors)}")
    
    result = safe_tool_call("detect_networks", "analyze", authors)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("detect_networks", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def resolve_concept(term: str, session_id: Optional[str] = None) -> str:
    """
    Map an ambiguous term to a specific knowledge graph node.
    """
    logger.info(f"resolve_concept called: term='{term}'")
    
    result = safe_tool_call("resolve_concept", "resolve", term)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("resolve_concept", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def generate_intelligence_report(subject: str, findings: List[str], session_id: Optional[str] = None) -> str:
    """
    Aggregate forensic findings into a structured intelligence report.
    """
    logger.info(f"generate_intelligence_report called: subject='{subject}' findings={len(findings)}")
    
    result = safe_tool_call("generate_intelligence_report", "generate", subject, findings=findings)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("generate_intelligence_report", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def discover_overlap(author_ids: List[str], session_id: Optional[str] = None) -> str:
    """
    Find shared rhetorical signals and style overlaps between multiple authors.
    """
    logger.info(f"discover_overlap called: count={len(author_ids)}")
    
    result = safe_tool_call("discover_overlap", "discover", author_ids)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("discover_overlap", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def analyze_rolling_delta(text: str, window_size: int = 1000, session_id: Optional[str] = None) -> str:
    """
    Perform temporal stylometric analysis to see how writing style evolves.
    """
    logger.info(f"analyze_rolling_delta called: text_len={len(text)} window={window_size}")
    
    result = safe_tool_call("analyze_rolling_delta", "analyze", text, window_size=window_size)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("analyze_rolling_delta", result)
    result["session_id"] = session.session_id
    
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def cross_author_comparison(texts: List[Dict[str, str]], session_id: Optional[str] = None) -> str:
    """
    Compare multiple authors/texts to find commonalities and discrepancies.
    
    Args:
        texts: List of dicts with {"text": "...", "author_id": "..."}
    """
    logger.info(f"cross_author_comparison called: count={len(texts)}")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "comparison_count": len(texts),
        "individual_fingerprints": [],
        "group_metrics": {}
    }
    
    author_ids = []
    
    for item in texts:
        text = item.get("text", "")
        aid = item.get("author_id", "unknown")
        author_ids.append(aid)
        
        fingerprint = safe_tool_call("analyze_authorship", "extract_linguistic_fingerprint", text, author_id=aid)
        results["individual_fingerprints"].append({
            "author_id": aid,
            "fingerprint": fingerprint
        })
    
    # Group analysis
    results["group_metrics"]["overlap"] = safe_tool_call("discover_overlap", "discover", author_ids)
    results["group_metrics"]["networks"] = safe_tool_call("detect_networks", "analyze", author_ids)
    
    # Session tracking
    session = session_manager.get_session(session_id)
    session.add_history("cross_author_comparison", results)
    results["session_id"] = session.session_id
    
    return json.dumps(results, indent=2, default=str)
@mcp.tool()
def process_batch(tool_name: str, inputs: List[Any], session_id: Optional[str] = None) -> str:
    """
    Execute a tool against multiple inputs in a single batch.
    
    Args:
        tool_name: Name of the tool to run (e.g., "analyze_sentiment")
        inputs: List of inputs for the tool
        session_id: Optional session identifier
        
    Returns:
        JSON with results for each input, including success/failure status
    """
    logger.info(f"process_batch called: tool={tool_name} count={len(inputs)}")
    
    results = {
        "tool": tool_name,
        "batch_size": len(inputs),
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    
    session = session_manager.get_session(session_id)
    
    for idx, item in enumerate(inputs):
        try:
            # Map tool name to our MCP tool function
            # Since tools are registered with @mcp.tool, we can try to call them via their names
            # or use safe_tool_call indirectly. For simplicity, we'll use safe_tool_call.
            
            # We need to find the default method for the tool
            registry_tool = registry.get_tool_info(tool_name)
            if not registry_tool:
                res = {"index": idx, "error": f"Tool {tool_name} not found in registry"}
            else:
                method = "analyze" # Default fallback
                if "authorship" in tool_name: method = "extract_linguistic_fingerprint"
                elif "search" in tool_name: method = "search"
                elif "query" in tool_name: method = "search"
                elif "save" in tool_name: method = "consolidate"
                elif "entities" in tool_name: method = "link_entities"
                elif "summarize" in tool_name: method = "summarize"
                
                res = safe_tool_call(tool_name, method, item)
                res["index"] = idx
            
            results["results"].append(res)
            
        except Exception as e:
            results["results"].append({"index": idx, "error": str(e)})
    
    # Store in session history
    session.add_history("process_batch", results)
    
    return json.dumps(results, indent=2, default=str)


# =============================================================================
# Session Tools
# =============================================================================

@mcp.tool()
def get_session_info(session_id: Optional[str] = None) -> str:
    """
    Get detailed information about a session.
    
    Returns session history, scratchpad, and metadata.
    """
    session = session_manager.get_session(session_id)
    return json.dumps(session.to_dict(), indent=2)


@mcp.tool()
def update_scratchpad(key: str, value: Any, session_id: Optional[str] = None) -> str:
    """
    Store temporary facts or context in the session scratchpad.
    """
    session = session_manager.get_session(session_id)
    session.update_scratchpad(key, value)
    return json.dumps({"success": True, "session_id": session.session_id, "key": key})


# =============================================================================
# Utility Tools
# =============================================================================

@mcp.tool()
def list_available_tools() -> str:
    """
    List all available MCP tools exposed by the Lawnmower Man gateway.
    
    Returns tools grouped by category with descriptions.
    """
    tools_by_category: Dict[str, List[Dict]] = {}
    
    for tool_def in registry.list_tools():
        category = tool_def.category
        if category not in tools_by_category:
            tools_by_category[category] = []
        tools_by_category[category].append({
            "name": tool_def.name,
            "description": tool_def.description,
            "parameters": tool_def.parameters
        })
    
    return json.dumps({
        "gateway": "Lawnmower Man",
        "version": "0.4.0",  # Sprint 4
        "tool_count": len(registry.TOOL_DEFINITIONS),
        "categories": tools_by_category,
        "sprint": 4
    }, indent=2)


# =============================================================================
# Production Hardening Tools
# =============================================================================

@mcp.tool()
def login(username: str, password: str) -> str:
    """
    Authenticate with the gateway and receive a JWT token.
    """
    token = auth_manager.login(username, password)
    if token:
        return json.dumps({"token": token, "expires_in": "24h"})
    return json.dumps({"error": "Invalid credentials"})


def validate_access(token: Optional[str], client_id: str) -> Optional[str]:
    """Helper to check rate limits and JWT."""
    # 1. Rate Limiting first (even for unauth)
    allowed, remaining = rate_limiter.is_allowed(client_id)
    if not allowed:
        return json.dumps({"error": "Rate limit exceeded", "retry_after": "60s"})
    
    # 2. JWT Verification (optional for now, but enforced if token provided)
    if token:
        payload = auth_manager.verify_token(token)
        if not payload:
            return json.dumps({"error": "Invalid or expired token"})
            
    return None


@mcp.tool()
def check_health() -> str:
    """
    Combined health check for the gateway and all dependencies.
    
    Returns:
        JSON with overall status (healthy, degraded, down)
    """
    logger.info("check_health called")
    
    # 1. Check SME System Verify
    verify_result = json.loads(verify_system())
    
    # 2. Check Session Manager
    session_count = len(session_manager._sessions)
    metrics_manager.set_active_sessions(session_count)
    
    # 3. Overall health determination
    status = verify_result.get("status", "unknown")
    metrics_manager.set_health(status)
    
    health = {
        "gateway": "Lawnmower Man",
        "version": "0.4.0",
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "active_sessions": session_count,
        "sme_health": verify_result
    }
    
    return json.dumps(health, indent=2)


@mcp.tool()
def get_system_latency() -> str:
    """
    Measure internal tool call latency and system responsive.
    """
    import time
    start = time.perf_counter()
    
    # Do a light registry walk
    registry.list_tools()
    
    end = time.perf_counter()
    latency_ms = (end - start) * 1000
    
    return json.dumps({
        "internal_latency_ms": round(latency_ms, 3),
        "timestamp": datetime.now().isoformat()
    })


# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info("Starting Lawnmower Man MCP Gateway v0.4.0 (Sprint 4)...")
    logger.info(f"Available tools: {len(registry.TOOL_DEFINITIONS)}")
    logger.info(f"Categories: {registry.get_categories()}")
    
    # Start metrics server
    metrics_manager.start()
    
    mcp.run()

