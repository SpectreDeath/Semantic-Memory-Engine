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
    from fastmcp import FastMCP
except ImportError:
    print("ERROR: FastMCP not installed. Run: pip install fastmcp")
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
# SmeCoreBridge — Dependency injection bridge for all tool classes
# =============================================================================


# =============================================================================
# Component Bridges — Modular interfaces for data, graph, and session layers
# =============================================================================


class SessionBridge:
    """Handles session scratchpad access."""

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id = session_id

    def get_session_entry(self, key: str) -> Any:
        """Retrieve data from the current session's scratchpad."""
        if not self.session_id:
            return None
        return session_manager.get_session(self.session_id).scratchpad.get(key)

    def get_session(self) -> Any | None:
        """Get the full session object."""
        if not self.session_id:
            return None
        return session_manager.get_session(self.session_id)


class SemanticGraphBridge:
    """Handles semantic graph queries and WordNet relationship extraction."""

    @staticmethod
    def get_ego_triples(entity_name: str) -> list[tuple]:
        """
        Live ego-graph discovery from the SemanticGraph (WordNet).
        Queries real semantic relationships to build the entity's network.
        """
        from src.core.factory import ToolFactory

        try:
            sg = ToolFactory.create_semantic_graph()
            meaning = sg.explore_meaning(entity_name)

            if not meaning:
                return [(entity_name, "is_a", "Concept"), (entity_name, "status", "unresolved")]

            triples = []
            if meaning.definitions:
                triples.append((entity_name, "definition", meaning.definitions[0]))

            for syn in meaning.synonyms[:3]:
                triples.append((entity_name, "synonym", syn))

            for hyper in meaning.hypernyms[:2]:
                triples.append((entity_name, "is_a", hyper))

            for hypo in meaning.hyponyms[:2]:
                triples.append((hypo, "is_a", entity_name))

            return triples

        except Exception as e:
            logger.exception(f"Ego-graph discovery error: {e}")
            return [(entity_name, "error", str(e))]

    def execute_graph_surface(
        self,
        entity_name: str,
        transformation_code: str,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Extract entity ego-triples and execute a graph transformation surface against them.
        """
        from gateway.surface_bridge import SurfaceBridge

        triples = self.get_ego_triples(entity_name)
        surface_bridge = SurfaceBridge()
        inputs = {"entity": entity_name, "triples": triples}
        return surface_bridge.execute_surface(
            code=transformation_code,
            inputs=inputs,
            schema=schema,
        )


class NexusDatabaseBridge:
    """Handles SQLite Nexus database queries, provenance registration, and HSM access."""

    def __init__(self) -> None:
        self._nexus = None

    def get_hsm(self):
        """Return the HardwareSecurity module for evidence signing (NexusAPI)."""
        from gateway.hardware_security import get_hsm as _get_hsm

        return _get_hsm()

    @property
    def nexus(self):
        if self._nexus is None:
            from gateway.nexus_db import get_nexus as _get_nexus

            self._nexus = _get_nexus()
        return self._nexus

    def get_source_reliability(self, source_id: str) -> dict[str, Any]:
        """Query the Nexus core for source provenance reliability."""
        try:
            sql = (
                "SELECT reliability_tier, integrity_hash, is_tamper_evident "
                "FROM prov.source_provenance WHERE source_id = ?"
            )
            res = self.nexus.query(sql, (source_id,))
            if res:
                row = res[0]
                return {
                    "tier": row["reliability_tier"],
                    "hash": row["integrity_hash"],
                    "tamper_evident": bool(row["is_tamper_evident"]),
                }
            return {"tier": 1, "hash": "Unknown", "tamper_evident": False}
        except Exception as e:
            logger.exception(f"Nexus visibility error: {e}")
            return {"tier": 0, "hash": "Error", "tamper_evident": False}

    def register_provenance(
        self, source_id: str, path: str, hash_val: str, tier: int, method: str
    ) -> bool:
        """Manually register a source via the Nexus."""
        try:
            sql = """
                INSERT OR REPLACE INTO prov.source_provenance
                    (source_id, origin_path, integrity_hash, reliability_tier, acquisition_method)
                VALUES (?, ?, ?, ?, ?)
            """
            self.nexus.execute(sql, (source_id, path, hash_val, tier, method))
            return True
        except Exception as e:
            logger.exception(f"Nexus registration error: {e}")
            return False


# =============================================================================
# SmeCoreBridge — Unified composition bridge for tool and extension execution
# =============================================================================


from gateway.surface_bridge import SurfaceBridge


class SmeCoreBridge(SessionBridge, NexusDatabaseBridge, SemanticGraphBridge, SurfaceBridge):
    """
    Composes SessionBridge, NexusDatabaseBridge, SemanticGraphBridge, and SurfaceBridge.

    Implements NexusAPI for extensions while decoupling individual functional areas.
    """

    def __init__(self, session_id: str | None = None) -> None:
        SessionBridge.__init__(self, session_id=session_id)
        NexusDatabaseBridge.__init__(self)
        SurfaceBridge.__init__(self)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_nexus"] = None
        return state


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

# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info(f"Starting {SME_NAME} v{SME_VERSION}...")
    logger.info(f"Available tools: {len(registry.TOOL_DEFINITIONS)}")
    logger.info(f"Categories: {registry.get_categories()}")
    metrics_manager.start()
    mcp.run()
