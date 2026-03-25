import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.QueryEngine")

try:
    from src.query.engine import QueryEngine
except ImportError:
    QueryEngine = None

try:
    from src.query.scout import ScoutDiscovery
except ImportError:
    ScoutDiscovery = None

try:
    from src.query.verifier import QueryVerifier
except ImportError:
    QueryVerifier = None

try:
    from src.query.concept_resolver import ConceptResolver
except ImportError:
    ConceptResolver = None

try:
    from src.query.aifdb_connector import AIFDBConnector
except ImportError:
    AIFDBConnector = None


class QueryEngineExtension(BasePlugin):
    """
    Query Engine Extension for SME.
    Provides query engine, scout discovery, query verification, concept resolution, and AIFDB connector.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.engine = QueryEngine() if QueryEngine else None
        self.scout = ScoutDiscovery() if ScoutDiscovery else None
        self.verifier = QueryVerifier() if QueryVerifier else None
        self.concept = ConceptResolver() if ConceptResolver else None
        self.aifdb = AIFDBConnector() if AIFDBConnector else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Query Engine extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.execute_query,
            self.discovery_search,
            self.verify_query,
            self.resolve_concept,
            self.query_aifdb,
        ]

    async def execute_query(self, query: str, filters: dict = None) -> str:
        """Execute semantic query."""
        if not self.engine:
            return json.dumps({"error": "QueryEngine not available"})
        try:
            results = self.engine.query(query, filters)
            return json.dumps({"query": query, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def discovery_search(self, topic: str, depth: int = 3) -> str:
        """Perform exploratory search."""
        if not self.scout:
            return json.dumps({"error": "ScoutDiscovery not available"})
        try:
            results = self.scout.discover(topic, depth)
            return json.dumps({"topic": topic, "depth": depth, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def verify_query(self, query: str, expected_results: list) -> str:
        """Verify query returns expected results."""
        if not self.verifier:
            return json.dumps({"error": "QueryVerifier not available"})
        try:
            result = self.verifier.verify(query, expected_results)
            return json.dumps({"query": query, "verified": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def resolve_concept(self, ambiguous_term: str, context: str = None) -> str:
        """Resolve ambiguous concept to specific meaning."""
        if not self.concept:
            return json.dumps({"error": "ConceptResolver not available"})
        try:
            resolved = self.concept.resolve(ambiguous_term, context)
            return json.dumps({"term": ambiguous_term, "context": context, "resolved": resolved})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def query_aifdb(self, query: str, database: str = "default") -> str:
        """Query AI forensics database."""
        if not self.aifdb:
            return json.dumps({"error": "AIFDBConnector not available"})
        try:
            results = self.aifdb.query(query, database)
            return json.dumps({"query": query, "database": database, "results": results})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return QueryEngineExtension(manifest, nexus_api)
