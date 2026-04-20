"""
Tests for gateway/metrics.py - Prometheus metrics management.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import os
from unittest.mock import patch, MagicMock

import pytest

from gateway.metrics import MetricsManager, get_metrics_manager


def test_metrics_manager_default_enabled():
    with patch.dict(os.environ, {}, clear=True):
        # Default enabled true
        mm = MetricsManager()
        assert mm.enabled is True


def test_metrics_manager_disabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "false"}):
        mm = MetricsManager()
        assert mm.enabled is False


@patch("gateway.metrics.start_http_server")
def test_start_starts_server(mock_start):
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "true"}):
        mm = MetricsManager(port=9000)
        mm.start()
        mock_start.assert_called_once_with(9000)


@patch("gateway.metrics.start_http_server")
def test_start_noop_when_disabled(mock_start):
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "false"}):
        mm = MetricsManager()
        mm.start()
        mock_start.assert_not_called()


def test_track_calls_enabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "true"}):
        mm = MetricsManager()
        # Mock the counter's labels().inc method
        mm.tool_calls_total = MagicMock()
        mm.tool_calls_total.labels.return_value.inc = MagicMock()
        mm.track_call("my_tool", "my_category")
        mm.tool_calls_total.labels.assert_called_with(tool_name="my_tool", category="my_category")
        mm.tool_calls_total.labels.return_value.inc.assert_called_once()


def test_track_calls_disabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "false"}):
        mm = MetricsManager()
        # Should not raise even though counters not created
        mm.track_call("tool", "cat")  # no-op


def test_track_error_enabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "true"}):
        mm = MetricsManager()
        mm.tool_errors_total = MagicMock()
        mm.tool_errors_total.labels.return_value.inc = MagicMock()
        mm.track_error("toolX", "ValueError")
        mm.tool_errors_total.labels.assert_called_with(tool_name="toolX", error_type="ValueError")


def test_observe_latency_enabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "true"}):
        mm = MetricsManager()
        mm.tool_latency_seconds = MagicMock()
        mm.tool_latency_seconds.labels.return_value.observe = MagicMock()
        mm.observe_latency("toolY", 0.5)
        mm.tool_latency_seconds.labels.assert_called_with(tool_name="toolY")
        mm.tool_latency_seconds.labels.return_value.observe.assert_called_with(0.5)


def test_set_active_sessions_enabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "true"}):
        mm = MetricsManager()
        mm.active_sessions = MagicMock()
        mm.set_active_sessions(5)
        mm.active_sessions.set.assert_called_with(5)


def test_set_health_enabled():
    with patch.dict(os.environ, {"SME_METRICS_ENABLED": "true"}):
        mm = MetricsManager()
        mm.system_health = MagicMock()
        mm.set_health("healthy")
        mm.system_health.set.assert_called_with(1)
        mm.set_health("degraded")
        mm.system_health.set.assert_called_with(0)
        mm.set_health("down")
        mm.system_health.set.assert_called_with(-1)


def test_get_metrics_manager_singleton():
    a = get_metrics_manager()
    b = get_metrics_manager()
    assert a is b
