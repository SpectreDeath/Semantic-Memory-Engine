"""
Unit Tests for Native Startup & Operator API Initialization
============================================================
Tests FastAPI operator server startup, router registration, and endpoint readiness.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestNativeOperatorStartup:
    """Test Operator API server initialization and route availability."""

    def test_app_title_and_routes(self):
        assert app.title == "SimpleMem Laboratory Control Room API"
        routes = [route.path for route in app.routes]

        assert "/api/v1/route" in routes
        assert "/ws/diagnostics" in routes

    def test_health_check_endpoint(self):
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "online"

    def test_route_endpoint_dispatch(self):
        client = TestClient(app)
        response = client.post(
            "/api/v1/route",
            json={
                "tool_name": "verify_system",
                "payload": {"check_disk": True},
                "mode": "local_only",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("executed_by") == "sme_local"
