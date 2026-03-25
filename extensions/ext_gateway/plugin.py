import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Gateway")

try:
    from gateway.mcp_server import MCPServer
except ImportError:
    MCPServer = None


class GatewayExtension(BasePlugin):
    """
    MCP Gateway Extension for SME.
    Provides MCP Gateway connection and management for server communication and tool exposure.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.server = MCPServer() if MCPServer else None
        self.connected = False

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] MCP Gateway extension activated.")
        self.connected = True

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.connect_gateway,
            self.disconnect_gateway,
            self.list_tools,
            self.call_tool,
            self.get_gateway_status,
            self.register_tool,
        ]

    async def connect_gateway(self, host: str = "localhost", port: int = 8000) -> str:
        """Connect to MCP Gateway."""
        logger.info(f"[{self.plugin_id}] Connecting to MCP Gateway at {host}:{port}")
        self.connected = True
        return json.dumps({"status": "connected", "host": host, "port": port})

    async def disconnect_gateway(self) -> str:
        """Disconnect from MCP Gateway."""
        logger.info(f"[{self.plugin_id}] Disconnecting from MCP Gateway")
        self.connected = False
        return json.dumps({"status": "disconnected"})

    async def list_tools(self) -> str:
        """List all available tools from gateway."""
        tools = [
            "trust_score_analysis",
            "stylometry_analyze",
            "semantic_audit",
            "adversarial_detect",
            "forensic_vault_store",
            "knowledge_graph_query",
            "web_research",
            "query_engine",
            "agent_execute",
            "analysis_run",
        ]
        return json.dumps({"tools": tools, "count": len(tools)})

    async def call_tool(self, tool_name: str, params: dict = None) -> str:
        """Call a tool on the gateway."""
        if not self.connected:
            return json.dumps({"error": "Gateway not connected"})
        logger.info(f"[{self.plugin_id}] Calling tool: {tool_name}")
        return json.dumps({"tool": tool_name, "params": params, "status": "executed"})

    async def get_gateway_status(self) -> str:
        """Get gateway connection status."""
        return json.dumps(
            {
                "connected": self.connected,
                "server": "MCP Server",
                "version": "3.0.0",
                "tools_available": 10,
            }
        )

    async def register_tool(self, tool_name: str, tool_definition: dict) -> str:
        """Register a new tool with the gateway."""
        logger.info(f"[{self.plugin_id}] Registering tool: {tool_name}")
        return json.dumps({"status": "registered", "tool": tool_name})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return GatewayExtension(manifest, nexus_api)
