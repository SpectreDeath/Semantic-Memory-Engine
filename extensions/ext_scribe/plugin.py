import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Scribe")

try:
    from src.scribe.engine import StylometryEngine
except ImportError:
    StylometryEngine = None

try:
    from src.scribe.impostors_checker import ImpostorsChecker
except ImportError:
    ImpostorsChecker = None

try:
    from src.scribe.contrastive_analyzer import ContrastiveAnalyzer
except ImportError:
    ContrastiveAnalyzer = None

try:
    from src.scribe.adaptive_learner import AdaptiveLearner
except ImportError:
    AdaptiveLearner = None

try:
    from src.scribe.rolling_delta import RollingDeltaAnalyzer
except ImportError:
    RollingDeltaAnalyzer = None

try:
    from src.scribe.stylo_wrapper import StyloWrapper
except ImportError:
    StyloWrapper = None


class ScribeExtension(BasePlugin):
    """
    Scribe Stylometry Extension for SME.
    Provides stylometry engine, impostor detection, contrastive analysis, adaptive learning, rolling delta analysis, and Stylo integration.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.engine = StylometryEngine() if StylometryEngine else None
        self.impostors = ImpostorsChecker() if ImpostorsChecker else None
        self.contrastive = ContrastiveAnalyzer() if ContrastiveAnalyzer else None
        self.adaptive = AdaptiveLearner() if AdaptiveLearner else None
        self.rolling_delta = RollingDeltaAnalyzer() if RollingDeltaAnalyzer else None
        self.stylo = StyloWrapper() if StyloWrapper else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Scribe Stylometry extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.analyze_style,
            self.detect_impostors,
            self.compare_styles,
            self.adaptive_learn,
            self.analyze_rolling_delta,
            self.stylo_integrate,
        ]

    async def analyze_style(self, text: str, author: str | None = None) -> str:
        """Analyze writing style of text."""
        if not self.engine:
            return json.dumps({"error": "StylometryEngine not available"})
        try:
            result = self.engine.analyze(text, author)
            return json.dumps({"text_length": len(text), "author": author, "analysis": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def detect_impostors(self, suspect_text: str, known_author_texts: list[str]) -> str:
        """Detect if suspect text matches known author."""
        if not self.impostors:
            return json.dumps({"error": "ImpostorsChecker not available"})
        try:
            result = self.impostors.check(suspect_text, known_author_texts)
            return json.dumps({"impostor_detected": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def compare_styles(self, text1: str, text2: str) -> str:
        """Compare writing styles of two texts."""
        if not self.contrastive:
            return json.dumps({"error": "ContrastiveAnalyzer not available"})
        try:
            result = self.contrastive.compare(text1, text2)
            return json.dumps(
                {"text1_length": len(text1), "text2_length": len(text2), "comparison": result}
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def adaptive_learn(self, training_data: list[dict], model_type: str = "author") -> str:
        """Train adaptive learning model."""
        if not self.adaptive:
            return json.dumps({"error": "AdaptiveLearner not available"})
        try:
            result = self.adaptive.train(training_data, model_type)
            return json.dumps(
                {"training_samples": len(training_data), "model_type": model_type, "result": result}
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def analyze_rolling_delta(self, text: str, window_size: int = 500) -> str:
        """Analyze style changes over time in text."""
        if not self.rolling_delta:
            return json.dumps({"error": "RollingDeltaAnalyzer not available"})
        try:
            result = self.rolling_delta.analyze(text, window_size)
            return json.dumps(
                {"text_length": len(text), "window_size": window_size, "analysis": result}
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def stylo_integrate(self, text: str, method: str = "mfc") -> str:
        """Integrate with Stylo R package for advanced analysis."""
        if not self.stylo:
            return json.dumps({"error": "StyloWrapper not available"})
        try:
            result = self.stylo.analyze(text, method)
            return json.dumps({"text_length": len(text), "method": method, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return ScribeExtension(manifest, nexus_api)
