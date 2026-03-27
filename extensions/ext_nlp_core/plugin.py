import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.NLPCore")

try:
    from src.core.sentiment_analyzer import SentimentAnalyzer
except ImportError:
    SentimentAnalyzer = None

try:
    from src.core.text_summarizer import TextSummarizer
except ImportError:
    TextSummarizer = None

try:
    from src.core.entity_linker import EntityLinker
except ImportError:
    EntityLinker = None

try:
    from src.core.document_clusterer import DocumentClusterer
except ImportError:
    DocumentClusterer = None

try:
    from src.core.nlp_pipeline import NLPPipeline
except ImportError:
    NLPPipeline = None


class NLPCoreExtension(BasePlugin):
    """
    NLP Core Processing Extension for SME.
    Provides sentiment analysis, text summarization, entity linking, document clustering, and NLP pipeline.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.sentiment = SentimentAnalyzer() if SentimentAnalyzer else None
        self.summarizer = TextSummarizer() if TextSummarizer else None
        self.entity_linker = EntityLinker() if EntityLinker else None
        self.clusterer = DocumentClusterer() if DocumentClusterer else None
        self.nlp_pipeline = NLPPipeline() if NLPPipeline else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] NLP Core extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.analyze_sentiment,
            self.summarize_text,
            self.link_entities,
            self.cluster_documents,
            self.process_nlp_pipeline,
        ]

    async def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of input text."""
        if not self.sentiment:
            return json.dumps({"error": "SentimentAnalyzer not available"})
        try:
            result = self.sentiment.analyze(text)
            return json.dumps({"text": text, "sentiment": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize input text."""
        if not self.summarizer:
            return json.dumps({"error": "TextSummarizer not available"})
        try:
            summary = self.summarizer.summarize(text, max_length)
            return json.dumps({"original_length": len(text), "summary": summary})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def link_entities(self, text: str) -> str:
        """Link entities in text to knowledge base."""
        if not self.entity_linker:
            return json.dumps({"error": "EntityLinker not available"})
        try:
            entities = self.entity_linker.link(text)
            return json.dumps({"text": text, "entities": entities})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def cluster_documents(self, documents: list[str], num_clusters: int = 3) -> str:
        """Cluster documents by similarity."""
        if not self.clusterer:
            return json.dumps({"error": "DocumentClusterer not available"})
        try:
            clusters = self.clusterer.cluster(documents, num_clusters)
            return json.dumps({"num_documents": len(documents), "clusters": clusters})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def process_nlp_pipeline(self, text: str, steps: list[str] | None = None) -> str:
        """Process text through NLP pipeline."""
        if not self.nlp_pipeline:
            return json.dumps({"error": "NLPPipeline not available"})
        try:
            if steps is None:
                steps = ["tokenize", "tag", "parse", "ner"]
            result = self.nlp_pipeline.process(text, steps)
            return json.dumps({"text": text, "steps": steps, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return NLPCoreExtension(manifest, nexus_api)
