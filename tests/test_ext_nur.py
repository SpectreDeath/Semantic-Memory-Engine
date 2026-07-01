"""Tests for ext_nur (Natural Unconstrained Reporter) extension."""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from extensions.ext_nur.forensic_intelligence_reporter import (
    ForensicAnalysis,
    ForensicIntelligenceReporter,
    IntelligenceBucket,
    generate_forensic_intelligence_summary,
)
from extensions.ext_nur.unified_forensic_reporter import (
    ExtensionLogEntry,
    ForensicSummary,
    UnifiedForensicReporter,
    generate_nexus_summary,
)


class TestIntelligenceBucket:
    """Tests for IntelligenceBucket enum."""

    def test_bucket_values_exist(self):
        assert (
            IntelligenceBucket.COMMERCIAL_SAFE.value
            == "Bucket A: Commercial/Safe (OpenAI/Google/Anthropic)"
        )
        assert (
            IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED.value
            == "Bucket B: Open-Source/Unconstrained (Llama/Mistral)"
        )
        assert (
            IntelligenceBucket.HUMAN_AUTHORED.value == "Bucket C: Human-Authored (High Diversity)"
        )
        assert (
            IntelligenceBucket.OBFUSCATED_DECEPTIVE.value
            == "Bucket D: Obfuscated/Deceptive (High Anomaly Score)"
        )


class TestForensicAnalysis:
    """Tests for ForensicAnalysis dataclass."""

    def test_forensic_analysis_creation(self):
        analysis = ForensicAnalysis(
            text_sample="test text",
            behavior_audit_results={"sentiment_volatility": 0.1},
            provenance_profiler_results={"god_term_density": 0.05},
            intelligence_bucket=IntelligenceBucket.COMMERCIAL_SAFE,
            confidence_score=0.9,
            analysis_timestamp=datetime.now(),
            supporting_evidence=["test evidence"],
            risk_assessment="LOW RISK - HIGH CONFIDENCE",
            source_characteristics={"text_length": 9},
        )
        assert analysis.text_sample == "test text"
        assert analysis.confidence_score == 0.9


class TestForensicIntelligenceReporter:
    """Tests for ForensicIntelligenceReporter class."""

    @pytest.fixture
    def reporter(self, tmp_path):
        with patch.object(
            ForensicIntelligenceReporter,
            "__init__",
            lambda self: (
                setattr(self, "report_directory", tmp_path)
                or setattr(self, "_model_signatures_cache", None)
                or setattr(self, "_cache_lock", MagicMock())
                or setattr(self, "bucket_thresholds", {})
            ),
        ):
            reporter = ForensicIntelligenceReporter.__new__(ForensicIntelligenceReporter)
            reporter.bucket_thresholds = {
                IntelligenceBucket.COMMERCIAL_SAFE: {
                    "max_sentiment_volatility": 0.3,
                    "min_lexical_diversity": 0.7,
                    "max_emphatic_qualifiers": 1,
                    "max_non_contracted_denials": 1,
                    "max_synthetic_repetitiveness": 0.3,
                    "min_god_term_density": 0.02,
                    "max_god_term_density": 0.08,
                    "min_distance_markers": 0,
                    "max_distance_markers": 2,
                },
                IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED: {
                    "max_sentiment_volatility": 0.6,
                    "min_lexical_diversity": 0.5,
                    "max_emphatic_qualifiers": 3,
                    "max_non_contracted_denials": 3,
                    "max_synthetic_repetitiveness": 0.5,
                    "min_god_term_density": 0.01,
                    "max_god_term_density": 0.15,
                    "min_distance_markers": 0,
                    "max_distance_markers": 5,
                },
                IntelligenceBucket.HUMAN_AUTHORED: {
                    "max_sentiment_volatility": 0.4,
                    "min_lexical_diversity": 0.8,
                    "max_emphatic_qualifiers": 2,
                    "max_non_contracted_denials": 2,
                    "max_synthetic_repetitiveness": 0.2,
                    "min_god_term_density": 0.0,
                    "max_god_term_density": 0.05,
                    "min_distance_markers": 0,
                    "max_distance_markers": 1,
                },
                IntelligenceBucket.OBFUSCATED_DECEPTIVE: {
                    "min_sentiment_volatility": 0.4,
                    "max_lexical_diversity": 0.6,
                    "min_emphatic_qualifiers": 3,
                    "min_non_contracted_denials": 3,
                    "min_synthetic_repetitiveness": 0.4,
                    "min_god_term_density": 0.05,
                    "min_distance_markers": 2,
                },
            }
            yield reporter

    def test_categorize_commercial_safe(self, reporter):
        behavior = {
            "sentiment_volatility": 0.2,
            "lexical_diversity_score": 0.8,
            "emphatic_qualifiers_count": 0,
            "non_contracted_denials_count": 0,
            "synthetic_repetitiveness_score": 0.1,
        }
        provenance = {
            "god_term_density": 0.03,
            "devil_term_density": 0.01,
            "distance_markers_count": 0,
        }
        bucket, confidence, evidence = reporter._categorize_intelligence_bucket(
            behavior, provenance
        )
        assert bucket == IntelligenceBucket.COMMERCIAL_SAFE
        assert 0.0 <= confidence <= 1.0

    def test_categorize_open_source_unconstrained(self, reporter):
        behavior = {
            "sentiment_volatility": 0.5,
            "lexical_diversity_score": 0.6,
            "emphatic_qualifiers_count": 2,
            "non_contracted_denials_count": 2,
            "synthetic_repetitiveness_score": 0.4,
        }
        provenance = {
            "god_term_density": 0.05,
            "devil_term_density": 0.02,
            "distance_markers_count": 2,
        }
        bucket, confidence, evidence = reporter._categorize_intelligence_bucket(
            behavior, provenance
        )
        assert bucket == IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED

    def test_generate_risk_assessment_high(self, reporter):
        risk = reporter._generate_risk_assessment(IntelligenceBucket.OBFUSCATED_DECEPTIVE, 0.9)
        assert "HIGH" in risk
        assert "CONFIDENCE" in risk

    def test_generate_risk_assessment_low(self, reporter):
        risk = reporter._generate_risk_assessment(IntelligenceBucket.COMMERCIAL_SAFE, 0.5)
        assert "LOW" in risk

    def test_extract_source_characteristics(self, reporter):
        behavior = {
            "sentiment_volatility": 0.3,
            "lexical_diversity_score": 0.7,
            "emphatic_qualifiers_count": 1,
            "non_contracted_denials_count": 0,
            "synthetic_repetitiveness_score": 0.2,
            "anomaly_detected": False,
        }
        provenance = {
            "god_term_density": 0.04,
            "devil_term_density": 0.02,
            "distance_markers_count": 1,
            "profile_detected": True,
        }
        chars = reporter._extract_source_characteristics(behavior, provenance)
        assert "text_length" in chars
        assert chars["sentiment_volatility"] == 0.3

    def test_get_mock_behavior_results(self, reporter):
        results = reporter._get_mock_behavior_results()
        assert "sentiment_volatility" in results
        assert "lexical_diversity_score" in results
        assert "status" in results

    def test_get_mock_provenance_results(self, reporter):
        results = reporter._get_mock_provenance_results()
        assert "god_term_density" in results
        assert "devil_term_density" in results

    def test_check_ghost_trap_persistence(self, reporter):
        result = reporter._check_ghost_trap_persistence()
        assert result is False


class TestGenerateForensicIntelligenceSummary:
    """Tests for generate_forensic_intelligence_summary function."""

    def test_generate_summary_with_mock_data(self, tmp_path):
        with patch(
            "extensions.ext_nur.forensic_intelligence_reporter.ForensicIntelligenceReporter"
        ) as MockReporter:
            mock_instance = MagicMock()
            mock_instance.generate_forensic_intelligence_summary.return_value = {
                "intelligence_bucket": "Bucket A: Commercial/Safe",
                "confidence_score": 0.85,
                "status": "FORENSIC_ANALYSIS_COMPLETED",
            }
            MockReporter.return_value = mock_instance

            result = generate_forensic_intelligence_summary("sample text for analysis")
            assert result["status"] == "FORENSIC_ANALYSIS_COMPLETED"
            assert "intelligence_bucket" in result


class TestExtensionLogEntry:
    """Tests for ExtensionLogEntry dataclass."""

    def test_log_entry_creation(self):
        entry = ExtensionLogEntry(
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
            level="INFO",
            message="Test message",
            extension="TestExtension",
            event_type="GENERAL",
        )
        assert entry.extension == "TestExtension"
        assert entry.level == "INFO"


class TestForensicSummary:
    """Tests for ForensicSummary dataclass."""

    def test_summary_creation(self):
        summary = ForensicSummary(
            overall_health_score=85.5,
            detected_issues=["issue 1"],
            resolved_issues=["issue 2"],
            system_status="GOOD",
            last_scan_time=datetime(2026, 1, 1, 12, 0, 0),
            extension_activity={"ext1": 10, "ext2": 5},
        )
        assert summary.system_status == "GOOD"
        assert summary.overall_health_score == 85.5


class TestUnifiedForensicReporter:
    """Tests for UnifiedForensicReporter class."""

    @pytest.fixture
    def reporter(self, tmp_path):
        reporter = UnifiedForensicReporter.__new__(UnifiedForensicReporter)
        reporter.report_dir = tmp_path
        reporter.log_patterns = {
            "ghost_trap": {
                "files": ["test.log"],
                "event_types": ["POTENTIAL SELF-REPLICATION EVENT"],
                "extension_name": "Ghost Trap",
            },
        }
        yield reporter

    def test_parse_log_line_valid(self, reporter):
        line = "2026-01-01 12:00:00,123 - test.logger - INFO - Test message"
        cutoff = datetime(2026, 1, 1, 0, 0, 0)
        ext_config = {"event_types": ["POTENTIAL"], "extension_name": "TestExt"}
        entry = reporter._parse_log_line(line, ext_config, cutoff)
        assert entry is not None
        assert entry.level == "INFO"
        assert entry.message == "Test message"

    def test_parse_log_line_invalid_format(self, reporter):
        line = "Invalid log line format"
        cutoff = datetime(2026, 1, 1, 0, 0, 0)
        ext_config = {"event_types": [], "extension_name": "TestExt"}
        entry = reporter._parse_log_line(line, ext_config, cutoff)
        assert entry is None

    def test_parse_log_line_old_timestamp(self, reporter):
        line = "2020-01-01 12:00:00,123 - test.logger - INFO - Old entry"
        cutoff = datetime(2026, 1, 1, 0, 0, 0)
        ext_config = {"event_types": [], "extension_name": "TestExt"}
        entry = reporter._parse_log_line(line, ext_config, cutoff)
        assert entry is None

    def test_classify_event_found(self, reporter):
        event = reporter._classify_event(
            "POTENTIAL SELF-REPLICATION EVENT detected", ["POTENTIAL SELF-REPLICATION EVENT"]
        )
        assert event == "POTENTIAL SELF-REPLICATION EVENT"

    def test_classify_event_not_found(self, reporter):
        event = reporter._classify_event("General message", ["POTENTIAL SELF-REPLICATION EVENT"])
        assert event == "GENERAL"

    def test_analyze_system_health_excellent(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="ok",
                extension="Ext",
                event_type="GENERAL",
            )
        ]
        summary = reporter.analyze_system_health(entries)
        assert summary.system_status == "EXCELLENT"
        assert summary.overall_health_score == 100.0

    def test_analyze_system_health_poor(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(),
                level="WARN",
                message="issue",
                extension="Ext",
                event_type="POTENTIAL SELF-REPLICATION EVENT",
            )
            for _ in range(6)
        ]
        summary = reporter.analyze_system_health(entries)
        assert summary.system_status == "POOR"

    def test_calculate_health_score_no_events(self, reporter):
        score = reporter._calculate_health_score({}, 0)
        assert score == 100.0

    def test_calculate_health_score_with_negative_events(self, reporter):
        event_counts = {"Ext-POTENTIAL SELF-REPLICATION EVENT": 2}
        score = reporter._calculate_health_score(event_counts, 10)
        assert score == 70.0


class TestGenerateNexusSummary:
    """Tests for generate_nexus_summary function."""

    def test_generate_nexus_summary_success(self, tmp_path):
        with patch(
            "extensions.ext_nur.unified_forensic_reporter.UnifiedForensicReporter"
        ) as MockReporter:
            mock_instance = MagicMock()
            mock_instance.read_extension_logs.return_value = []
            mock_instance.generate_nexus_summary.return_value = str(tmp_path / "report.md")
            MockReporter.return_value = mock_instance

            result = generate_nexus_summary()
            assert result["status"] == "SUCCESS"

    def test_generate_nexus_summary_failure(self):
        with patch(
            "extensions.ext_nur.unified_forensic_reporter.UnifiedForensicReporter"
        ) as MockReporter:
            mock_instance = MagicMock()
            mock_instance.generate_nexus_summary.return_value = ""
            MockReporter.return_value = mock_instance

            result = generate_nexus_summary()
            assert result["status"] == "FAILED"


class TestUnifiedForensicReporterReportContent:
    """Tests for report content generation."""

    @pytest.fixture
    def reporter(self, tmp_path):
        reporter = UnifiedForensicReporter.__new__(UnifiedForensicReporter)
        reporter.report_dir = tmp_path
        yield reporter

    def test_rnj1_forensic_analysis_healthy(self, reporter):
        conclusion = reporter._rnj1_forensic_analysis(
            health_score=95.0,
            system_status="EXCELLENT",
            detected_count=0,
            resolved_count=0,
            hallucination_events=[],
            replication_events=[],
            watermark_events=[],
            extension_activity={"Ghost Trap": 5},
        )
        assert "EXCELLENT" in conclusion
        assert "LOW" in conclusion

    def test_rnj1_forensic_analysis_with_hallucinations(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(),
                level="WARN",
                message="Hallucination detected",
                extension="Cross-Modal",
                event_type="MULTIMODAL HALLUCINATION DETECTED",
            )
        ]
        conclusion = reporter._rnj1_forensic_analysis(
            health_score=70.0,
            system_status="FAIR",
            detected_count=1,
            resolved_count=0,
            hallucination_events=entries,
            replication_events=[],
            watermark_events=[],
            extension_activity={},
        )
        assert "Multimodal Hallucination Detection" in conclusion

    def test_rnj1_forensic_analysis_with_replication(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(),
                level="ERROR",
                message="Replication detected",
                extension="Ghost Trap",
                event_type="POTENTIAL SELF-REPLICATION EVENT",
            )
        ]
        conclusion = reporter._rnj1_forensic_analysis(
            health_score=50.0,
            system_status="POOR",
            detected_count=1,
            resolved_count=0,
            hallucination_events=[],
            replication_events=entries,
            watermark_events=[],
            extension_activity={},
        )
        assert "Self-Replication" in conclusion


class TestUnifiedForensicReporterPlugin:
    """Tests for UnifiedForensicReporterPlugin class."""

    @pytest.fixture
    def plugin(self):
        from extensions.ext_nur.plugin import UnifiedForensicReporterPlugin

        manifest = {"plugin_id": "test_nur", "name": "Test NUR"}
        nexus_api = MagicMock()
        with (
            patch("extensions.ext_nur.plugin.get_performance_monitor") as mock_perf,
            patch("extensions.ext_nur.plugin.ErrorHandler") as mock_err,
            patch("extensions.ext_nur.plugin.UnifiedForensicReporter") as mock_reporter,
            patch("extensions.ext_nur.plugin.ForensicIntelligenceReporter") as mock_forensic,
        ):
            mock_perf.return_value = MagicMock(get_all_stats=MagicMock(return_value={}))
            mock_err.return_value = MagicMock(
                handle_tool_error=MagicMock(return_value='{"status": "ok"}')
            )
            mock_reporter.return_value = MagicMock(
                generate_nexus_summary=MagicMock(return_value="/tmp/report.md")
            )
            mock_forensic.return_value = MagicMock()
            yield UnifiedForensicReporterPlugin(manifest, nexus_api)

    def test_plugin_initialization(self, plugin):
        assert plugin.plugin_id == "test_nur"
        assert "analysis_period_hours" in plugin.config

    def test_plugin_get_tools(self, plugin):
        tools = plugin.get_tools()
        assert len(tools) == 4


class TestCreatePlugin:
    """Tests for create_plugin and register_extension functions."""

    def test_create_plugin(self):
        from extensions.ext_nur.plugin import create_plugin, UnifiedForensicReporterPlugin

        manifest = {"plugin_id": "test_plugin", "name": "Test"}
        nexus_api = MagicMock()
        with (
            patch("extensions.ext_nur.plugin.get_performance_monitor") as mock_perf,
            patch("extensions.ext_nur.plugin.ErrorHandler"),
            patch("extensions.ext_nur.plugin.UnifiedForensicReporter"),
            patch("extensions.ext_nur.plugin.ForensicIntelligenceReporter"),
        ):
            mock_perf.return_value = MagicMock()
            plugin = create_plugin(manifest, nexus_api)
            assert isinstance(plugin, UnifiedForensicReporterPlugin)

    def test_register_extension(self):
        from extensions.ext_nur.plugin import register_extension, UnifiedForensicReporterPlugin

        manifest = {"plugin_id": "test_reg", "name": "Test"}
        nexus_api = MagicMock()
        with (
            patch("extensions.ext_nur.plugin.get_performance_monitor") as mock_perf,
            patch("extensions.ext_nur.plugin.ErrorHandler"),
            patch("extensions.ext_nur.plugin.UnifiedForensicReporter"),
            patch("extensions.ext_nur.plugin.ForensicIntelligenceReporter"),
        ):
            mock_perf.return_value = MagicMock()
            plugin = register_extension(manifest, nexus_api)
            assert isinstance(plugin, UnifiedForensicReporterPlugin)
