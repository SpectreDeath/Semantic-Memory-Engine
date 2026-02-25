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
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional

# Ensure SME is importable when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from gateway.session_manager import get_session_manager
from gateway.tool_registry import get_registry
from gateway.routers import register_all_routers

# =============================================================================
# Logging — structured JSON format for log aggregators
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
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
_extension_manager: Optional[ExtensionManager] = None


def get_extension_manager(nexus_api: Any = None) -> ExtensionManager:
    global _extension_manager
    if _extension_manager is None:
        _extension_manager = ExtensionManager(nexus_api=nexus_api)
    return _extension_manager


# =============================================================================
# SmeCoreBridge — Dependency injection bridge for all tool classes
# =============================================================================

class SmeCoreBridge:
    """
    Bridges tool classes to the gateway's session and data layers.

    Implements NexusAPI: extensions use ``nexus_api.nexus`` and
    ``nexus_api.get_hsm()`` instead of importing gateway internals directly.
    """

    def __init__(self, session_id: Optional[str] = None) -> None:
        self.session_id = session_id
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

    def __getstate__(self):
        # Prevent pickling of the sqlite3 connection
        state = self.__dict__.copy()
        state["_nexus"] = None
        return state

    def get_session_entry(self, key: str) -> Any:
        """Retrieve data from the current session's scratchpad."""
        if not self.session_id:
            return None
        return session_manager.get_session(self.session_id).scratchpad.get(key)

    def get_session(self) -> Optional[Any]:
        """Get the full session object."""
        if not self.session_id:
            return None
        return session_manager.get_session(self.session_id)

    def get_ego_triples(self, entity_name: str) -> List[tuple]:
        """
        Simulated ego-graph discovery from the ConceptNet core.
        In a real scenario, this would query the SQLite/HDF5 backend.

        TODO: Replace hardcoded simulation_data with a live query against the
              Centrifuge SQLite or PostgreSQL Nexus knowledge graph.
              Tracked in: https://github.com/SpectreDeath/Semantic-Memory-Engine/issues
        """
        simulation_data = {
            "Administrative Account": [
                ("Administrative Account", "is_a", "System Identity"),
                ("Administrative Account", "part_of", "Access Control"),
                ("System Identity", "granted_to", "User_Alpha"),
                ("Access Control", "protects", "Perimeter"),
                ("User_Alpha", "modified", "Security Policy"),
            ],
            "Perimeter Breach": [
                ("Perimeter Breach", "is_a", "Security Event"),
                ("Perimeter Breach", "caused_by", "Unauthorized Entry"),
                ("Security Event", "triggers", "Audit Log"),
                ("Audit Log", "monitored_by", "Security Analyst"),
            ],
        }
        return simulation_data.get(entity_name, [
            (entity_name, "is_a", "Concept"),
            (entity_name, "related_to", "Knowledge Base"),
        ])

    def get_source_reliability(self, source_id: str) -> Dict[str, Any]:
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
            logger.error(f"Nexus visibility error: {e}")
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
            logger.error(f"Nexus registration error: {e}")
            return False


# =============================================================================
# Instantiate core bridge
# =============================================================================
sme_core = SmeCoreBridge()

# =============================================================================
# Extension Loading — deferred to the FastMCP startup lifecycle hook.
# This avoids asyncio.run() at import time which breaks uvicorn (raises
# RuntimeError when a loop is already running) and Jupyter environments.
# =============================================================================
extension_manager = get_extension_manager(nexus_api=sme_core)


@mcp.on_startup()
async def _load_extensions() -> None:
    """Discover and register all hot-swappable extension plugins on server start."""
    await extension_manager.discover_and_load()

    for tool_info in extension_manager.get_extension_tools():
        registry.add_tool(
            tool_info["name"],
            tool_info["handler"],
            description=tool_info["description"],
            parameters=tool_info.get("parameters", {}),
            handler=tool_info["handler"],
        )
        mcp.tool(
            name=tool_info["name"],
            description=tool_info["description"],
        )(tool_info["handler"])
        logger.info(
            f"ExtensionManager: Registered plugin tool '{tool_info['name']}' "
            f"(Plugin: {tool_info['plugin_id']})"
        )


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
    logger.info("Starting Lawnmower Man MCP Gateway v3.0.0 (Crucible Bridge)...")
    logger.info(f"Available tools: {len(registry.TOOL_DEFINITIONS)}")
    logger.info(f"Categories: {registry.get_categories()}")
    metrics_manager.start()
    mcp.run()
