"""
Tests for gateway/tools/query.py - Query tool definitions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from gateway.tool_registry import ToolDefinition
from gateway.tools.query import QUERY_TOOLS


def test_query_tools_keys():
    expected = ["semantic_search", "query_knowledge", "resolve_concept", "entity_extractor"]
    for key in expected:
        assert key in QUERY_TOOLS


def test_semantic_search_definition():
    tool: ToolDefinition = QUERY_TOOLS["semantic_search"]
    assert tool.name == "semantic_search"
    assert tool.category == "query"
    assert tool.factory_method == "create_search_engine"
    assert tool.parameters == {"query": "str", "limit": "int"}


def test_query_knowledge_definition():
    tool = QUERY_TOOLS["query_knowledge"]
    assert tool.factory_method == "create_scout"


def test_resolve_concept_definition():
    tool = QUERY_TOOLS["resolve_concept"]
    assert tool.factory_method == "create_concept_resolver"


def test_entity_extractor_definition():
    tool = QUERY_TOOLS["entity_extractor"]
    assert tool.category == "query"
    assert tool.parameters["text"] == "str"
