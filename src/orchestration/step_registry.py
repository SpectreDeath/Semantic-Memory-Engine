"""
🔧 Workflow Step Registry
=========================
Maps workflow step names to actual SME handlers (skills/tools).
Enables workflow engine to execute real SME capabilities.

Each entry maps: step_name -> (handler_function, param_schema)
"""

import logging
from typing import Any, Callable

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
        """Search academic papers."""
        try:
            from src.gathering.scholar_api import ScholarAPI

            api = ScholarAPI()
            papers = api.search(query, max_results)
            return {"status": "success", "count": len(papers), "papers": papers}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register(
        "scholar_search", scholar_search_handler, {"query": "string", "max_results": "integer"}
    )

    def osint_scan_handler(username: str, platforms: list | None = None, **kwargs) -> dict:
        """Run OSINT scan on username."""
        try:
            from src.gathering.osint_toolkit import OSINTToolkit

            toolkit = OSINTToolkit()
            result = toolkit.scan_username(username, platforms or ["twitter", "reddit"])
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    registry.register("osint_scan", osint_scan_handler, {"username": "string", "platforms": "list"})

    # =============================================================================
    # ANALYSIS STEPS
    # =============================================================================

    def stylometry_handler(text: str, author_id: str | None = None, **kwargs) -> dict:
        """Analyze writing style."""
        try:
            from src.scribe.engine import StylometryEngine

            engine = StylometryEngine()
            profile = engine.extract_linguistic_fingerprint(text, author_id)
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
        """Query database."""
        try:
            from src.core.data_manager import DataManager

            manager = DataManager()
            result = manager.query(query, params or {})
            return {"status": "success", "results": result}
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
