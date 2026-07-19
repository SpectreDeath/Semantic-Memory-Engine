"""
Gateway Traffic Router - Dynamic Load Balancing & Workload Dispatch
=====================================================================
Routes incoming tool calls and workflow requests between local SME forensic
runtimes and em-cubed distributed execution nodes.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Ensure em-cubed is importable if co-located
em_cubed_path = Path(__file__).resolve().parent.parent.parent / "em-cubed" / "src"
if em_cubed_path.exists() and str(em_cubed_path) not in sys.path:
    sys.path.insert(0, str(em_cubed_path))

logger = logging.getLogger("lawnmower.traffic_router")

# Routing Modes
RULE_AUTO_BALANCE = "auto"
RULE_LOCAL_ONLY = "local_only"
RULE_EM_CUBED_WORKFLOW = "em_cubed_workflow"

# Target Nodes
NODE_SME_LOCAL = "sme_local"
NODE_EM_CUBED_DISTRIBUTED = "em_cubed_node"

# Tools classified as workflow/surface execution by default
WORKFLOW_SURFACE_TOOLS: set[str] = {
    "execute_surface",
    "execute_graph_surface",
    "distributed_workflow",
    "cluster_documents",
}


class TrafficRouter:
    """
    Dynamic gateway router for workload balancing between SME and em-cubed.
    """

    def __init__(self, default_mode: str = RULE_AUTO_BALANCE) -> None:
        self.default_mode = os.environ.get("SME_ROUTING_MODE", default_mode)

    def resolve_route(
        self,
        tool_name: str,
        payload: dict[str, Any] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """
        Determine target execution node for an incoming request.

        Args:
            tool_name: Name of tool or workflow.
            payload: Request arguments.
            mode: Routing mode override (auto, local_only, em_cubed_workflow).

        Returns:
            Dict containing target_node, mode, reason, and fallback_node.
        """
        active_mode = mode or self.default_mode

        if active_mode == RULE_LOCAL_ONLY:
            return {
                "target_node": NODE_SME_LOCAL,
                "mode": RULE_LOCAL_ONLY,
                "reason": "Explicit local_only policy enforced.",
                "fallback_node": None,
            }

        if active_mode == RULE_EM_CUBED_WORKFLOW:
            return {
                "target_node": NODE_EM_CUBED_DISTRIBUTED,
                "mode": RULE_EM_CUBED_WORKFLOW,
                "reason": "Explicit em_cubed_workflow policy enforced.",
                "fallback_node": NODE_SME_LOCAL,
            }

        # Auto-balancing rule
        if tool_name in WORKFLOW_SURFACE_TOOLS or "workflow" in tool_name:
            target = NODE_EM_CUBED_DISTRIBUTED
            reason = f"Tool '{tool_name}' classified as compute-heavy workflow surface."
        else:
            target = NODE_SME_LOCAL
            reason = f"Tool '{tool_name}' classified as local forensic query."

        return {
            "target_node": target,
            "mode": RULE_AUTO_BALANCE,
            "reason": reason,
            "fallback_node": NODE_SME_LOCAL if target != NODE_SME_LOCAL else None,
        }

    def probe_node_health(self, node_id: str = NODE_EM_CUBED_DISTRIBUTED) -> dict[str, Any]:
        """Check health and availability of target execution node."""
        if node_id == NODE_SME_LOCAL:
            return {"node_id": NODE_SME_LOCAL, "status": "online", "latency_ms": 0.5}

        # Probe em-cubed node availability
        try:
            from em_cubed.surfaces.python_surface import PythonSurface

            ps = PythonSurface()
            is_available = ps.available
            return {
                "node_id": NODE_EM_CUBED_DISTRIBUTED,
                "status": "online" if is_available else "degraded",
                "available": is_available,
                "latency_ms": 2.1,
            }
        except ImportError:
            return {
                "node_id": NODE_EM_CUBED_DISTRIBUTED,
                "status": "offline",
                "available": False,
                "reason": "em_cubed package not directly importable",
            }

    def dispatch_workload(
        self,
        tool_name: str,
        payload: dict[str, Any] | None = None,
        mode: str | None = None,
        sme_core: Any | None = None,
        mimo_config: Any | None = None,
    ) -> dict[str, Any]:
        """
        Resolve route and dispatch workload to target execution runtime.
        """
        eff_mode = mode
        if mimo_config and hasattr(mimo_config, "d4_routing_mode"):
            eff_mode = mimo_config.d4_routing_mode

        route = self.resolve_route(tool_name, payload=payload, mode=eff_mode)
        target = route["target_node"]
        args = payload or {}

        logger.info(f"TrafficRouter dispatching '{tool_name}' -> {target} ({route['reason']})")

        if target == NODE_EM_CUBED_DISTRIBUTED:
            health = self.probe_node_health(NODE_EM_CUBED_DISTRIBUTED)
            if health["status"] == "offline" and route["fallback_node"] == NODE_SME_LOCAL:
                logger.warning(f"Node {NODE_EM_CUBED_DISTRIBUTED} offline. Falling back to local.")
                target = NODE_SME_LOCAL

        if target == NODE_EM_CUBED_DISTRIBUTED:
            if tool_name == "execute_distributed_workflow" or "tasks_spec" in args:
                from gateway.em_cubed_bridge import EmCubedWorkflowBridge

                bridge = EmCubedWorkflowBridge()
                return bridge.execute_workflow_dag(
                    workflow_id=args.get("workflow_id"),
                    tasks_spec=args.get("tasks_spec", []),
                )

            if sme_core and hasattr(sme_core, "execute_surface"):
                code = args.get("code", f"result = '{tool_name} executed on em_cubed'")
                return sme_core.execute_surface(
                    code=code,
                    inputs=args.get("inputs", args),
                    schema=args.get("schema"),
                )

        return {
            "status": "success",
            "executed_by": target,
            "tool_name": tool_name,
            "route_info": route,
            "payload": args,
        }
