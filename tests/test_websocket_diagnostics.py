"""
Unit Tests for WebSocket Diagnostics Stream
===========================================
Tests the /ws/diagnostics WebSocket connection and telemetry payload structure.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestWebSocketDiagnostics:
    """Test /ws/diagnostics endpoint and payload structure."""

    def test_websocket_diagnostics_stream(self):
        client = TestClient(app)
        with client.websocket_connect("/ws/diagnostics") as websocket:
            data = websocket.receive_json()

            assert data["type"] == "diagnostics"
            payload = data["data"]

            assert "cpu" in payload
            assert "memory" in payload
            assert "latency_ms" in payload
            assert "timestamp" in payload

            # Verify enriched subsystem telemetry
            assert "routing" in payload
            assert "mode" in payload["routing"]
            assert "em_cubed_node" in payload["routing"]

            assert "nexus" in payload
            assert "attached_databases" in payload["nexus"]
