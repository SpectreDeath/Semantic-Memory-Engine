"""
Lawnmower Man MCP Server - Gateway Orchestrator
================================================
This is the **thin orchestrator** for the SME forensic toolkit. All tool
definitions live in gateway/routers/. This file is responsible only for:

  1. Infrastructure setup (FastMCP, logging, managers)
  2. The SmeCoreBridge dependency-injection object
  3. Extension loading via @mcp.on_startup() lifecycle hook
  4. Calling register_all_routers() to wire domain routers
  5. Server entry point

Usage:
    python -m gateway.mcp_server
    # Or via Docker:
    docker-compose up lawnmower-gateway
"""

from __future__ import annotations

import logging
import sys
from typing import Any

# Standard bootstrap
import src.bootstrap
from src.core.constants import (
    DEFAULT_LOG_LEVEL,
    LOG_DATE_FORMAT,
    LOG_FORMAT,
    SME_NAME,
    SME_VERSION,
)

src.bootstrap.initialize()

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from fastmcp import FastMCP
    except ImportError:
        print("ERROR: MCP / FastMCP v2.0+ not installed. Run: pip install mcp fastmcp")
        sys.exit(1)

from gateway.auth import get_auth_manager
from gateway.extension_manager import ExtensionManager
from gateway.hardware_security import get_hsm
from gateway.metrics import get_metrics_manager
from gateway.nexus_db import get_nexus
from gateway.rate_limiter import get_rate_limiter
from gateway.routers import register_all_routers
from gateway.session_manager import get_session_manager
from gateway.tool_registry import get_registry

# =============================================================================
# Logging — structured JSON format for log aggregators
# =============================================================================
logging.basicConfig(
    level=getattr(logging, DEFAULT_LOG_LEVEL),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)
logger = logging.getLogger("lawnmower.mcp")

# =============================================================================
# FastMCP instance
# =============================================================================
mcp = FastMCP(
    "Lawnmower Man Gateway",
    instructions="MCP gateway to the Semantic Memory Engine forensic toolkit",
)

# =============================================================================
# Shared singleton managers
# =============================================================================
registry = get_registry()
session_manager = get_session_manager()
auth_manager = get_auth_manager()
metrics_manager = get_metrics_manager()
rate_limiter = get_rate_limiter()

# =============================================================================
# Extension manager (lazy singleton)
# =============================================================================
_extension_manager: ExtensionManager | None = None


def get_extension_manager(nexus_api: Any = None) -> ExtensionManager:
    global _extension_manager
    if _extension_manager is None:
        _extension_manager = ExtensionManager(nexus_api=nexus_api)
    return _extension_manager


# =============================================================================
# Component Bridges & SmeCoreBridge — Imported from gateway.bridges
# =============================================================================
from gateway.bridges import (
    NexusDatabaseBridge,
    SemanticGraphBridge,
    SessionBridge,
    SmeCoreBridge,
    SurfaceBridge,
)


# =============================================================================
# Instantiate core bridge
# =============================================================================
sme_core = SmeCoreBridge()

# =============================================================================
# Extension Loading — deferred to the FastMCP startup lifecycle hook.
# This avoids asyncio.run() at import time which breaks uvicorn (raises
# RuntimeError when a loop is already running) and Jupyter environments.
# =============================================================================
# =============================================================================
# Extension Loading — moved to a manual call to avoid FastMCP hook issues
# =============================================================================
extension_manager = get_extension_manager(nexus_api=sme_core)


async def load_extensions() -> None:
    """Discover and register all hot-swappable extension plugins."""
    await extension_manager.discover_and_load()

    for tool_info in extension_manager.get_extension_tools():
        try:
            registry.add_tool(
                tool_info["name"],
                tool_info["handler"],
                description=tool_info["description"],
                parameters=tool_info.get("parameters", {}),
            )
            # Register with FastMCP
            mcp.tool(
                name=tool_info["name"],
                description=tool_info["description"],
            )(tool_info["handler"])
            logger.info(
                f"ExtensionManager: Registered plugin tool '{tool_info['name']}' "
                f"(Plugin: {tool_info['plugin_id']})"
            )
        except Exception as e:
            logger.exception(
                f"ExtensionManager: Failed to register tool '{tool_info['name']}': {e}"
            )
            continue  # Graceful degradation - continue with other tools


# =============================================================================
# Register all domain routers
# =============================================================================
register_all_routers(
    mcp=mcp,
    sme_core=sme_core,
    registry=registry,
    session_manager=session_manager,
    metrics_manager=metrics_manager,
    auth_manager=auth_manager,
    rate_limiter=rate_limiter,
    extension_manager=extension_manager,
    get_hsm=get_hsm,
    get_nexus=get_nexus,
)

# Exposed tool wrappers for direct module invocation
serverDiscover = registry.get_tool("serverDiscover")  # noqa: N816
verify_system = registry.get_tool("verify_system")
list_available_tools = registry.get_tool("list_available_tools")
get_memory_stats = registry.get_tool("get_memory_stats")

# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info(f"Starting {SME_NAME} v{SME_VERSION}...")
    logger.info(f"Available tools: {len(registry.TOOL_DEFINITIONS)}")
    logger.info(f"Categories: {registry.get_categories()}")
    metrics_manager.start()
    mcp.run()
