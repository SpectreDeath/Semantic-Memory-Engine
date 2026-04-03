"""Diagnostic Tools - System health, monitoring, and diagnostics."""

from gateway.tool_registry import ToolDefinition

DIAGNOSTIC_TOOLS = {
    "verify_system": ToolDefinition(
        name="verify_system",
        description="Check system health: CPU, RAM, database status, and data integrity",
        factory_method="create_system_monitor",
        category="diagnostics",
        parameters={},
    ),
    "get_memory_stats": ToolDefinition(
        name="get_memory_stats",
        description="Get statistics about stored knowledge: facts, vectors, entries",
        factory_method="create_centrifuge",
        category="diagnostics",
        parameters={},
    ),
}
