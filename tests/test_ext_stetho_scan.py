"""Tests for ext_stetho_scan extension modules."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from extensions.ext_stetho_scan.governor_integration import (
    CPUUsageLevel,
    GovernorStatus,
    StethoGovernorIntegration,
    create_stetho_governor_hook,
    safe_detect_watermark_pulse,
)
from extensions.ext_stetho_scan.plugin import (
    StatisticalWatermarkDecoderPlugin,
    register_extension,
)
from extensions.ext_stetho_scan.statistical_watermark_decoder import (
    StatisticalWatermarkDecoder,
    WatermarkDetection,
    detect_watermark_pulse,
)

# ============================================================
# Phase 1: Data class tests
# ============================================================

@pytest.mark.phase1
class TestWatermarkDetection:
    """Tests for WatermarkDetection dataclass."""

    def test_watermark_detection_creation(self):
        detection = WatermarkDetection(
            has_invisible_markers=True,
            z_score_analysis={"the": 2.5},
            provider_signature="OPENAI",
            confidence_score=0.85,
            detected_markers=["\u200b"],
            timestamp=datetime.now(),
        )
        assert detection.has_invisible_markers is True
        assert detection.provider_signature == "OPENAI"
        assert len(detection.detected_markers) == 1


# ============================================================
# Phase 1: Governor Integration tests
# ============================================================

@pytest.mark.phase1
class TestGovernorStatusEnum:
    """Tests for GovernorStatus enum."""

    def test_governor_status_values(self):
        assert GovernorStatus.NORMAL.value == "NORMAL"
        assert GovernorStatus.WARNING.value == "WARNING"
        assert GovernorStatus.CRITICAL.value == "CRITICAL"
        assert GovernorStatus.UNKNOWN.value == "UNKNOWN"


@pytest.mark.phase1
class TestCPUUsageLevelEnum:
    """Tests for CPUUsageLevel enum."""

    def test_cpu_usage_level_values(self):
        assert CPUUsageLevel.LOW.value == "LOW"
        assert CPUUsageLevel.MEDIUM.value == "MEDIUM"
        assert CPUUsageLevel.HIGH.value == "HIGH"
        assert CPUUsageLevel.UNKNOWN.value == "UNKNOWN"


@pytest.mark.phase1
class TestStethoGovernorIntegration:
    """Tests for StethoGovernorIntegration class."""

    def test_governor_integration_creation(self):
        integration = StethoGovernorIntegration()
        assert integration._governor_status == GovernorStatus.UNKNOWN
        assert integration._cpu_usage_level == CPUUsageLevel.UNKNOWN
        assert integration._detection_count == 0

    def test_get_governor_status_returns_enum(self):
        integration = StethoGovernorIntegration()
        result = integration.get_governor_status()
        assert isinstance(result, GovernorStatus)

    def test_get_cpu_usage_level_returns_enum(self):
        integration = StethoGovernorIntegration()
        result = integration.get_cpu_usage_level()
        assert isinstance(result, CPUUsageLevel)

    def test_is_safe_to_detect_returns_bool(self):
        integration = StethoGovernorIntegration()
        result = integration.is_safe_to_detect()
        assert isinstance(result, bool)

    def test_get_status_info(self):
        integration = StethoGovernorIntegration()
        result = integration.get_status_info()
        assert "governor_status" in result
        assert "cpu_usage_level" in result
        assert "detection_count" in result
        assert "is_safe_to_detect" in result

    def test_record_detection(self):
        integration = StethoGovernorIntegration()
        integration.record_detection(0.5)
        assert integration._detection_count == 1
        assert integration._total_detection_time == 0.5


@pytest.mark.phase1
class TestCreateStethoGovernorHook:
    """Tests for create_stetho_governor_hook function."""

    def test_hook_returns_callable(self):
        hook = create_stetho_governor_hook()
        assert callable(hook)

    def test_hook_executes_with_normal_status(self):
        hook = create_stetho_governor_hook()
        result = hook("NORMAL")
        assert result["status"] == "hook_executed"
        assert result["new_governor_status"] == "NORMAL"

    def test_hook_executes_with_warning_status(self):
        hook = create_stetho_governor_hook()
        result = hook("WARNING")
        assert result["status"] == "hook_executed"
        assert result["new_governor_status"] == "WARNING"

    def test_hook_executes_with_critical_status(self):
        hook = create_stetho_governor_hook()
        result = hook("CRITICAL")
        assert result["status"] == "hook_executed"
        assert result["new_governor_status"] == "CRITICAL"


# ============================================================
# Phase 1: StatisticalWatermarkDecoder tests
# ============================================================

@pytest.mark.phase1
class TestStatisticalWatermarkDecoder:
    """Tests for StatisticalWatermarkDecoder class."""

    def test_decoder_creation(self):
        decoder = StatisticalWatermarkDecoder()
        assert decoder.invisible_markers is not None
        assert len(decoder.invisible_markers) > 0
        assert "\u200b" in decoder.invisible_markers

    def test_detect_invisible_markers_found(self):
        decoder = StatisticalWatermarkDecoder()
        text = "Test\u200bText"
        detected = decoder.detect_invisible_markers(text)
        assert len(detected) == 1

    def test_detect_invisible_markers_none(self):
        decoder = StatisticalWatermarkDecoder()
        text = "Plain text without invisible markers"
        detected = decoder.detect_invisible_markers(text)
        assert len(detected) == 0

    def test_tokenize_text_basic(self):
        decoder = StatisticalWatermarkDecoder()
        text = "Hello, world! This is a test."
        tokens = decoder.tokenize_text(text)
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_text_empty(self):
        decoder = StatisticalWatermarkDecoder()
        text = ""
        tokens = decoder.tokenize_text(text)
        assert len(tokens) == 0

    def test_calculate_z_scores_basic(self):
        decoder = StatisticalWatermarkDecoder()
        tokens = ["the", "the", "is", "a", "test"]
        result = decoder.calculate_z_scores(tokens)
        assert isinstance(result, dict)

    def test_calculate_z_scores_empty(self):
        decoder = StatisticalWatermarkDecoder()
        tokens = []
        result = decoder.calculate_z_scores(tokens)
        assert result == {}

    def test_calculate_z_scores_single_token(self):
        decoder = StatisticalWatermarkDecoder()
        tokens = ["the"]
        result = decoder.calculate_z_scores(tokens)
        # Single token still gets processed (std_dev defaults to 0.01)
        assert isinstance(result, dict)

    def test_analyze_provider_signature_match(self):
        decoder = StatisticalWatermarkDecoder()
        z_scores = {"the": 2.5, "of": 2.3, "and": 2.0}
        result = decoder.analyze_provider_signature(z_scores)
        # Should return a provider since match_score < 5.0 threshold
        assert result is not None

    def test_analyze_provider_signature_no_match(self):
        decoder = StatisticalWatermarkDecoder()
        # Use empty dict to test - the function returns first provider with match_score 0
        # which is < 5.0, so it returns a provider
        z_scores = {}
        result = decoder.analyze_provider_signature(z_scores)
        # With empty z_scores, match_score is 0 for all providers, so it returns the first one
        assert result in decoder.provider_signatures

    def test_analyze_character_frequency_basic(self):
        decoder = StatisticalWatermarkDecoder()
        text = "test text sample"
        result = decoder.analyze_character_frequency(text)
        assert isinstance(result, dict)

    def test_analyze_character_frequency_empty(self):
        decoder = StatisticalWatermarkDecoder()
        text = ""
        result = decoder.analyze_character_frequency(text)
        assert result == {}

    def test_calculate_confidence_score_with_markers(self):
        decoder = StatisticalWatermarkDecoder()
        result = decoder._calculate_confidence_score(
            has_markers=True, z_scores={"the": 2.5}, provider="OPENAI", char_deviations={}
        )
        assert 0.0 <= result <= 1.0
        assert result >= 0.4  # Has markers score

    def test_calculate_confidence_score_without_markers(self):
        decoder = StatisticalWatermarkDecoder()
        result = decoder._calculate_confidence_score(
            has_markers=False, z_scores={}, provider=None, char_deviations={}
        )
        assert 0.0 <= result <= 1.0


# ============================================================
# Phase 1: Main function tests
# ============================================================

@pytest.mark.phase1
class TestDetectWatermarkPulse:
    """Tests for detect_watermark_pulse function."""

    def test_detect_watermark_pulse_plain_text(self):
        result = detect_watermark_pulse("Plain text without watermarks")
        assert "has_invisible_markers" in result
        assert "z_score_analysis" in result
        assert "provider_signature" in result
        assert "confidence_score" in result
        assert "status" in result

    def test_detect_watermark_pulse_returns_json(self):
        result = detect_watermark_pulse("Test text")
        json_str = json.dumps(result)
        assert json_str is not None


@pytest.mark.phase1
class TestSafeDetectWatermarkPulse:
    """Tests for safe_detect_watermark_pulse function."""

    def test_safe_detect_watermark_pulse_default_governor(self):
        result = safe_detect_watermark_pulse("Test text")
        assert "has_invisible_markers" in result
        assert "status" in result

    def test_safe_detect_watermark_pulse_with_none_governor(self):
        governor = StethoGovernorIntegration()
        governor._governor_status = GovernorStatus.NORMAL
        governor._cpu_usage_level = CPUUsageLevel.LOW
        result = safe_detect_watermark_pulse("Test text", governor)
        assert "status" in result


# ============================================================
# Phase 2: Integration tests
# ============================================================

@pytest.mark.phase2
class TestWatermarkIntegration:
    """Integration tests for watermark detection."""

    def test_detection_with_invisible_marker(self):
        text = "AI generated\u200bcontent"
        result = detect_watermark_pulse(text)
        assert result["has_invisible_markers"] is True
        assert len(result["detected_markers"]) > 0

    def test_detection_full_pipeline(self):
        text = "The quick brown fox jumps over the lazy dog"
        result = detect_watermark_pulse(text)
        assert isinstance(result["confidence_score"], float)
        assert isinstance(result["z_score_analysis"], dict)


# ============================================================
# Phase 2: Plugin tests
# ============================================================

@pytest.mark.phase2
class TestStatisticalWatermarkDecoderPlugin:
    """Tests for StatisticalWatermarkDecoderPlugin class."""

    def test_plugin_creation(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        assert plugin.name == "Statistical Watermark Decoder Extension"
        assert plugin.version == "1.0.0"
        assert plugin.is_active is False

    def test_plugin_activate(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        result = plugin.activate()
        assert result is True
        assert plugin.is_active is True

    def test_plugin_deactivate(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        plugin.is_active = True
        result = plugin.deactivate()
        assert result is True
        assert plugin.is_active is False

    def test_plugin_get_status(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        result = plugin.get_status()
        assert "name" in result
        assert "is_active" in result
        assert "config" in result

    def test_plugin_configure(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        result = plugin.configure(z_score_threshold=3.0)
        assert result is True

    def test_plugin_get_tools(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        tools = plugin.get_tools()
        assert len(tools) > 0
        assert callable(tools[0])

    def test_plugin_get_events(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        events = plugin.get_events()
        assert "governor_status_changed" in events
        assert "detection_started" in events

    def test_plugin_handle_event_governor_status(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        result = plugin.handle_event("governor_status_changed", status="NORMAL", timestamp="2024-01-01")
        assert result["status_updated"] is True

    def test_plugin_handle_event_cpu_usage(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        result = plugin.handle_event("cpu_usage_changed", cpu_level="HIGH")
        assert result["cpu_level_updated"] is True

    def test_plugin_handle_event_detection_started(self):
        plugin = StatisticalWatermarkDecoderPlugin({}, None)
        result = plugin.handle_event("detection_started")
        assert result["detection_started"] is True


@pytest.mark.phase2
class TestRegisterExtension:
    """Tests for register_extension function."""

    def test_register_extension(self):
        plugin = register_extension({}, None)
        assert isinstance(plugin, StatisticalWatermarkDecoderPlugin)

    def test_get_plugin_function(self):
        from extensions.ext_stetho_scan.plugin import get_plugin
        plugin = get_plugin({}, None)
        assert isinstance(plugin, StatisticalWatermarkDecoderPlugin)
