import dataclasses
import hashlib
import json
import logging
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from urllib import parse


import pydantic
from gateway import hardware_security, nexus_db, session_manager

# Ensure SME is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import SME core components

# Configure logging
logger = logging.getLogger("scrapegraph_harvester")

# Try to import ScrapeGraphAI and dependencies
SCRAPEGRAPH_AVAILABLE = False

try:
    from scrapegraphai import graphs
    SCRAPEGRAPH_AVAILABLE = True
    logger.info("ScrapeGraphAI dependencies available")
except ImportError as e:
    logger.warning(f"ScrapeGraphAI dependencies not available: {e}")
    graphs = None


# Pydantic schemas for tool validation
class ScrapeRequest(pydantic.BaseModel):
    url: str = pydantic.Field(..., min_length=1, description="URL to scrape")
    prompt: str = pydantic.Field(default="Extract all forensic evidence", description="Extraction prompt")
    model: str = pydantic.Field(default="ollama/llama3.2", description="LLM model to use")
    
    @pydantic.validator('url')
    def validate_url(cls, v):
        """Validate that the URL is well-formed and safe"""
        try:
            parsed = parse.urlparse(v)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("Invalid URL format")
            
            # Block potentially dangerous schemes
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP/HTTPS URLs are allowed")
            
            # Basic security checks
            if any(pattern in v.lower() for pattern in ['localhost', '127.0.0.1', 'file://']):
                raise ValueError("Local and file URLs are not allowed for security reasons")
                
            return v
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")

class ResearchRequest(pydantic.BaseModel):
    query: str = pydantic.Field(..., min_length=1, max_length=500, description="Search query")
    results_count: int = pydantic.Field(default=10, ge=1, le=20, description="Number of results to synthesize")
    model: str = pydantic.Field(default="ollama/llama3.2", description="LLM model to use")
    
    @pydantic.validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

class MarkdownifyRequest(pydantic.BaseModel):
    url: str = pydantic.Field(..., min_length=1, description="URL to convert to Markdown")
    model: str = pydantic.Field(default="ollama/llama3.2", description="LLM model to use")
    
    @pydantic.validator('url')
    def validate_url(cls, v):
        """Validate that the URL is well-formed and safe"""
        try:
            parsed = parse.urlparse(v)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError("Invalid URL format")
            
            # Block potentially dangerous schemes
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP/HTTPS URLs are allowed")
            
            # Basic security checks
            if any(pattern in v.lower() for pattern in ['localhost', '127.0.0.1', 'file://']):
                raise ValueError("Local and file URLs are not allowed for security reasons")
                
            return v
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")

@dataclasses.dataclass
class MemoryNode:
    id: str
    content: str
    source_url: str
    timestamp: str
    trust_score: float
    entities: list[str]
    relationships: list[dict[str, Any]]

class ScrapeGraphHarvester:
    """
    Main plugin class for ScrapeGraphAI integration with SME.
    Handles agentic scraping, research, and Markdown conversion.
    """
    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus_api = nexus_api
        self.hsm = hardware_security.get_hsm()
        self.nexus = nexus_db.get_nexus()
        self.session_manager = session_manager.get_session_manager()
        self.category = "forensics"

        # VRAM-optimized model configuration with timeouts
        self.default_config = {
            "llm": {
                "model": "ollama/llama3.2",
                "temperature": 0.0,
                "format": "json",
                "base_url": "http://ollama:11434",
                "max_tokens": 4096,
                "timeout": 120  # 2 minute timeout
            },
            "embeddings": {
                "model": "ollama/nomic-embed-text",
                "base_url": "http://ollama:11434"
            },
            "headless": True,
            "max_concurrent_requests": 2,
            "scraping_timeout": 60,  # 1 minute timeout for scraping
            "max_retries": 3
        }

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests

        logger.info("ScrapeGraphAI Harvester initialized with VRAM-optimized configuration")

    async def scrape_and_remember(self, request: ScrapeRequest) -> dict[str, Any]:
        """
        Extract forensic evidence from a URL using agentic scraping and store in memory.
        """
        if not SCRAPEGRAPH_AVAILABLE:
            return {"error": "ScrapeGraphAI dependencies not installed", "status": "error"}

        try:
            # Configure graph with user model or default
            config = self.default_config.copy()
            config["llm"] = config["llm"].copy()
            config["llm"]["model"] = request.model

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

    async def deep_research(self, request: ResearchRequest) -> dict[str, Any]:
        """
        Search the web for a topic and synthesize findings into structured memory nodes.
        """
        if not SCRAPEGRAPH_AVAILABLE:
            return {"error": "ScrapeGraphAI dependencies not installed", "status": "error"}

        try:
            # Configure graph with user model or default
            config = self.default_config.copy()
            config["llm"] = config["llm"].copy()
            config["llm"]["model"] = request.model

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

    async def markdownify(self, request: MarkdownifyRequest) -> dict[str, Any]:
        """
        Convert any URL to clean Markdown for semantic memory indexing.
        """
        if not SCRAPEGRAPH_AVAILABLE:
            return {"error": "ScrapeGraphAI dependencies not installed", "status": "error"}

        try:
            # Configure graph with user model or default
            config = self.default_config.copy()
            config["llm"] = config["llm"].copy()
            config["llm"]["model"] = request.model

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
    def _process_scraped_results(self, result: Any, source_url: str) -> list[MemoryNode]:
        """
        Process SmartScraperGraph results into structured memory nodes.
        """
        nodes = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract entities and relationships from the result
        entities = self._extract_entities(result)
        relationships = self._extract_relationships(result)

        # Create memory nodes from the extracted data
        for item in result.data:
            # Generate unique node ID using content hash and timestamp to prevent collisions
            content_hash = hashlib.sha256(item['content'].encode('utf-8')).hexdigest()[:12]
            node_id = f"scrape_{content_hash}_{int(time.time())}"
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

    def _process_search_results(self, result: Any, query: str) -> list[MemoryNode]:
        """
        Process SearchGraph results into structured memory nodes.
        """
        nodes = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract entities and relationships from the result
        entities = self._extract_entities(result)
        relationships = self._extract_relationships(result)

        # Create memory nodes from the search results
        for item in result.results:
            # Generate unique node ID using title hash and timestamp
            title_hash = hashlib.sha256(item['title'].encode('utf-8')).hexdigest()[:12]
            node_id = f"research_{title_hash}_{int(time.time())}"
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

    def _process_markdown_results(self, result: Any, source_url: str) -> list[MemoryNode]:
        """
        Process MarkdownifyGraph results into structured memory nodes.
        """
        nodes = []
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract entities and relationships from the result
        entities = self._extract_entities(result)
        relationships = self._extract_relationships(result)

        # Create a single memory node for the Markdown content
        markdown_hash = hashlib.sha256(result.markdown.encode('utf-8')).hexdigest()[:12]
        node_id = f"markdown_{markdown_hash}_{int(time.time())}"
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

    def _extract_entities(self, result: Any) -> list[str]:
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

    def _extract_relationships(self, result: Any) -> list[dict[str, Any]]:
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

    def _calculate_trust_score(self, item: dict[str, Any], source_url: str) -> float:
        """
        Calculate a sophisticated trust score for the scraped content.
        """
        trust_components = {
            'source_reputation': 0.0,
            'content_quality': 0.0,
            'structure_validity': 0.0,
            'freshness': 0.0
        }
        
        # 1. Source reputation scoring
        domain = parse.urlparse(source_url).netloc.lower()
        if any(d in domain for d in ['wikipedia.org', 'wikimedia.org']):
            trust_components['source_reputation'] = 0.4
        elif any(d in domain for d in ['.gov', '.edu']):
            trust_components['source_reputation'] = 0.35
        elif any(d in domain for d in ['.org', '.net']):
            trust_components['source_reputation'] = 0.25
        elif '.com' in domain:
            trust_components['source_reputation'] = 0.15
        else:
            trust_components['source_reputation'] = 0.1

        # 2. Content quality scoring
        content = item.get('content', '')
        content_length = len(content)
        
        if content_length == 0:
            trust_components['content_quality'] = 0.0
        elif content_length < 100:
            trust_components['content_quality'] = 0.1
        elif content_length < 500:
            trust_components['content_quality'] = 0.3
        elif content_length < 1000:
            trust_components['content_quality'] = 0.5
        elif content_length < 5000:
            trust_components['content_quality'] = 0.7
        else:
            trust_components['content_quality'] = 0.8

        # 3. Structure validity scoring
        structure_score = 0.0
        if content:
            # Check for proper HTML structure
            if any(tag in content.lower() for tag in ['<h1>', '<h2>', '<p>', '<div>']):
                structure_score += 0.2
            # Check for links
            if 'http' in content:
                structure_score += 0.1
            # Check for metadata indicators
            if any(meta in content.lower() for meta in ['published', 'author', 'date', 'source']):
                structure_score += 0.1
        
        trust_components['structure_validity'] = structure_score

        # 4. Freshness scoring (if available)
        # This would be enhanced if we had access to HTTP headers or metadata
        trust_components['freshness'] = 0.1  # Base freshness score

        # Calculate weighted average
        weights = {
            'source_reputation': 0.4,
            'content_quality': 0.35,
            'structure_validity': 0.15,
            'freshness': 0.1
        }
        
        weighted_score = sum(
            trust_components[component] * weights[component] 
            for component in trust_components
        )
        
        # Apply logarithmic scaling to prevent extreme scores
        final_score = min(0.95, max(0.05, weighted_score))
        
        return round(final_score, 2)

    def _store_memory_nodes(self, nodes: list[MemoryNode]) -> None:
        """
        Store memory nodes in the SME database with batch operations and error handling.
        """
        if not nodes:
            return

        # Batch insert for better performance
        batch_data = []
        for node in nodes:
            try:
                # Validate node data before insertion
                if not all([node.id, node.content, node.source_url, node.timestamp]):
                    logger.warning(f"Skipping invalid node {node.id}: missing required fields")
                    continue

                # Calculate content hash for HSM signing
                content_hash = hashlib.sha256(node.content.encode('utf-8')).hexdigest()
                
                batch_data.append((
                    node.id,
                    node.content,
                    node.source_url,
                    node.timestamp,
                    node.trust_score,
                    json.dumps(node.entities),
                    json.dumps(node.relationships)
                ))

                # Sign the evidence with HSM
                self.hsm.sign_evidence(
                    source_id=node.id,
                    data_hash=content_hash
                )

            except Exception as e:
                logger.exception(f"Failed to prepare node {node.id} for storage: {e}")
                continue

        if batch_data:
            try:
                # Use batch insert for better performance
                for node_data in batch_data:
                    try:
                        self.nexus.execute("""
                            INSERT INTO nexus.memory_nodes 
                            (node_id, content, source_url, timestamp, trust_score, entities, relationships)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(node_id) DO UPDATE SET
                                content = excluded.content,
                                source_url = excluded.source_url,
                                timestamp = excluded.timestamp,
                                trust_score = excluded.trust_score,
                                entities = excluded.entities,
                                relationships = excluded.relationships
                        """, node_data)
                    except Exception as batch_e:
                        logger.exception(f"Batch insert failed for node {node_data[0]}: {batch_e}")
                        # Fallback to individual insert
                        try:
                            self.nexus.execute("""
                                INSERT INTO nexus.memory_nodes 
                                (node_id, content, source_url, timestamp, trust_score, entities, relationships)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, node_data)
                        except Exception as fallback_e:
                            logger.exception(f"Fallback insert failed for node {node_data[0]}: {fallback_e}")
                
                logger.info(f"Successfully stored {len(batch_data)} memory nodes")

            except Exception as e:
                logger.exception(f"Failed to store memory nodes: {e}")

    # Extension contract methods
    def get_tools(self) -> dict[str, Any]:
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

    def on_ingestion(self, raw_data: str, metadata: dict[str, Any]) -> None:
        """
        Called when new data is ingested into the system.
        """
        logger.debug(f"New ingestion event: {metadata.get('type', 'unknown')}")
