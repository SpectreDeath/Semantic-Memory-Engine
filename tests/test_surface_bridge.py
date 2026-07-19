"""
Unit Tests for SurfaceBridge Integration
=========================================
Tests JSON schema validation, surface execution, and MCP bridge delegation.
"""

from __future__ import annotations

import pytest

from gateway.mcp_server import SemanticGraphBridge, SmeCoreBridge
from gateway.surface_bridge import SurfaceBridge


class TestSurfaceBridgeSchemaValidation:
    """Test JSON Schema validation in SurfaceBridge."""

    SCHEMA = {
        "type": "object",
        "required": ["threshold", "target"],
        "properties": {
            "threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "target": {"type": "string", "minLength": 1},
        },
    }

    def test_valid_inputs_pass_validation(self):
        bridge = SurfaceBridge()
        code = "{'status': 'ok', 'score': threshold}"
        inputs = {"threshold": 0.85, "target": "Alpha"}

        res = bridge.execute_surface(code=code, inputs=inputs, schema=self.SCHEMA)

        assert res["status"] == "success"
        assert res["validated"] is True
        assert res["result"] == {"status": "ok", "score": 0.85}

    def test_invalid_inputs_fail_validation(self):
        bridge = SurfaceBridge()
        code = "{'status': 'should_not_run'}"
        # threshold violates max limit (1.5 > 1.0)
        inputs = {"threshold": 1.5, "target": "Alpha"}

        res = bridge.execute_surface(code=code, inputs=inputs, schema=self.SCHEMA)

        assert res["status"] == "validation_error"
        assert "Schema Validation Error" in res["error"]


class TestBridgeIntegration:
    """Test SmeCoreBridge & SemanticGraphBridge integration."""

    def test_sme_core_bridge_has_surface_execution(self):
        core = SmeCoreBridge()
        code = "x * 2"
        res = core.execute_surface(code=code, inputs={"x": 21})

        assert res["status"] == "success"
        assert res["result"] == 42

    def test_semantic_graph_bridge_execute_graph_surface(self):
        graph_bridge = SemanticGraphBridge()
        code = "{'entity': entity, 'count': len(triples)}"

        res = graph_bridge.execute_graph_surface(
            entity_name="Intelligence",
            transformation_code=code,
        )

        assert res["status"] == "success"
        assert res["result"]["entity"] == "Intelligence"
        assert isinstance(res["result"]["count"], int)
