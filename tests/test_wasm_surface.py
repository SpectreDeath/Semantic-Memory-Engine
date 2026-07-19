"""
Unit Tests for Pillar 2: Wasm Surface Execution Bridge
======================================================
Tests SurfaceBridge.execute_wasm_surface, schema validation, and sandbox fallback.
"""

from __future__ import annotations

import pytest

from gateway.surface_bridge import SurfaceBridge


class TestWasmSurfaceExecution:
    """Test Wasm Surface execution and validation."""

    def test_execute_wasm_surface_success(self):
        bridge = SurfaceBridge()
        res = bridge.execute_wasm_surface(
            code="100 + 200",
            inputs={"val": 10},
        )

        assert res["status"] == "success"
        assert res["runtime"] in ("wasm_sandbox", "wasm_fallback")
        assert res["result"] == 300

    def test_execute_wasm_surface_schema_failure(self):
        bridge = SurfaceBridge()
        schema = {
            "type": "object",
            "properties": {"val": {"type": "integer"}},
            "required": ["val"],
        }
        res = bridge.execute_wasm_surface(
            code="result = 42",
            inputs={"val": "not_an_int"},
            schema=schema,
        )

        assert res["status"] == "error"
        assert "Schema Validation Error" in res["error"]
