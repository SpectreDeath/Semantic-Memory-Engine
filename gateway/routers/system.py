"""
gateway/routers/system.py
=========================
System health, hardware telemetry, and gateway utility tools.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None

from gateway.health_check import deep_health_check

logger = logging.getLogger("lawnmower.system")


# ---------------------------------------------------------------------------
# Internal helper — shared by verify_system AND check_health without .fn hack
# ---------------------------------------------------------------------------


def _get_system_status(registry: Any) -> dict:
    """Collect system health data and return as a plain dict."""
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "telemetry": {},
        "data_integrity": {},
        "semantic_memory": {},
    }

    if psutil:
        cpu_usage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        result["telemetry"] = {
            "cpu_percent": cpu_usage,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_used_percent": memory.percent,
        }

    db_path = os.environ.get("SME_DB_PATH", "data/knowledge_core.sqlite")
    result["data_integrity"]["knowledge_db"] = {
        "path": db_path,
        "exists": os.path.exists(db_path),
        "size_gb": round(os.path.getsize(db_path) / (1024**3), 3) if os.path.exists(db_path) else 0,
    }

    csv_path = "data/conceptnet-assertions-5.7.0.csv"
    result["data_integrity"]["conceptnet"] = {
        "path": csv_path,
        "exists": os.path.exists(csv_path),
        "size_gb": round(os.path.getsize(csv_path) / (1024**3), 2)
        if os.path.exists(csv_path)
        else 0,
    }

    try:
        tool = registry.get_tool("get_memory_stats")
        if tool and hasattr(tool, "get_stats"):
            result["semantic_memory"] = tool.get_stats()
        else:
            result["semantic_memory"] = {"status": "pending_initialization"}
    except Exception as e:
        result["semantic_memory"] = {"error": str(e)}

    if not result["data_integrity"]["knowledge_db"]["exists"]:
        result["status"] = "degraded"
        result["message"] = "Knowledge database not found. Run 'sme index' to initialize."

    return result


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------


def register(
    mcp: Any,
    registry: Any,
    session_manager: Any,
    metrics_manager: Any,
    auth_manager: Any,
    rate_limiter: Any,
    extension_manager: Any,
    get_hsm: Any,
    get_nexus: Any,
    sme_core: Any = None,
) -> None:
    """Register all system / utility tools with the FastMCP instance."""

    @mcp.tool()
    def get_system_guardrail() -> str:
        """
        Returns the Epistemic Gatekeeper System Prompt.
        Use this to ground the AI's personality and enforcement rules.
        """
        return """
    EPISTEMIC GATEKEEPER ACTIVE (v1.2.0).

    You are an Epistemically Humble Forensic Assistant.
    Your mission is to analyze data while strictly maintaining trust boundaries.

    RULES:
    1. If any data retrieved has a Normalized Trust Score (NTS) < 50, you MUST prefix your response with:
       "**[SYNTHETIC DATA WARNING]** Statistical indicators suggest this data is primarily synthetic/Grok-derived. Use for hypothesis generation only; do not treat as grounded evidence."
    2. Prioritize "Grounded Human Content" (NTS > 80) over synthetic signals.
    3. If trust is Indeterminate (50-80), append a 'CAUTION: MIXED SIGNALS' note.

    Maintain rigorous skepticism. Verify, then Trust.
    """

    @mcp.tool()
    def verify_system() -> str:
        """
        Verify system health and return hardware telemetry.

        Returns CPU/RAM usage, database status, and data integrity checks.
        This is the instrumentation heartbeat for Project Lawnmower Man.
        """
        logger.info("verify_system called")
        return json.dumps(_get_system_status(registry), indent=2)

    @mcp.tool()
    def check_health() -> str:
        """
        Combined health check for the gateway and all dependencies.

        Returns:
            JSON with overall status (healthy, degraded, down)
        """
        logger.info("check_health called")

        verify_result = _get_system_status(registry)
        session_count = len(session_manager._sessions)
        metrics_manager.set_active_sessions(session_count)

        status = verify_result.get("status", "unknown")
        metrics_manager.set_health(status)

        health = {
            "gateway": "Lawnmower Man",
            "version": "3.0.0",
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "active_sessions": session_count,
            "sme_health": verify_result,
            "hardware": get_hsm().get_telemetry(),
            "nexus": get_nexus().get_status(),
            "extensions": extension_manager.get_status(),
        }
        return json.dumps(health, indent=2)

    @mcp.tool()
    def deep_health() -> str:
        """
        Comprehensive deep health check for all system dependencies.

        Checks:
        - PostgreSQL connectivity
        - SQLite database accessibility
        - Sidecar service availability
        - Environment variables
        - Disk space
        - Extension loading

        Returns:
            JSON with detailed status of all subsystems
        """
        logger.info("deep_health called")
        result = deep_health_check()
        return json.dumps(result, indent=2)

    @mcp.tool()
    def get_system_latency() -> str:
        """Measure internal tool-call latency and system responsiveness."""
        start = time.perf_counter()
        registry.list_tools()
        latency_ms = (time.perf_counter() - start) * 1000
        return json.dumps(
            {
                "internal_latency_ms": round(latency_ms, 3),
                "timestamp": datetime.now().isoformat(),
            }
        )

    @mcp.tool()
    def get_hardware_status() -> str:
        """Retrieve the current status and alerts from the Hardware Security Module (TPM)."""
        return json.dumps(get_hsm().get_telemetry(), indent=2)

    @mcp.tool()
    def login(username: str, password: str) -> str:
        """Authenticate with the gateway and receive a JWT token."""
        token = auth_manager.login(username, password)
        if token:
            return json.dumps({"token": token, "expires_in": "24h"})
        return json.dumps({"error": "Invalid credentials"})

    @mcp.tool()
    def list_available_tools() -> str:
        """Introspect the ToolRegistry to provide a live manifest of all registered tools."""
        from gateway.routers.shared import serialize_result

        tools = registry.list_tools()
        manifest = {
            "version": "3.0.0",
            "codename": "Crucible Bridge",
            "total_tools": len(tools),
            "registry": tools,
        }
        return json.dumps(serialize_result(manifest), indent=2)

    @mcp.tool()
    def route_execution(
        tool_name: str, payload: dict | None = None, mode: str = "auto"
    ) -> str:
        """Dynamically route and dispatch tool execution between SME local runtime and em-cubed distributed nodes."""
        from gateway.traffic_router import TrafficRouter

        router = TrafficRouter()
        res = router.dispatch_workload(
            tool_name=tool_name, payload=payload, mode=mode, sme_core=sme_core
        )
        return json.dumps(res, indent=2)

    @mcp.tool()
    def execute_distributed_workflow(
        workflow_id: str | None = None, tasks_spec: list[dict] | None = None
    ) -> str:
        """Execute a multi-step em-cubed distributed workflow DAG across execution pools."""
        from gateway.em_cubed_bridge import EmCubedWorkflowBridge

        bridge = EmCubedWorkflowBridge()
        res = bridge.execute_workflow_dag(workflow_id=workflow_id, tasks_spec=tasks_spec)
        return json.dumps(res, indent=2)

    @mcp.tool()
    def route_scientific_workflow(
        prompt: str, target_domain: str = "bioinformatics"
    ) -> str:
        """Route and execute multi-modal scientific workflow DAG (ChEMBL, PubChem, PDB, PyMOL)."""
        from gateway.scientific_router import ScientificDomainRouter

        sci_router = ScientificDomainRouter()
        res = sci_router.execute_scientific_workflow(prompt=prompt, target_domain=target_domain)
        return json.dumps(res, indent=2)

    @mcp.tool()
    def analyze_media_forensics(
        file_path: str, checks: list[str] | None = None
    ) -> str:
        """Analyze media file for EXIF metadata, LSB steganography, and ELA artifacts."""
        from extensions.ext_forensic_media.plugin import ForensicMediaPlugin

        plugin = ForensicMediaPlugin()
        res = plugin.analyze_media_forensics(file_path=file_path, checks=checks)
        return json.dumps(res, indent=2)

    @mcp.tool()
    def harvest_threat_iocs(
        raw_text: str, source_id: str = "darkweb_feed"
    ) -> str:
        """Extract threat intelligence IOCs (IP, SHA256, BTC wallet) and inject into VIndexOverlay."""
        from gateway.threat_harvester import ThreatIntelligenceHarvester

        harvester = ThreatIntelligenceHarvester()
        res = harvester.harvest_threat_iocs(raw_text=raw_text, source_id=source_id)
        return json.dumps(res, indent=2)
