"""
Tool Registry - Dynamic Discovery and Registration for SME Tools

This module provides automatic discovery and registration of all SME
ToolFactory methods as MCP-callable tools.

Usage:
    from gateway.tool_registry import ToolRegistry
    
    registry = ToolRegistry()
    tools = registry.get_all_tools()
"""

import sys
import os
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from functools import wraps
import logging

# Ensure SME src is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Metadata for an MCP-exposed tool."""
    name: str
    description: str
    factory_method: str
    category: str
    parameters: Dict[str, Any]


class ToolRegistry:
    """
    Central registry for discovering and managing SME tools.
    
    Maps ToolFactory methods to MCP tool definitions with metadata
    for documentation and validation.
    """
    
    # Tool definitions mapping MCP names to ToolFactory methods
    TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
        # ===== TIER 1: Core Tools (Sprint 1) =====
        "verify_system": ToolDefinition(
            name="verify_system",
            description="Check system health: CPU, RAM, database status, and data integrity",
            factory_method="create_system_monitor",
            category="diagnostics",
            parameters={}
        ),
        "semantic_search": ToolDefinition(
            name="semantic_search",
            description="Search the knowledge base using semantic vector similarity",
            factory_method="create_search_engine",
            category="query",
            parameters={"query": "str", "limit": "int"}
        ),
        "query_knowledge": ToolDefinition(
            name="query_knowledge",
            description="Query the knowledge graph for related concepts",
            factory_method="create_scout",
            category="query",
            parameters={"concept": "str"}
        ),
        "save_memory": ToolDefinition(
            name="save_memory",
            description="Persist a new fact or insight to the knowledge base",
            factory_method="create_synapse",
            category="memory",
            parameters={"fact": "str", "source": "str"}
        ),
        "get_memory_stats": ToolDefinition(
            name="get_memory_stats",
            description="Get statistics about stored knowledge: facts, vectors, entries",
            factory_method="create_centrifuge",
            category="diagnostics",
            parameters={}
        ),
        
        # ===== TIER 2: Forensic Tools (Sprint 2) =====
        "analyze_authorship": ToolDefinition(
            name="analyze_authorship",
            description="Extract linguistic fingerprint for authorship attribution",
            factory_method="create_scribe",
            category="forensics",
            parameters={"text": "str", "author_id": "str"}
        ),
        "analyze_sentiment": ToolDefinition(
            name="analyze_sentiment",
            description="Detect emotions, sarcasm, and sentiment in text",
            factory_method="create_sentiment_analyzer",
            category="analysis",
            parameters={"text": "str"}
        ),
        "link_entities": ToolDefinition(
            name="link_entities",
            description="Extract and link entities to knowledge bases",
            factory_method="create_entity_linker",
            category="analysis",
            parameters={"text": "str"}
        ),
        "summarize_text": ToolDefinition(
            name="summarize_text",
            description="Summarize text using extractive, abstractive, or query-focused modes",
            factory_method="create_text_summarizer",
            category="analysis",
            parameters={"text": "str", "mode": "str", "max_sentences": "int"}
        ),
        
        # ===== TIER 3: Advanced Tools (Sprint 3) =====
        "cluster_documents": ToolDefinition(
            name="cluster_documents",
            description="Cluster documents by semantic similarity",
            factory_method="create_document_clusterer",
            category="analysis",
            parameters={"documents": "list", "algorithm": "str"}
        ),
        "build_knowledge_graph": ToolDefinition(
            name="build_knowledge_graph",
            description="Build semantic graph from concepts and relationships",
            factory_method="create_semantic_graph",
            category="graph",
            parameters={"concepts": "list"}
        ),
        "verify_facts": ToolDefinition(
            name="verify_facts",
            description="Verify claims against the knowledge base",
            factory_method="create_fact_verifier",
            category="forensics",
            parameters={"claim": "str"}
        ),
        "analyze_nlp": ToolDefinition(
            name="analyze_nlp",
            description="Deep NLP analysis: dependencies, coreference, semantic roles",
            factory_method="create_nlp_pipeline",
            category="analysis",
            parameters={"text": "str"}
        ),
        "detect_networks": ToolDefinition(
            name="detect_networks",
            description="Detect coordinated sockpuppet networks",
            factory_method="create_network_generator",
            category="forensics",
            parameters={"authors": "list"}
        ),
        "resolve_concept": ToolDefinition(
            name="resolve_concept",
            description="Map ambiguous terms to specific knowledge graph nodes",
            factory_method="create_concept_resolver",
            category="query",
            parameters={"term": "str"}
        ),
        "generate_intelligence_report": ToolDefinition(
            name="generate_intelligence_report",
            description="Aggregate findings into a structured forensic report",
            factory_method="create_intelligence_reports",
            category="analysis",
            parameters={"subject": "str", "findings": "list"}
        ),
        "discover_overlap": ToolDefinition(
            name="discover_overlap",
            description="Find shared rhetorical signals between different authors",
            factory_method="create_overlap_discovery",
            category="forensics",
            parameters={"author_ids": "list"}
        ),
        "analyze_rolling_delta": ToolDefinition(
            name="analyze_rolling_delta",
            description="Temporal stylometric analysis of writing style evolution",
            factory_method="create_rolling_delta",
            category="analysis",
            parameters={"text": "str", "window_size": "int"}
        ),
    }
    
    def __init__(self):
        self._tool_instances: Dict[str, Any] = {}
        self._factory = None
        
    def _get_factory(self):
        """Lazy-load the ToolFactory to avoid import issues."""
        if self._factory is None:
            try:
                from src.core.factory import ToolFactory
                self._factory = ToolFactory
                logger.info("ToolFactory loaded successfully")
            except ImportError as e:
                logger.error(f"Failed to import ToolFactory: {e}")
                raise
        return self._factory
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get or create a tool instance by name.
        
        Uses singleton pattern to cache expensive tool instances.
        
        Args:
            tool_name: The MCP tool name (e.g., 'semantic_search')
            
        Returns:
            The tool instance, or None if not found
        """
        if tool_name not in self.TOOL_DEFINITIONS:
            logger.warning(f"Unknown tool requested: {tool_name}")
            return None
            
        if tool_name not in self._tool_instances:
            definition = self.TOOL_DEFINITIONS[tool_name]
            factory = self._get_factory()
            
            # Get the factory method by name
            factory_method = getattr(factory, definition.factory_method, None)
            if factory_method is None:
                logger.error(f"Factory method not found: {definition.factory_method}")
                return None
                
            try:
                self._tool_instances[tool_name] = factory_method()
                logger.info(f"Created tool instance: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to create tool {tool_name}: {e}")
                return None
                
        return self._tool_instances[tool_name]
    
    def list_tools(self, category: Optional[str] = None) -> list:
        """
        List available tools, optionally filtered by category.
        
        Args:
            category: Filter by category (diagnostics, query, memory, forensics, analysis)
            
        Returns:
            List of tool definitions
        """
        tools = list(self.TOOL_DEFINITIONS.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get metadata for a specific tool."""
        return self.TOOL_DEFINITIONS.get(tool_name)
    
    def get_categories(self) -> list:
        """Get all unique tool categories."""
        return list(set(t.category for t in self.TOOL_DEFINITIONS.values()))
    
    def reset(self, tool_name: Optional[str] = None):
        """
        Clear cached tool instances.
        
        Args:
            tool_name: Specific tool to reset, or None for all tools
        """
        if tool_name:
            self._tool_instances.pop(tool_name, None)
        else:
            self._tool_instances.clear()
        logger.info(f"Reset tool cache: {tool_name or 'all'}")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global ToolRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
