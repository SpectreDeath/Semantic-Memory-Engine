"""
Tests for Ghost Trap Extension Plugin.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from extensions.ext_ghost_trap.ghost_detector import GhostDetector, GhostFile, scan_for_ghosts
from extensions.ext_ghost_trap.ghost_trap_client import GhostTrapClient, get_ghost_trap
from extensions.ext_ghost_trap.persistence_monitor import (
    GhostTrapMonitor,
    get_monitoring_status,
    ghost_monitor,
)
from extensions.ext_ghost_trap.plugin import GhostTrapPlugin, get_plugin, register_extension


class TestGhostTrapPlugin:
    """Tests for GhostTrapPlugin class."""

    def test_plugin_initialization(self):
        """Test plugin initializes with correct defaults."""
        plugin = GhostTrapPlugin({}, None)
        assert plugin.name == "Ghost Trap Extension"
        assert plugin.version == "1.0.0"
        assert plugin.is_active is False
        assert plugin.config["size_threshold_mb"] == 100
        assert plugin.config["monitoring_enabled"] is True

    def test_activate_success(self):
        """Test successful plugin activation."""
        plugin = GhostTrapPlugin({}, None)
        result = plugin.activate()
        assert result is True
        assert plugin.is_active is True

    def test_deactivate_success(self):
        """Test successful plugin deactivation."""
        plugin = GhostTrapPlugin({}, None)
        plugin.activate()
        result = plugin.deactivate()
        assert result is True
        assert plugin.is_active is False

    def test_get_status(self):
        """Test status retrieval."""
        plugin = GhostTrapPlugin({}, None)
        status = plugin.get_status()
        assert status["name"] == "Ghost Trap Extension"
        assert status["is_active"] is False
        assert "monitoring_status" in status
        assert "config" in status

    def test_configure_updates_config(self):
        """Test configuration updates."""
        plugin = GhostTrapPlugin({}, None)
        result = plugin.configure(size_threshold_mb=200, monitoring_enabled=False)
        assert result is True
        assert plugin.config["size_threshold_mb"] == 200
        assert plugin.config["monitoring_enabled"] is False

    def test_configure_invalid_key(self):
        """Test configuration ignores invalid keys."""
        plugin = GhostTrapPlugin({}, None)
        result = plugin.configure(invalid_key="value")
        assert result is True
        assert "invalid_key" not in plugin.config

    def test_get_tools_returns_scan_tool(self):
        """Test tools endpoint returns callable."""
        plugin = GhostTrapPlugin({}, None)
        tools = plugin.get_tools()
        assert len(tools) == 1
        assert callable(tools[0])

    def test_get_hooks(self):
        """Test hooks endpoint returns governor hook."""
        plugin = GhostTrapPlugin({}, None)
        hooks = plugin.get_hooks()
        assert "governor_task_execution" in hooks

    def test_get_events(self):
        """Test events endpoint returns expected events."""
        plugin = GhostTrapPlugin({}, None)
        events = plugin.get_events()
        assert "task_execution_started" in events
        assert "task_execution_completed" in events
        assert "file_created" in events
        assert "ghost_detected" in events

    def test_handle_event_task_started(self):
        """Test task_execution_started event starts monitoring."""
        plugin = GhostTrapPlugin({}, None)
        result = plugin.handle_event("task_execution_started")
        assert result["monitoring_started"] is True

    def test_handle_event_task_completed(self):
        """Test task_execution_completed event stops monitoring."""
        plugin = GhostTrapPlugin({}, None)
        plugin.activate()
        result = plugin.handle_event("task_execution_completed")
        assert result["monitoring_stopped"] is True

    def test_handle_event_unknown(self):
        """Test unknown events return handled false."""
        plugin = GhostTrapPlugin({}, None)
        result = plugin.handle_event("unknown_event")
        assert result["event_handled"] is False


class TestGhostDetector:
    """Tests for GhostDetector class."""

    def test_detector_initialization(self):
        """Test detector initializes correctly."""
        detector = GhostDetector(size_threshold_mb=50)
        assert detector.size_threshold_bytes == 50 * 1024 * 1024
        assert ".bin" in detector.target_extensions

    def test_get_file_size_mb(self, tmp_path):
        """Test file size calculation."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB
        detector = GhostDetector()
        size = detector._get_file_size_mb(test_file)
        assert abs(size - 5.0) < 0.01

    def test_is_hidden_file_dot_prefix(self, tmp_path):
        """Test hidden file detection with dot prefix."""
        hidden_file = tmp_path / ".hidden" / "test.bin"
        hidden_file.parent.mkdir(exist_ok=True)
        hidden_file.write_bytes(b"x")
        detector = GhostDetector()
        assert detector._is_hidden_file(hidden_file) is True

    def test_should_scan_file_includes_large_bin(self, tmp_path):
        """Test file scanning includes large .bin files."""
        large_file = tmp_path / "model.bin"
        large_file.write_bytes(b"x" * (150 * 1024 * 1024))  # 150 MB
        detector = GhostDetector(size_threshold_mb=100)
        assert detector._should_scan_file(large_file) is True

    def test_should_scan_file_excludes_small(self, tmp_path):
        """Test file scanning excludes small files."""
        small_file = tmp_path / "small.json"
        small_file.write_bytes(b"x" * 100)
        detector = GhostDetector(size_threshold_mb=100)
        assert detector._should_scan_file(small_file) is False

    def test_should_scan_file_excludes_wrong_ext(self, tmp_path):
        """Test file scanning excludes wrong extensions."""
        txt_file = tmp_path / "file.txt"
        txt_file.write_bytes(b"x" * (150 * 1024 * 1024))
        detector = GhostDetector(size_threshold_mb=100)
        assert detector._should_scan_file(txt_file) is False

    def test_analyze_file_name_patterns(self, tmp_path):
        """Test suspicious pattern detection in file names."""
        model_file = tmp_path / "model_weights.bin"
        detector = GhostDetector()
        indicators = detector._analyze_file_name(model_file)
        assert any("model" in ind for ind in indicators)

    def test_scan_directory_returns_list(self, tmp_path):
        """Test directory scanning returns list of GhostFiles."""
        large_file = tmp_path / "ghost.bin"
        large_file.write_bytes(b"x" * (150 * 1024 * 1024))
        detector = GhostDetector(project_root=str(tmp_path), size_threshold_mb=100)
        with patch("builtins.print"):
            ghost_files = detector.scan_directory(recursive=False)
        assert isinstance(ghost_files, list)
        assert any(f.path == str(large_file) for f in ghost_files)

    def test_generate_report_clean(self):
        """Test report generation for clean scan."""
        detector = GhostDetector()
        report = detector.generate_report([])
        assert report["status"] == "clean"

    def test_generate_report_suspicious(self, tmp_path):
        """Test report generation for suspicious files."""
        ghost = GhostFile(
            path=str(tmp_path / "test.bin"),
            size_mb=150.0,
            file_type=".bin",
            is_hidden=False,
            last_modified=datetime.now(),
            suspicious_indicators=["model: model"],
        )
        detector = GhostDetector()
        report = detector.generate_report([ghost])
        assert report["status"] == "suspicious_activity_detected"
        assert report["scan_summary"]["total_suspicious_files"] == 1


class TestGhostTrapMonitor:
    """Tests for GhostTrapMonitor class."""

    def test_monitor_initialization(self):
        """Test monitor initializes correctly."""
        monitor = GhostTrapMonitor()
        assert monitor._is_monitoring is False
        assert len(monitor._hidden_directories) > 0

    def test_get_monitoring_status(self):
        """Test monitoring status retrieval."""
        status = get_monitoring_status()
        assert "is_monitoring" in status
        assert "hidden_directories" in status
        assert "wrapped_functions" in status

    def test_is_hidden_directory_dot_prefix(self):
        """Test hidden directory detection with dot prefix."""
        monitor = GhostTrapMonitor()
        assert monitor._is_hidden_directory("/home/user/.cache/file") is True

    def test_is_hidden_directory_empty(self):
        """Test hidden directory detection with empty path."""
        monitor = GhostTrapMonitor()
        assert monitor._is_hidden_directory("") is False
        assert monitor._is_hidden_directory(None) is False


class TestScanForGhosts:
    """Tests for scan_for_ghosts function."""

    def test_scan_for_ghosts_returns_json(self, tmp_path):
        """Test scan returns valid JSON string."""
        large_file = tmp_path / "model.bin"
        large_file.write_bytes(b"x" * (150 * 1024 * 1024))
        with patch("builtins.print"):
            result = scan_for_ghosts(
                project_root=str(tmp_path),
                size_threshold_mb=100,
                recursive=False,
                detailed_report=False,
            )
        data = json.loads(result)
        assert "status" in data

    def test_scan_for_ghosts_clean_directory(self, tmp_path):
        """Test scan on clean directory."""
        result = scan_for_ghosts(
            project_root=str(tmp_path),
            size_threshold_mb=100,
            recursive=False,
            detailed_report=False,
        )
        data = json.loads(result)
        assert data["status"] == "clean"


class TestGhostTrapClient:
    """Tests for GhostTrapClient class."""

    def test_client_initialization(self):
        """Test client initializes correctly."""
        client = GhostTrapClient()
        assert client.data_dir is not None
        assert "events.jsonl" in client.events_file
        assert "alerts.jsonl" in client.alerts_file

    def test_read_jsonl_missing_file(self):
        """Test reading from non-existent file returns empty list."""
        client = GhostTrapClient()
        events = client._read_jsonl("nonexistent_path.jsonl")
        assert events == []

    def test_read_jsonl_with_events(self, tmp_path):
        """Test reading events from JSONL file."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"event": "test1"}\n{"event": "test2"}\n')
        client = GhostTrapClient(str(tmp_path))
        events = client._read_jsonl(str(events_file))
        assert len(events) == 2
        assert events[0]["event"] == "test1"

    def test_read_jsonl_with_invalid_json(self, tmp_path):
        """Test reading JSONL skips invalid lines."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"event": "valid"}\ninvalid\n{"event": "valid2"}\n')
        client = GhostTrapClient(str(tmp_path))
        events = client._read_jsonl(str(events_file))
        assert len(events) == 2

    def test_get_recent_events_empty(self, tmp_path):
        """Test get_recent_events with empty file."""
        client = GhostTrapClient(str(tmp_path))
        events = client.get_recent_events(hours=24, limit=100)
        assert events == []

    def test_get_alerts_empty(self, tmp_path):
        """Test get_alerts with empty file."""
        client = GhostTrapClient(str(tmp_path))
        alerts = client.get_alerts(hours=24, severity=None)
        assert alerts == []

    def test_get_alerts_with_severity_filter(self, tmp_path):
        """Test get_alerts filters by severity."""
        alerts_file = tmp_path / "alerts.jsonl"
        alerts_file.write_text(
            '{"severity": "high", "event": "e1"}\n{"severity": "low", "event": "e2"}\n'
        )
        client = GhostTrapClient(str(tmp_path))
        alerts = client.get_alerts(hours=24, severity="high")
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "high"

    def test_get_persistence_events(self, tmp_path):
        """Test get_persistence_events filters correctly."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text(
            '{"event_type": "persistence_created"}\n{"event_type": "other_event"}\n'
        )
        client = GhostTrapClient(str(tmp_path))
        events = client.get_persistence_events(hours=24)
        assert len(events) == 1
        assert "persistence" in events[0]["event_type"].lower()

    def test_check_path_flagged(self, tmp_path):
        """Test check_path returns flagged for matching path."""
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"path": "/home/user/.cache/suspicious"}\n')
        client = GhostTrapClient(str(tmp_path))
        result = client.check_path("/home/user/.cache/suspicious")
        assert result["flagged"] is True

    def test_check_path_not_flagged(self, tmp_path):
        """Test check_path returns not flagged for non-matching path."""
        client = GhostTrapClient(str(tmp_path))
        result = client.check_path("/some/other/path")
        assert result["flagged"] is False

    def test_get_status(self, tmp_path):
        """Test get_status returns correct structure."""
        client = GhostTrapClient(str(tmp_path))
        status = client.get_status()
        assert status["ghost_trap"] == "active"
        assert status["recent_events_count"] == 0
        assert status["recent_alerts_count"] == 0


class TestPluginFactory:
    """Tests for plugin factory functions."""

    def test_get_plugin_returns_instance(self):
        """Test get_plugin returns GhostTrapPlugin instance."""
        plugin = get_plugin()
        assert isinstance(plugin, GhostTrapPlugin)

    def test_register_extension_returns_instance(self):
        """Test register_extension returns plugin instance."""
        plugin = register_extension({}, None)
        assert isinstance(plugin, GhostTrapPlugin)

    def test_get_ghost_trap_singleton(self):
        """Test get_ghost_trap returns singleton."""
        client1 = get_ghost_trap()
        client2 = get_ghost_trap()
        assert client1 is client2
