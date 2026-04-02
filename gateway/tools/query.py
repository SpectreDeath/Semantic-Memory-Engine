"""Query Tools - Semantic search, knowledge graph, and query operations."""

from gateway.tool_registry import ToolDefinition

QUERY_TOOLS = {
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
    "resolve_concept": ToolDefinition(
        name="resolve_concept",
        description="Map ambiguous terms to specific knowledge graph nodes",
        factory_method="create_concept_resolver",
        category="query",
        parameters={"term": "str"}
    ),
    "entity_extractor": ToolDefinition(
        name="entity_extractor",
        description="Advanced entity cross-referencing against the 10GB ConceptNet knowledge graph.",
        factory_method="create_concept_resolver",
        category="query",
        parameters={"text": "str"}
    ),
}