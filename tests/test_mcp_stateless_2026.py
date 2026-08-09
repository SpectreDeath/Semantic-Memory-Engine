"""
tests/test_mcp_stateless_2026.py
===================================
Unit test suite verifying compliance with Model Context Protocol (MCP) 2026-07-28
Specification (Stateless MCP Architecture).
"""

import json

from gateway.rate_limiter import RateLimiter
from gateway.routers.shared import (
    extract_mcp_headers,
    format_input_required_response,
)
from gateway.session_manager import get_session_manager
from gateway.traffic_router import TrafficRouter


class TestMCP2026StatelessSpec:
    """Test suite for MCP 2026-07-28 protocol compliance."""

    def test_handshake_and_session_id_decoupling(self):
        """Verify requests execute statelessly without initialize handshake or Mcp-Session-Id."""
        sm = get_session_manager()
        # Passing None (no session handshake) returns stateless session
        session = sm.get_session(None)
        assert session is not None
        assert session.session_id.startswith("stateless_")

        ephemeral = sm.get_stateless_session()
        assert ephemeral.session_id.startswith("stateless_")

    def test_header_extraction(self):
        """Verify case-insensitive extraction of MCP-Method and MCP-Name HTTP headers."""
        headers = {
            "MCP-Method": "tools/call",
            "MCP-Name": "semantic_search",
            "Content-Type": "application/json",
        }
        mcp_method, mcp_name = extract_mcp_headers(headers)
        assert mcp_method == "tools/call"
        assert mcp_name == "semantic_search"

        # Case insensitivity check
        lowercase_headers = {
            "mcp-method": "serverDiscover",
            "mcp-name": "system",
        }
        mcp_method, mcp_name = extract_mcp_headers(lowercase_headers)
        assert mcp_method == "serverDiscover"
        assert mcp_name == "system"

    def test_traffic_router_header_routing(self):
        """Verify TrafficRouter utilizes MCP-Method and MCP-Name headers for route resolution."""
        router = TrafficRouter()
        route = router.resolve_route(
            tool_name="unknown_tool",
            mcp_method="tools/call",
            mcp_name="distributed_workflow",
        )
        # Should detect 'distributed_workflow' from header and route to em_cubed_node
        assert route["target_node"] == "em_cubed_node"
        assert route["mcp_method"] == "tools/call"
        assert route["mcp_name"] == "distributed_workflow"

    def test_rate_limiter_header_isolation(self):
        """Verify RateLimiter uses MCP-Method and MCP-Name for fine-grained per-tool key isolation."""
        limiter = RateLimiter(requests_per_minute=2)
        client_ip = "192.168.1.50"

        # Call with tool A header
        allowed_a1, _rem_a1 = limiter.is_allowed(client_ip, mcp_method="tools/call", mcp_name="tool_a")
        allowed_a2, _rem_a2 = limiter.is_allowed(client_ip, mcp_method="tools/call", mcp_name="tool_a")
        allowed_a3, _rem_a3 = limiter.is_allowed(client_ip, mcp_method="tools/call", mcp_name="tool_a")

        assert allowed_a1 is True
        assert allowed_a2 is True
        assert allowed_a3 is False  # Limit 2 exceeded for tool_a

        # Call with tool B header should still be allowed (separate key bucket)
        allowed_b1, _rem_b1 = limiter.is_allowed(client_ip, mcp_method="tools/call", mcp_name="tool_b")
        assert allowed_b1 is True

    def test_server_discover_capability(self):
        """Verify serverDiscover tool returns valid 2026-07-28 stateless capabilities metadata."""
        from gateway import mcp_server

        discover_fn = mcp_server.serverDiscover
        if hasattr(discover_fn, "fn"):
            callable_fn = discover_fn.fn
        elif callable(discover_fn):
            callable_fn = discover_fn
        else:
            from gateway.tool_registry import get_registry
            tool = get_registry().get_tool("serverDiscover")
            callable_fn = getattr(tool, "run", getattr(tool, "execute", tool))

        res_json = callable_fn()
        res = json.loads(res_json)

        assert res["spec_version"] == "2026-07-28"
        assert res["stateless"] is True
        assert res["capabilities"]["stateless_transport"] is True
        assert "MCP-Method" in res["capabilities"]["routing_headers"]
        assert "MCP-Name" in res["capabilities"]["routing_headers"]
        assert res["_meta"]["handshake_required"] is False
        assert res["_meta"]["mcp_session_id_deprecated"] is True

    def test_input_required_response_format(self):
        """Verify format_input_required_response produces valid multi-round-trip interactive payloads."""
        resp = format_input_required_response(
            prompt="Confirm forensic red team attack simulation parameters?",
            input_schema={"type": "object", "properties": {"iterations": {"type": "integer"}}},
            continuation_token="task_token_99182",
        )

        assert resp["status"] == "input_required"
        assert "Confirm forensic" in resp["prompt"]
        assert resp["continuation_token"] == "task_token_99182"
        assert resp["_meta"]["mcp_spec"] == "2026-07-28"
        assert resp["_meta"]["interactive"] is True

    def test_database_backed_task_tokens(self):
        """Verify get_task_state returns token state without needing persistent socket handshake."""
        sm = get_session_manager()
        state = sm.get_task_state("token_non_existent")
        assert state["task_token"] == "token_non_existent"
        assert state["status"] == "not_found"
