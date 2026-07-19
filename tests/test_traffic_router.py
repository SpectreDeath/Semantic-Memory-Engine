"""
Unit Tests for Gateway Traffic Router
======================================
Tests route resolution, node health probing, fallback policies, and workload dispatching.
"""

from __future__ import annotations

import pytest

from gateway.mcp_server import SmeCoreBridge
from gateway.traffic_router import (
    NODE_EM_CUBED_DISTRIBUTED,
    NODE_SME_LOCAL,
    RULE_AUTO_BALANCE,
    RULE_EM_CUBED_WORKFLOW,
    RULE_LOCAL_ONLY,
    TrafficRouter,
)


class TestTrafficRouterResolution:
    """Test route resolution rules."""

    def test_auto_balance_forensic_tool_routes_local(self):
        router = TrafficRouter()
        route = router.resolve_route(tool_name="analyze_authorship")

        assert route["target_node"] == NODE_SME_LOCAL
        assert route["mode"] == RULE_AUTO_BALANCE
        assert route["fallback_node"] is None

    def test_auto_balance_surface_tool_routes_em_cubed(self):
        router = TrafficRouter()
        route = router.resolve_route(tool_name="execute_surface")

        assert route["target_node"] == NODE_EM_CUBED_DISTRIBUTED
        assert route["mode"] == RULE_AUTO_BALANCE
        assert route["fallback_node"] == NODE_SME_LOCAL

    def test_explicit_local_only_mode(self):
        router = TrafficRouter()
        route = router.resolve_route(tool_name="execute_surface", mode=RULE_LOCAL_ONLY)

        assert route["target_node"] == NODE_SME_LOCAL
        assert route["mode"] == RULE_LOCAL_ONLY

    def test_explicit_em_cubed_mode(self):
        router = TrafficRouter()
        route = router.resolve_route(tool_name="semantic_search", mode=RULE_EM_CUBED_WORKFLOW)

        assert route["target_node"] == NODE_EM_CUBED_DISTRIBUTED
        assert route["mode"] == RULE_EM_CUBED_WORKFLOW
        assert route["fallback_node"] == NODE_SME_LOCAL


class TestNodeHealthProbing:
    """Test node health probing."""

    def test_probe_local_node_returns_online(self):
        router = TrafficRouter()
        health = router.probe_node_health(NODE_SME_LOCAL)

        assert health["node_id"] == NODE_SME_LOCAL
        assert health["status"] == "online"

    def test_probe_em_cubed_node(self):
        router = TrafficRouter()
        health = router.probe_node_health(NODE_EM_CUBED_DISTRIBUTED)

        assert health["node_id"] == NODE_EM_CUBED_DISTRIBUTED
        assert "status" in health


class TestWorkloadDispatch:
    """Test workload dispatching via TrafficRouter."""

    def test_dispatch_local_tool(self):
        router = TrafficRouter()
        sme_core = SmeCoreBridge()

        res = router.dispatch_workload(
            tool_name="verify_system",
            payload={"check_disk": True},
            mode=RULE_LOCAL_ONLY,
            sme_core=sme_core,
        )

        assert res["status"] == "success"
        assert res["executed_by"] == NODE_SME_LOCAL
        assert res["tool_name"] == "verify_system"

    def test_dispatch_surface_tool(self):
        router = TrafficRouter()
        sme_core = SmeCoreBridge()

        res = router.dispatch_workload(
            tool_name="execute_surface",
            payload={"code": "2 + 2"},
            mode=RULE_AUTO_BALANCE,
            sme_core=sme_core,
        )

        assert res["status"] == "success"
