"""
Gateway Tool Modules - Organized tool registry by domain.

This module replaces the monolithic tool_registry.py TOOL_DEFINITIONS
with focused, maintainable modules organized by function.

Module Structure:
- diagnostics: System health, monitoring, diagnostics
- query: Semantic search, knowledge graph queries
- memory: Knowledge persistence, session management
- utilities: General purpose tools, auth, health checks
"""

from gateway.tools.diagnostics import DIAGNOSTIC_TOOLS
from gateway.tools.memory import MEMORY_TOOLS
from gateway.tools.query import QUERY_TOOLS

__all__ = ["DIAGNOSTIC_TOOLS", "MEMORY_TOOLS", "QUERY_TOOLS"]


def get_all_tools() -> dict:
    """Get all registered tools from all modules."""
    tools = {}
    tools.update(DIAGNOSTIC_TOOLS)
    tools.update(QUERY_TOOLS)
    tools.update(MEMORY_TOOLS)
    return tools
