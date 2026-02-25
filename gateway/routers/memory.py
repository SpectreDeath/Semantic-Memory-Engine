"""
gateway/routers/memory.py
=========================
Memory, knowledge-base, and session management tools.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from gateway.routers.shared import make_safe_tool_call, serialize_result

logger = logging.getLogger("lawnmower.memory")


def register(
    mcp: Any,
    registry: Any,
    session_manager: Any,
    metrics_manager: Any,
) -> None:
    """Register memory and session tools with the FastMCP instance."""

    safe_tool_call = make_safe_tool_call(registry, metrics_manager)

    # ------------------------------------------------------------------
    # TIER 1 — Memory tools
    # ------------------------------------------------------------------

    @mcp.tool()
    def semantic_search(
        query: str, limit: int = 5, session_id: Optional[str] = None
    ) -> str:
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
            result = safe_tool_call("semantic_search", "query", query, limit=limit)

        result["query"] = query
        result["limit"] = limit

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
        session = session_manager.get_session(session_id)
        session.add_history("query_knowledge", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def save_memory(
        fact: str, source: str = "user_input", session_id: Optional[str] = None
    ) -> str:
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

        stats: dict = {
            "timestamp": datetime.now().isoformat(),
            "storage": {},
            "counts": {},
            "health": "unknown",
        }

        try:
            tool = registry.get_tool("get_memory_stats")
            if tool:
                if hasattr(tool, "get_stats"):
                    stats["counts"]["centrifuge"] = tool.get_stats()
                elif hasattr(tool, "count"):
                    stats["counts"]["centrifuge"] = {"total": tool.count()}

            db_path = os.environ.get("SME_DB_PATH", "data/knowledge_core.sqlite")
            if os.path.exists(db_path):
                stats["storage"]["knowledge_db_mb"] = round(
                    os.path.getsize(db_path) / (1024 ** 2), 2
                )

            chroma_path = "data/chroma_db"
            if os.path.exists(chroma_path):
                total_size = sum(
                    os.path.getsize(os.path.join(dirpath, fname))
                    for dirpath, _, filenames in os.walk(chroma_path)
                    for fname in filenames
                )
                stats["storage"]["chroma_db_mb"] = round(total_size / (1024 ** 2), 2)

            stats["health"] = "healthy"

        except Exception as e:
            logger.error(f"get_memory_stats error: {e}")
            stats["error"] = str(e)
            stats["health"] = "error"

        return json.dumps(stats, indent=2)

    # ------------------------------------------------------------------
    # Session tools
    # ------------------------------------------------------------------

    @mcp.tool()
    def store_session_entry(
        key: str, value: Any, session_id: Optional[str] = None
    ) -> str:
        """
        Persist arbitrary data (like stylistic baselines or suspect vectors)
        in the session scratchpad.
        """
        session = session_manager.get_session(session_id)
        session.update_scratchpad(key, value)
        logger.info(f"store_session_entry: {key} stored in session {session.session_id}")
        return json.dumps({"success": True, "key": key, "session_id": session.session_id})

    @mcp.tool()
    def get_session_info(session_id: Optional[str] = None) -> str:
        """
        Get detailed information about a session.

        Returns session history, scratchpad, and metadata.
        """
        session = session_manager.get_session(session_id)
        return json.dumps(session.to_dict(), indent=2)

    @mcp.tool()
    def update_scratchpad(
        key: str, value: Any, session_id: Optional[str] = None
    ) -> str:
        """Store temporary facts or context in the session scratchpad."""
        session = session_manager.get_session(session_id)
        session.update_scratchpad(key, value)
        return json.dumps(
            {"success": True, "session_id": session.session_id, "key": key}
        )
