"""
Tests for ext_stetho_scan extension
=======================================
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestWatermarkDetection:
    """Tests for WatermarkDetection dataclass."""

    def test_detection_creation(self):
        """WatermarkDetection should initialize with all fields."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import WatermarkDetection

        detection = WatermarkDetection(
            has_invisible_markers=True,
            z_score_analysis={"the": 1.5},
            provider_signature="OPENAI",
            confidence_score=0.75,
            detected_markers=["\u200b"],
            timestamp="2026-01-01T00:00:00",
        )

        assert detection.has_invisible_markers is True
        assert detection.z_score_analysis == {"the": 1.5}
        assert detection.provider_signature == "OPENAI"
        assert detection.confidence_score == 0.75


class TestStatisticalWatermarkDecoder:
    """Tests for StatisticalWatermarkDecoder class."""

    def test_decoder_creation(self):
        """Decoder should initialize with invisible markers and provider signatures."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import (
            StatisticalWatermarkDecoder,
        )

        decoder = StatisticalWatermarkDecoder()

        assert decoder.invisible_markers is not None
        assert len(decoder.invisible_markers) > 0
        assert decoder.provider_signatures is not None
        assert "OPENAI" in decoder.provider_signatures
        assert "GOOGLE" in decoder.provider_signatures

    def test_detect_invisible_markers(self):
        """Should detect invisible unicode markers in text."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import (
            StatisticalWatermarkDecoder,
        )

        decoder = StatisticalWatermarkDecoder()

        text_with_markers = "Hello\u200bWorld\u200cTest"
        detected = decoder.detect_invisible_markers(text_with_markers)

        assert len(detected) == 2
        assert "\u200b" in detected
        assert "\u200c" in detected

    def test_detect_invisible_markers_clean_text(self):
        """Should return empty list for clean text."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import (
            StatisticalWatermarkDecoder,
        )

        decoder = StatisticalWatermarkDecoder()

        clean_text = "Hello World Test"
        detected = decoder.detect_invisible_markers(clean_text)

        assert len(detected) == 0

    def test_tokenize_text(self):
        """Should tokenize text into words."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import (
            StatisticalWatermarkDecoder,
        )

        decoder = StatisticalWatermarkDecoder()

        text = "Hello, world! This is a test."
        tokens = decoder.tokenize_text(text)

        assert "hello" in tokens
        assert "world" in tokens
        assert "this" in tokens
        assert "test" in tokens
        assert "," not in tokens
        assert "!" not in tokens

    def test_calculate_z_scores(self):
        """Should calculate Z-Scores for tokens."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import (
            StatisticalWatermarkDecoder,
        )

        decoder = StatisticalWatermarkDecoder()

        tokens = ["the", "the", "of", "and", "the", "a", "in"] * 100
        z_scores = decoder.calculate_z_scores(tokens)

        assert "the" in z_scores
        assert "of" in z_scores


class TestDetectWatermarkPulse:
    """Tests for detect_watermark_pulse function."""

    def test_detect_clean_text(self):
        """Should return detection results for clean text."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import detect_watermark_pulse

        result = detect_watermark_pulse("Hello world, this is a test.")

        assert "has_invisible_markers" in result
        assert "z_score_analysis" in result
        assert "confidence_score" in result
        assert "status" in result

    def test_detect_text_with_markers(self):
        """Should detect invisible markers."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import detect_watermark_pulse

        text_with_marker = "Hello\u200bWorld\u200cTest"
        result = detect_watermark_pulse(text_with_marker)

        assert result["has_invisible_markers"] is True
        assert len(result["detected_markers"]) > 0

    def test_returns_json_serializable(self):
        """Should return JSON-serializable dictionary."""
        from extensions.ext_stetho_scan.statistical_watermark_decoder import detect_watermark_pulse

        result = detect_watermark_pulse("Test text")

        json_str = json.dumps(result)
        assert json_str is not None


class TestStethoScanPlugin:
    """Tests for StatisticalWatermarkDecoderPlugin class."""

    def test_plugin_creation(self):
        """Should create plugin instance."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        assert plugin.name == "Statistical Watermark Decoder Extension"
        assert plugin.version == "1.0.0"
        assert plugin.is_active is False

    def test_plugin_activate(self):
        """Should activate plugin."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        result = plugin.activate()

        assert result is True
        assert plugin.is_active is True

    def test_plugin_deactivate(self):
        """Should deactivate plugin."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        plugin.activate()
        result = plugin.deactivate()

        assert result is True
        assert plugin.is_active is False

    def test_plugin_get_status(self):
        """Should return status dictionary."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        status = plugin.get_status()

        assert "name" in status
        assert "version" in status
        assert "is_active" in status
        assert "config" in status

    def test_plugin_configure(self):
        """Should update configuration."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        result = plugin.configure(z_score_threshold=3.0)

        assert result is True
        assert plugin.config["z_score_threshold"] == 3.0

    def test_plugin_get_tools(self):
        """Should return detection tools."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        tools = plugin.get_tools()

        assert len(tools) == 1

    def test_plugin_get_hooks(self):
        """Should return event hooks."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        hooks = plugin.get_hooks()

        assert "governor_status_check" in hooks

    def test_plugin_get_events(self):
        """Should return list of events."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        events = plugin.get_events()

        assert "governor_status_changed" in events
        assert "watermark_detected" in events

    def test_plugin_handle_event(self):
        """Should handle events."""
        from extensions.ext_stetho_scan.plugin import StatisticalWatermarkDecoderPlugin

        manifest = {"plugin_id": "test_plugin"}
        plugin = StatisticalWatermarkDecoderPlugin(manifest, None)

        result = plugin.handle_event("detection_started")

        assert result["detection_started"] is True


class TestStethoScanGovernorIntegration:
    """Tests for governor integration."""

    def test_governor_status_info(self):
        """Should return status info."""
        with patch(
            "extensions.ext_stetho_scan.governor_integration.StethoGovernorIntegration.get_status_info"
        ):
            from extensions.ext_stetho_scan.governor_integration import StethoGovernorIntegration

            integration = StethoGovernorIntegration()
            # Should not raise
            integration.get_status_info()


class TestGetPlugin:
    """Tests for plugin factory functions."""

    def test_get_plugin_function(self):
        """Should create plugin via get_plugin."""
        from extensions.ext_stetho_scan.plugin import get_plugin

        plugin = get_plugin()

        assert plugin is not None
        assert plugin.name == "Statistical Watermark Decoder Extension"

    def test_register_extension_function(self):
        """Should create plugin via register_extension."""
        from extensions.ext_stetho_scan.plugin import register_extension

        manifest = {"plugin_id": "test"}
        plugin = register_extension(manifest, None)

        assert plugin is not None
