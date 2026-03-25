import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.AnalysisCore")

try:
    from src.analysis.engine import SentimentIntensityAnalyzer as AnalysisEngine
except (ImportError, ModuleNotFoundError):
    AnalysisEngine = None

try:
    from src.analysis.comparisons import DocumentComparison
except (ImportError, ModuleNotFoundError):
    DocumentComparison = None

try:
    from src.analysis.knowledge_graph import KnowledgeGraphOperations
except (ImportError, ModuleNotFoundError):
    KnowledgeGraphOperations = None

try:
    from src.analysis.overlap_discovery import OverlapDiscovery
except (ImportError, ModuleNotFoundError):
    OverlapDiscovery = None

try:
    from src.analysis.correlator import DataCorrelator
except (ImportError, ModuleNotFoundError):
    DataCorrelator = None

try:
    from src.analysis.rhetoric import RhetoricalAnalyzer
except (ImportError, ModuleNotFoundError):
    RhetoricalAnalyzer = None

try:
    from src.analysis.polars_forensics import PolarsForensics
except (ImportError, ModuleNotFoundError):
    PolarsForensics = None

try:
    from src.analysis.intelligence_reports import IntelligenceReporter
except (ImportError, ModuleNotFoundError):
    IntelligenceReporter = None

try:
    from src.analysis.federation_gate import FederationGate
except (ImportError, ModuleNotFoundError):
    FederationGate = None


class AnalysisCoreExtension(BasePlugin):
    """
    Analysis Core Extension for SME.
    Provides analysis engine, document comparison, knowledge graph operations, semantic overlap detection, data correlation, rhetorical analysis, polars forensics, intelligence reporting, and federation gate control.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.engine = AnalysisEngine() if AnalysisEngine else None
        self.comparison = DocumentComparison() if DocumentComparison else None
        self.kg = KnowledgeGraphOperations() if KnowledgeGraphOperations else None
        self.overlap = OverlapDiscovery() if OverlapDiscovery else None
        self.correlator = DataCorrelator() if DataCorrelator else None
        self.rhetoric = RhetoricalAnalyzer() if RhetoricalAnalyzer else None
        self.polars = PolarsForensics() if PolarsForensics else None
        self.reporter = IntelligenceReporter() if IntelligenceReporter else None
        self.federation = FederationGate() if FederationGate else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Analysis Core extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.run_analysis,
            self.compare_documents,
            self.kg_operations,
            self.detect_overlap,
            self.correlate_data,
            self.analyze_rhetoric,
            self.polars_analyze,
            self.generate_report,
            self.federation_control,
        ]

    async def run_analysis(self, data: Any, analysis_type: str) -> str:
        """Run analysis on data."""
        if not self.engine:
            return json.dumps({"error": "AnalysisEngine not available"})
        try:
            result = self.engine.analyze(data, analysis_type)
            return json.dumps({"analysis_type": analysis_type, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def compare_documents(self, doc1: str, doc2: str, mode: str = "full") -> str:
        """Compare two documents."""
        if not self.comparison:
            return json.dumps({"error": "DocumentComparison not available"})
        try:
            result = self.comparison.compare(doc1, doc2, mode)
            return json.dumps({"mode": mode, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def kg_operations(self, operation: str, params: dict) -> str:
        """Perform knowledge graph operations."""
        if not self.kg:
            return json.dumps({"error": "KnowledgeGraphOperations not available"})
        try:
            result = self.kg.operate(operation, params)
            return json.dumps({"operation": operation, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def detect_overlap(self, documents: list[str], threshold: float = 0.8) -> str:
        """Detect semantic overlap between documents."""
        if not self.overlap:
            return json.dumps({"error": "OverlapDiscovery not available"})
        try:
            result = self.overlap.detect(documents, threshold)
            return json.dumps(
                {"num_documents": len(documents), "threshold": threshold, "result": result}
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def correlate_data(self, sources: list[str], correlation_type: str = "pearson") -> str:
        """Correlate data from multiple sources."""
        if not self.correlator:
            return json.dumps({"error": "DataCorrelator not available"})
        try:
            result = self.correlator.correlate(sources, correlation_type)
            return json.dumps(
                {
                    "num_sources": len(sources),
                    "correlation_type": correlation_type,
                    "result": result,
                }
            )
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def analyze_rhetoric(self, text: str) -> str:
        """Analyze rhetorical patterns in text."""
        if not self.rhetoric:
            return json.dumps({"error": "RhetoricalAnalyzer not available"})
        try:
            result = self.rhetoric.analyze(text)
            return json.dumps({"text_length": len(text), "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def polars_analyze(self, data: Any, query: str) -> str:
        """Analyze data using Polars high-performance queries."""
        if not self.polars:
            return json.dumps({"error": "PolarsForensics not available"})
        try:
            result = self.polars.analyze(data, query)
            return json.dumps({"query": query, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def generate_report(self, data: Any, template: str = "standard") -> str:
        """Generate intelligence report."""
        if not self.reporter:
            return json.dumps({"error": "IntelligenceReporter not available"})
        try:
            report = self.reporter.generate(data, template)
            return json.dumps({"template": template, "report": report})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def federation_control(self, action: str, system_id: str, params: dict = None) -> str:
        """Control inter-system federation gate."""
        if not self.federation:
            return json.dumps({"error": "FederationGate not available"})
        try:
            result = self.federation.control(action, system_id, params)
            return json.dumps({"action": action, "system_id": system_id, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return AnalysisCoreExtension(manifest, nexus_api)
