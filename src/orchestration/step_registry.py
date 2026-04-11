"""
🔧 Workflow Step Registry
=========================
Maps workflow step names to actual SME handlers (skills/tools).
Enables workflow engine to execute real SME capabilities.

Each entry maps: step_name -> (handler_function, param_schema)
"""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("StepRegistry")


class StepRegistry:
    """Registry mapping step names to handlers."""

    def __init__(self):
        self._steps: dict[str, tuple[Callable, dict]] = {}

    def register(
        self,
        name: str,
        handler: Callable,
        params: dict[str, Any] | None = None,
        description: str = "",
    ):
        """Register a step handler."""
        self._steps[name] = (handler, params or {})
        logger.info(f"Registered workflow step: {name}")

    def get_handler(self, name: str) -> Callable | None:
        """Get handler by name."""
        if name in self._steps:
            return self._steps[name][0]
        return None

    def get_params(self, name: str) -> dict[str, Any]:
        """Get param schema for step."""
        if name in self._steps:
            return self._steps[name][1]
        return {}

    def list_steps(self) -> list[dict[str, Any]]:
        """List all registered steps."""
        return [
            {"name": name, "params": params, "description": ""}
            for name, (_, params) in self._steps.items()
        ]


def create_sme_step_registry() -> StepRegistry:
    """Create registry with SME skill/tool handlers."""
    registry = StepRegistry()

    # =============================================================================
    # HARVESTING STEPS
    # =============================================================================

    def harvest_url_handler(url: str, **kwargs) -> dict:
        """Harvest a URL to atomic facts."""
        try:
            from src.harvester.crawler import WebCrawler

            crawler = WebCrawler()
            result = crawler.fetch(url)
            return {"status": "success", "url": url, "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register(
        "harvest_url",
        harvest_url_handler,
        {"url": "string", "extract_js": "boolean"},
    )

    def rss_bridge_handler(feed_url: str, **kwargs) -> dict:
        """Fetch and process RSS feed."""
        try:
            from src.gathering.rss_bridge import RSSBridge

            bridge = RSSBridge()
            articles = bridge.fetch_feed(feed_url)
            return {"status": "success", "count": len(articles), "articles": articles}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("rss_fetch", rss_bridge_handler, {"feed_url": "string"})

    def scholar_search_handler(query: str, max_results: int = 10, **kwargs) -> dict:
        """Search academic papers via CrossRef API."""
        try:
            import json

            import requests

            # CrossRef API - free, no key required
            url = "https://api.crossref.org/works"
            params = {
                "query": query,
                "rows": min(max_results, 20),
                "select": "title,author,published,container-title,doi,abstract",
            }

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            papers = []
            for item in data.get("message", {}).get("items", []):
                authors = item.get("author", [])
                author_names = [
                    f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors
                ]

                papers.append(
                    {
                        "title": item.get("title", [""])[0] if item.get("title") else "",
                        "authors": author_names[:5],  # Limit to 5 authors
                        "year": item.get("published", {}).get("date-parts", [[None]])[0][0],
                        "journal": item.get("container-title", [""])[0]
                        if item.get("container-title")
                        else "",
                        "doi": item.get("doi", ""),
                        "abstract": item.get("abstract", "")[:300] if item.get("abstract") else "",
                    }
                )

            return {"status": "success", "count": len(papers), "papers": papers}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register(
        "scholar_search", scholar_search_handler, {"query": "string", "max_results": "integer"}
    )

    def osint_scan_handler(username: str, platforms: list | None = None, **kwargs) -> dict:
        """Run OSINT scan on username."""
        try:
            import io
            import sys

            from src.gathering.osint_toolkit import footprint_username, save_to_json

            # Capture output to avoid print statements
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            result = footprint_username(username)

            # Restore stdout
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Save results
            save_to_json(result)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def search_wikipedia_handler(query: str, **kwargs) -> dict:
        """Search Wikipedia for a person or topic."""
        try:
            import json

            import requests

            # Wikipedia API search
            search_url = "https://en.wikipedia.org/w/api.php"
            headers = {
                "User-Agent": "SME-Research-Bot/1.0 (investigation@local; educational research)"
            }
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
                "srlimit": 5,
            }

            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []
            if "query" in data and "search" in data["query"]:
                for item in data["query"]["search"]:
                    # Get more details for each result
                    detail_params = {
                        "action": "query",
                        "titles": item["title"],
                        "prop": "extracts|info",
                        "exintro": True,
                        "explaintext": True,
                        "inprop": "url",
                        "format": "json",
                    }
                    detail_resp = requests.get(
                        search_url, params=detail_params, headers=headers, timeout=15
                    )
                    detail_resp.raise_for_status()
                    detail_data = detail_resp.json()
                    pages = detail_data.get("query", {}).get("pages", {})
                    for page_id, page_info in pages.items():
                        if page_id != "-1":
                            results.append(
                                {
                                    "title": page_info.get("title", ""),
                                    "snippet": item.get("snippet", ""),
                                    "extract": page_info.get("extract", "")[:500],
                                    "url": page_info.get("fullurl", ""),
                                }
                            )
                            break

            return {"status": "success", "results": results, "query": query}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("search_wikipedia", search_wikipedia_handler, {"query": "string"})

    registry.register("osint_scan", osint_scan_handler, {"username": "string", "platforms": "list"})

    # =============================================================================
    # ANALYSIS STEPS
    # =============================================================================

    def stylometry_handler(text: str, author_id: str | None = None, **kwargs) -> dict:
        """Analyze writing style - simple word frequency analysis."""
        try:
            import re
            from collections import Counter

            # Simple stylometric features
            words = re.findall(r"\b\w+\b", text.lower())
            sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in sentences if s.strip()]

            # Feature extraction
            word_count = len(words)
            avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0
            avg_sentence_length = word_count / len(sentences) if sentences else 0

            # Word frequency (top 20)
            word_freq = Counter(words).most_common(20)

            # Function words (common)
            function_words = {
                "the",
                "a",
                "an",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "must",
                "to",
                "of",
                "in",
                "for",
                "on",
                "with",
            }
            func_word_count = sum(1 for w in words if w in function_words)
            func_word_ratio = func_word_count / word_count if word_count > 0 else 0

            profile = {
                "word_count": word_count,
                "avg_word_length": round(avg_word_length, 2),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "top_words": dict(word_freq[:20]),
                "function_word_ratio": round(func_word_ratio, 3),
                "unique_words": len(set(words)),
            }

            return {"status": "success", "profile": profile}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("stylometry", stylometry_handler, {"text": "string", "author_id": "string?"})

    def sentiment_handler(text: str, **kwargs) -> dict:
        """Analyze text sentiment."""
        try:
            from src.core.sentiment_analyzer import SentimentAnalyzer

            analyzer = SentimentAnalyzer()
            result = analyzer.analyze(text)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("sentiment", sentiment_handler, {"text": "string"})

    def text_summarize_handler(text: str, ratio: float = 0.3, **kwargs) -> dict:
        """Summarize text."""
        try:
            from src.core.text_summarizer import TextSummarizer

            summarizer = TextSummarizer()
            summary = summarizer.summarize(text, ratio)
            return {"status": "success", "summary": summary}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("summarize", text_summarize_handler, {"text": "string", "ratio": "float"})

    def rhetorical_analysis_handler(text: str, **kwargs) -> dict:
        """Analyze rhetorical structure."""
        try:
            from src.analysis.rhetoric import analyze_rhetoric

            result = analyze_rhetoric(text)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("rhetorical_analysis", rhetorical_analysis_handler, {"text": "string"})

    def overlap_detection_handler(texts: list[str], **kwargs) -> dict:
        """Detect semantic overlap between texts."""
        try:
            from src.analysis.overlap_discovery import OverlapDiscovery

            detector = OverlapDiscovery()
            overlaps = detector.find_overlaps(texts)
            return {"status": "success", "overlaps": overlaps}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("overlap_detection", overlap_detection_handler, {"texts": "list"})

    # =============================================================================
    # AI STEPS
    # =============================================================================

    def ai_flow_handler(flow_name: str, input_data: dict, **kwargs) -> dict:
        """Execute AI flow."""
        try:
            from src.ai.bridge import run_ai_flow

            result = run_ai_flow(flow_name, input_data)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("ai_flow", ai_flow_handler, {"flow_name": "string", "input_data": "object"})

    def concept_lookup_handler(term: str, **kwargs) -> dict:
        """Look up concept via AI."""
        try:
            from src.ai.agent_logic import lookup_concept

            result = lookup_concept(term)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("concept_lookup", concept_lookup_handler, {"term": "string"})

    # =============================================================================
    # SECURITY/FORENSICS STEPS
    # =============================================================================

    def trust_score_handler(data_source: str, content: str, **kwargs) -> dict:
        """Calculate epistemic trust score."""
        try:
            from extensions.ext_epistemic_gatekeeper.plugin import EpistemicGatekeeper

            gatekeeper = EpistemicGatekeeper()
            score = gatekeeper.calculate_trust(content)
            return {"status": "success", "trust_score": score, "source": data_source}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register(
        "trust_score", trust_score_handler, {"data_source": "string", "content": "string"}
    )

    def bot_detection_handler(username: str, platform: str = "twitter", **kwargs) -> dict:
        """Detect if account is a bot."""
        try:
            from extensions.ext_social_intel.plugin import SocialIntel

            intel = SocialIntel()
            result = intel.detect_bot(username, platform)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register(
        "bot_detection", bot_detection_handler, {"username": "string", "platform": "string"}
    )

    # =============================================================================
    # DATA STEPS
    # =============================================================================

    def save_to_db_handler(data: dict, table: str, **kwargs) -> dict:
        """Save data to database."""
        try:
            from src.core.data_manager import DataManager

            manager = DataManager()
            result = manager.save(table, data)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("save_to_db", save_to_db_handler, {"data": "object", "table": "string"})

    def query_db_handler(query: str, params: dict | None = None, **kwargs) -> dict:
        """Query database using SQLite."""
        try:
            import json
            import os
            import sqlite3

            # Use the SME database
            db_path = os.path.join(os.getcwd(), "data", "storage", "laboratory.db")

            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Parse query - support basic SELECT statements
            if query.strip().upper().startswith("SELECT"):
                cursor.execute(query, params or {})
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
            else:
                cursor.execute(query, params or {})
                conn.commit()
                results = {"rows_affected": cursor.rowcount}

            conn.close()
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("query_db", query_db_handler, {"query": "string", "params": "object?"})

    def gephi_export_handler(mode: str, data: dict, **kwargs) -> dict:
        """Export to Gephi."""
        try:
            from src.utils.gephi_bridge import GephiBridge

            bridge = GephiBridge()
            result = bridge.export(mode, data)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("gephi_export", gephi_export_handler, {"mode": "string", "data": "object"})

    # =============================================================================
    # UTILITY STEPS
    # =============================================================================

    def webhook_handler(url: str, payload: dict, **kwargs) -> dict:
        """Send webhook notification."""
        import httpx

        try:
            response = httpx.post(url, json=payload, timeout=10)
            return {"status": "success", "status_code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("webhook", webhook_handler, {"url": "string", "payload": "object"})

    def log_handler(message: str, level: str = "info", **kwargs) -> dict:
        """Log a message."""
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
        return {"status": "success", "logged": message}

    registry.register("log", log_handler, {"message": "string", "level": "string"})

    return registry


# Global registry instance
_sme_registry: StepRegistry | None = None


def get_step_registry() -> StepRegistry:
    """Get the global SME step registry."""
    global _sme_registry
    if _sme_registry is None:
        _sme_registry = create_sme_step_registry()
    return _sme_registry
