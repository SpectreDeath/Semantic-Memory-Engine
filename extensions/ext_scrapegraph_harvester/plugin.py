import dataclasses
import json
import logging
import pathlib
import sys
from datetime import datetime
from typing import Any, List

import pydantic
from pydantic import types
from scrapegraphai import graphs
from scrapegraphai import config as config_mod

from gateway import hardware_security, nexus_db, session_manager
from src.core import chroma_indexer

# Ensure SME is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import SME core components

# Configure logging
logger = logging.getLogger("scrapegraph_harvester")

# Try to import ScrapeGraphAI and dependencies
try:
    SCRAPEGRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ScrapeGraphAI dependencies not available: {e}")
    SCRAPEGRAPH_AVAILABLE = False


# Pydantic schemas for tool validation
class ScrapeRequest(pydantic.BaseModel):
    url: types.constr(min_length=1) = pydantic.Field(..., description="URL to scrape")
    prompt: str = pydantic.Field(default="Extract all forensic evidence", description="Extraction prompt")
    model: str = pydantic.Field(default="ollama/llama3.2", description="LLM model to use")

class ResearchRequest(pydantic.BaseModel):
    query: types.constr(min_length=1) = pydantic.Field(..., description="Search query")
    results_count: int = pydantic.Field(default=10, ge=1, le=20, description="Number of results to synthesize")
    model: str = pydantic.Field(default="ollama/llama3.2", description="LLM model to use")

class MarkdownifyRequest(pydantic.BaseModel):
    url: types.constr(min_length=1) = pydantic.Field(..., description="URL to convert to Markdown")
    model: str = pydantic.Field(default="ollama/llama3.2", description="LLM model to use")

@dataclasses.dataclass
class MemoryNode:
    id: str
    content: str
    source_url: str
    timestamp: str
    trust_score: float
    entities: List[str]
    relationships: List[Dict[str, Any]]

class ScrapeGraphHarvester:
    """
    Main plugin class for ScrapeGraphAI integration with SME.
    Handles agentic scraping, research, and Markdown conversion.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus_api = nexus_api
        self.hsm = hardware_security.get_hsm()
        self.nexus = nexus_db.get_nexus()
        self.session_manager = session_manager.get_session_manager()
        self.category = "forensics"
        
        # VRAM-optimized model configuration
        self.default_config = config_mod.GraphConfig(
            llm={
                "model": "ollama/llama3.2",
                "temperature": 0.0,
                "format": "json",
                "base_url": "http://ollama:11434",
                "max_tokens": 4096
            },
            embeddings={
                "model": "ollama/nomic-embed-text",
                "base_url": "http://ollama:11434"
            },
            headless=True,
            max_concurrent_requests=2
        )
        
        logger.info("ScrapeGraphAI Harvester initialized with VRAM-optimized configuration")

    async def scrape_and_remember(self, request: ScrapeRequest) -> Dict[str, Any]:
        """
        Extract forensic evidence from a URL using agentic scraping and store in memory.
        """
        if not SCRAPEGRAPH_AVAILABLE:
            return {"error": "ScrapeGraphAI dependencies not installed", "status": "error"}

        try:
            # Configure graph with user model or default
            config = self.default_config._replace(
                llm=self.default_config.llm._replace(model=request.model)
            )

            # Create and run the SmartScraperGraph
            graph = graphs.SmartScraperGraph(
                prompt=request.prompt,
                source=request.url,
                config=config
            )

            result = await graph.run()

            # Process and store the results
            memory_nodes = self._process_scraped_results(result, request.url)
            self._store_memory_nodes(memory_nodes)

            return {
                "status": "success",
                "url": request.url,
                "prompt": request.prompt,
                "model": request.model,
                "nodes_created": len(memory_nodes),
                "entities_extracted": len(set(e for node in memory_nodes for e in node.entities)),
                "trust_score": round(sum(n.trust_score for n in memory_nodes) / len(memory_nodes), 2)
            }

        except Exception as e:
            logger.error(f"Scrape error: {e}")
            return {"error": str(e), "status": "error"}

    async def deep_research(self, request: ResearchRequest) -> Dict[str, Any]:
        """
        Search the web for a topic and synthesize findings into structured memory nodes.
        """
        if not SCRAPEGRAPH_AVAILABLE:
            return {"error": "ScrapeGraphAI dependencies not installed", "status": "error"}

        try:
            # Configure graph with user model or default
            config = self.default_config._replace(
                llm=self.default_config.llm._replace(model=request.model)
            )

            # Create and run the SearchGraph
            graph = graphs.SearchGraph(
                query=request.query,
                config=config
            )

            result = await graph.run()

            # Process and store the results
            memory_nodes = self._process_search_results(result, request.query)
            self._store_memory_nodes(memory_nodes)

            return {
                "status": "success",
                "query": request.query,
                "model": request.model,
                "results_count": len(result.results),
                "nodes_created": len(memory_nodes),
                "entities_extracted": len(set(e for node in memory_nodes for e in node.entities)),
                "trust_score": round(sum(n.trust_score for n in memory_nodes) / len(memory_nodes), 2)
            }

        except Exception as e:
            logger.error(f"Research error: {e}")
            return {"error": str(e), "status": "error"}

    async def markdownify(self, request: MarkdownifyRequest) -> Dict[str, Any]:
        """
        Convert any URL to clean Markdown for semantic memory indexing.
        """
        if not SCRAPEGRAPH_AVAILABLE:
            return {"error": "ScrapeGraphAI dependencies not installed", "status": "error"}

        try:
            # Configure graph with user model or default
            config = self.default_config._replace(
                llm=self.default_config.llm._replace(model=request.model)
            )

            # Create and run the MarkdownifyGraph
            graph = graphs.MarkdownifyGraph(
                source=request.url,
                config=config
            )

            result = await graph.run()

            # Process and store the results
            memory_nodes = self._process_markdown_results(result, request.url)
            self._store_memory_nodes(memory_nodes)

            return {
                "status": "success",
                "url": request.url,
                "model": request.model,
                "markdown_length": len(result.markdown),
                "nodes_created": len(memory_nodes),
                "entities_extracted": len(set(e for node in memory_nodes for e in node.entities)),
                "trust_score": round(sum(n.trust_score for n in memory_nodes) / len(memory_nodes), 2)
            }

        except Exception as e:
            logger.error(f"Markdownify error: {e}")
            return {"error": str(e), "status": "error"}

    # Helper methods for processing and storing results
    def _process_scraped_results(self, result: Any, source_url: str) -> List[MemoryNode]:
        """
        Process SmartScraperGraph results into structured memory nodes.
        """
        nodes = []
        timestamp = datetime.now().isoformat()

        # Extract entities and relationships from the result
        entities = self._extract_entities(result)
        relationships = self._extract_relationships(result)

        # Create memory nodes from the extracted data
        for item in result.data:
            node_id = f"scrape_{hash(item['content']) % 1000000}"
            trust_score = self._calculate_trust_score(item, source_url)
            
            nodes.append(MemoryNode(
                id=node_id,
                content=item['content'],
                source_url=source_url,
                timestamp=timestamp,
                trust_score=trust_score,
                entities=entities,
                relationships=relationships
            ))

        return nodes

    def _process_search_results(self, result: Any, query: str) -> List[MemoryNode]:
        """
        Process SearchGraph results into structured memory nodes.
        """
        nodes = []
        timestamp = datetime.now().isoformat()

        # Extract entities and relationships from the result
        entities = self._extract_entities(result)
        relationships = self._extract_relationships(result)

        # Create memory nodes from the search results
        for item in result.results:
            node_id = f"research_{hash(item['title']) % 1000000}"
            trust_score = self._calculate_trust_score(item, item['url'])
            
            content = f"## {item['title']}\n\n{item['snippet']}\n\n**Source**: {item['url']}\n\n{item['content']}"
            
            nodes.append(MemoryNode(
                id=node_id,
                content=content,
                source_url=item['url'],
                timestamp=timestamp,
                trust_score=trust_score,
                entities=entities,
                relationships=relationships
            ))

        return nodes

    def _process_markdown_results(self, result: Any, source_url: str) -> List[MemoryNode]:
        """
        Process MarkdownifyGraph results into structured memory nodes.
        """
        nodes = []
        timestamp = datetime.now().isoformat()

        # Extract entities and relationships from the result
        entities = self._extract_entities(result)
        relationships = self._extract_relationships(result)

        # Create a single memory node for the Markdown content
        node_id = f"markdown_{hash(result.markdown) % 1000000}"
        trust_score = self._calculate_trust_score(result, source_url)
        
        nodes.append(MemoryNode(
            id=node_id,
            content=result.markdown,
            source_url=source_url,
            timestamp=timestamp,
            trust_score=trust_score,
            entities=entities,
            relationships=relationships
        ))

        return nodes

    def _extract_entities(self, result: Any) -> List[str]:
        """
        Extract named entities from the scraping result.
        """
        entities = []
        try:
            # Try to extract entities from the result structure
            if hasattr(result, 'entities'):
                entities = result.entities
            elif hasattr(result, 'data'):
                for item in result.data:
                    if 'entities' in item:
                        entities.extend(item['entities'])
        except Exception:
            pass

        return list(set(entities))[:10]  # Limit to top 10 entities

    def _extract_relationships(self, result: Any) -> List[Dict[str, Any]]:
        """
        Extract relationships from the scraping result.
        """
        relationships = []
        try:
            # Try to extract relationships from the result structure
            if hasattr(result, 'relationships'):
                relationships = result.relationships
            elif hasattr(result, 'data'):
                for item in result.data:
                    if 'relationships' in item:
                        relationships.extend(item['relationships'])
        except Exception:
            pass

        return relationships[:5]  # Limit to top 5 relationships

    def _calculate_trust_score(self, item: Dict[str, Any], source_url: str) -> float:
        """
        Calculate a trust score for the scraped content.
        """
        # Simple trust scoring based on source and content quality
        base_score = 0.5  # Neutral baseline

        # Add points for reputable sources
        if "wikipedia.org" in source_url:
            base_score += 0.2
        elif "gov" in source_url or "edu" in source_url:
            base_score += 0.3

        # Add points for content length (more content = more trustworthy)
        content_length = len(item.get('content', ''))
        if content_length > 500:
            base_score += 0.1
        elif content_length > 1000:
            base_score += 0.2

        # Cap the score between 0 and 1
        return max(0.0, min(1.0, base_score))

    def _store_memory_nodes(self, nodes: List[MemoryNode]) -> None:
        """
        Store memory nodes in the SME database and index in ChromaDB.
        """
        for node in nodes:
            try:
                # Store in PostgreSQL Nexus
                self.nexus.execute("""
                    INSERT INTO nexus.memory_nodes 
                    (node_id, content, source_url, timestamp, trust_score, entities, relationships)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    node.id,
                    node.content,
                    node.source_url,
                    node.timestamp,
                    node.trust_score,
                    json.dumps(node.entities),
                    json.dumps(node.relationships)
                ))

                # Index in ChromaDB (if available)
                try:
                    indexer = chroma_indexer.ChromaIndexer()
                    indexer.index_node(node.id, node.content)
                except Exception:
                    pass

                # Sign the evidence with HSM
                self.hsm.sign_evidence({
                    "node_id": node.id,
                    "content_hash": hash(node.content),
                    "source_url": node.source_url,
                    "timestamp": node.timestamp
                })

            except Exception as e:
                logger.error(f"Failed to store memory node {node.id}: {e}")

    # Extension contract methods
    def get_tools(self) -> Dict[str, Any]:
        """
        Return the tools provided by this extension.
        """
        return {
            "scrape_and_remember": self.scrape_and_remember,
            "deep_research": self.deep_research,
            "markdownify": self.markdownify
        }

    def on_startup(self) -> None:
        """
        Called when the extension is loaded.
        """
        logger.info("ScrapeGraphAI Harvester extension started successfully")

    def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]) -> None:
        """
        Called when new data is ingested into the system.
        """
        logger.debug(f"New ingestion event: {metadata.get('type', 'unknown')}")