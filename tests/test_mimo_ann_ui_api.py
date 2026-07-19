"""
Unit Tests for Pillar 1: MIMO 6D & ANN UI Telemetry API Endpoints
=================================================================
Tests POST /api/v1/ann/backprop and enriched telemetry payloads.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestMimoAnnUiApi:
    """Test MIMO 6D Control Surface & ANN Backprop API Endpoints."""

    def test_ann_backprop_endpoint(self):
        client = TestClient(app)
        response = client.post(
            "/api/v1/ann/backprop",
            json={
                "layer_index": 1,
                "target_objective": "test_objective",
                "trajectory": [
                    {"task_id": "step_0", "status": "success"},
                    {"task_id": "step_1", "status": "error", "error": "Test error"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"
        assert data.get("layer_index") == 1
        assert "global_gradient" in data
        assert "local_gradient" in data
        assert "validation_result" in data
        assert data.get("saved_to_pool") is True
