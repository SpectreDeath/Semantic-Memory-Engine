"""Memory Tools - Knowledge base persistence and memory management."""

from gateway.tool_registry import ToolDefinition

MEMORY_TOOLS = {
    "save_memory": ToolDefinition(
        name="save_memory",
        description="Persist a new fact or insight to the knowledge base",
        factory_method="create_synapse",
        category="memory",
        parameters={"fact": "str", "source": "str"}
    ),
    # Session tools
    "get_session_info": ToolDefinition(
        name="get_session_info",
        description="Get detailed information about a session",
        factory_method=None,
        category="session",
        parameters={"session_id": "str"}
    ),
    "update_scratchpad": ToolDefinition(
        name="update_scratchpad",
        description="Store temporary facts or context in the session scratchpad",
        factory_method=None,
        category="session",
        parameters={"key": "str", "value": "any"}
    ),
}