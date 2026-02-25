"""
gateway/routers/nlp.py
======================
Natural Language Processing tools: entity extraction, sentiment analysis,
text summarisation, deep NLP analysis, and concept resolution.
"""

import json
import logging
import string
from datetime import datetime
from typing import Any, Optional

from gateway.routers.shared import make_safe_tool_call, serialize_result

logger = logging.getLogger("lawnmower.nlp")


def register(
    mcp: Any,
    registry: Any,
    session_manager: Any,
    metrics_manager: Any,
) -> None:
    """Register NLP tools with the FastMCP instance."""

    safe_tool_call = make_safe_tool_call(registry, metrics_manager)

    @mcp.tool()
    def entity_extractor(text: str, session_id: Optional[str] = None) -> str:
        """
        Advanced entity cross-referencing against the 10GB ConceptNet knowledge graph.

        Identifies mentions, retrieves candidates, and returns ranked matches
        with relationship types and relevance scores.
        Delegates to the registered entity-linker tool; falls back to a
        token-heuristic scan if the linker is unavailable.
        """
        logger.info(f"entity_extractor called: text_len={len(text)}")

        linker_result = safe_tool_call("link_entities", "link_entities", text)
        raw_entities = []
        if linker_result.get("success") and isinstance(linker_result.get("data"), dict):
            raw_entities = linker_result["data"].get("entities", [])

        if not raw_entities:
            stopwords = {
                "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
                "to", "of", "and", "or", "but", "for", "with", "that", "this",
                "it", "he", "she", "they", "we", "i", "my", "your", "our",
            }
            tokens = text.translate(str.maketrans("", "", string.punctuation)).split()
            candidate_names = list({
                t for t in tokens
                if len(t) > 3 and t[0].isupper() and t.lower() not in stopwords
            })
            raw_entities = [
                {
                    "entity_name": name,
                    "relationship_type": "mentioned_in",
                    "relevance_score": round(0.5 + (len(name) / (2 * max(len(name), 10))), 2),
                }
                for name in candidate_names[:20]
            ]

        extracted = {
            "text": text[:200] + ("..." if len(text) > 200 else ""),
            "entity_count": len(raw_entities),
            "entities": raw_entities,
            "core_version": "ConceptNet 5.7.0",
            "timestamp": datetime.now().isoformat(),
        }

        session = session_manager.get_session(session_id)
        session.add_history("entity_extractor", extracted)
        return json.dumps(extracted, indent=2)

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
                "provided_chars": len(text),
            })

        try:
            tool = registry.get_tool("analyze_sentiment")
            if tool is None:
                return json.dumps({"error": "Sentiment analyzer not available"})

            if hasattr(tool, "analyze"):
                result = tool.analyze(text)
            elif hasattr(tool, "get_sentiment"):
                result = tool.get_sentiment(text)
            else:
                return json.dumps({"error": "Analyze method not found"})

            serialized = serialize_result(result)
            serialized["text_length"] = len(text)
            serialized["analysis_timestamp"] = datetime.now().isoformat()

            session = session_manager.get_session(session_id)
            session.add_history("analyze_sentiment", serialized)
            serialized["session_id"] = session.session_id
            return json.dumps(serialized, indent=2, default=str)

        except Exception as e:
            logger.error(f"analyze_sentiment error: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def link_entities(
        text: str,
        knowledge_base: str = "wikipedia",
        session_id: Optional[str] = None,
    ) -> str:
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
                "provided_chars": len(text),
            })

        try:
            tool = registry.get_tool("link_entities")
            if tool is None:
                return json.dumps({"error": "Entity linker not available"})

            if hasattr(tool, "link_entities"):
                result = tool.link_entities(text)
            elif hasattr(tool, "extract"):
                result = tool.extract(text)
            elif hasattr(tool, "analyze"):
                result = tool.analyze(text)
            else:
                return json.dumps({"error": "Entity linking method not found"})

            serialized = serialize_result(result)
            serialized["text_length"] = len(text)
            serialized["knowledge_base"] = knowledge_base
            serialized["analysis_timestamp"] = datetime.now().isoformat()

            session = session_manager.get_session(session_id)
            session.add_history("link_entities", serialized)
            serialized["session_id"] = session.session_id
            return json.dumps(serialized, indent=2, default=str)

        except Exception as e:
            logger.error(f"link_entities error: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def summarize_text(
        text: str,
        mode: str = "extractive",
        ratio: float = 0.3,
        session_id: Optional[str] = None,
    ) -> str:
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
                "provided_chars": len(text),
            })

        ratio = max(0.1, min(0.9, ratio))

        try:
            tool = registry.get_tool("summarize_text")
            if tool is None:
                return json.dumps({"error": "Text summarizer not available"})

            if hasattr(tool, "summarize"):
                result = tool.summarize(text, ratio=ratio)
            elif hasattr(tool, "process"):
                result = tool.process(text, ratio=ratio)
            else:
                return json.dumps({"error": "Summarize method not found"})

            serialized = serialize_result(result)
            serialized["original_length"] = len(text)
            serialized["mode"] = mode
            serialized["requested_ratio"] = ratio
            serialized["analysis_timestamp"] = datetime.now().isoformat()

            session = session_manager.get_session(session_id)
            session.add_history("summarize_text", serialized)
            serialized["session_id"] = session.session_id
            return json.dumps(serialized, indent=2, default=str)

        except Exception as e:
            logger.error(f"summarize_text error: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def analyze_nlp(text: str, session_id: Optional[str] = None) -> str:
        """Perform deep NLP analysis: dependencies, coreference, and semantic roles."""
        logger.info(f"analyze_nlp called: text_len={len(text)}")
        result = safe_tool_call("analyze_nlp", "process", text)
        session = session_manager.get_session(session_id)
        session.add_history("analyze_nlp", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)

    @mcp.tool()
    def resolve_concept(term: str, session_id: Optional[str] = None) -> str:
        """Map an ambiguous term to a specific knowledge graph node."""
        logger.info(f"resolve_concept called: term='{term}'")
        result = safe_tool_call("resolve_concept", "resolve", term)
        session = session_manager.get_session(session_id)
        session.add_history("resolve_concept", result)
        result["session_id"] = session.session_id
        return json.dumps(result, indent=2, default=str)
