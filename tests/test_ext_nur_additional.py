"""Additional tests for ext_nur extension - full coverage."""

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
    UnifiedForensicReporter,
    generate_nexus_summary,
)


@pytest.mark.phase1
class TestUnifiedForensicReporterFullCoverage:
    """Additional tests for full coverage of UnifiedForensicReporter."""

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
            "stetho_scan": {
                "files": ["watermark.log"],
                "event_types": ["PROVENANCE IDENTIFIED", "DETECTION BLOCKED"],
                "extension_name": "Stetho",
            },
        }
        yield reporter

    def test_read_extension_logs_missing_file(self, reporter):
        entries = reporter.read_extension_logs(hours_back=24)
        assert entries == []

    def test_analyze_system_health_with_verified(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(), level="INFO", message="ok",
                extension="Ext", event_type="MULTIMODAL SYNC VERIFIED"
            )
        ]
        summary = reporter.analyze_system_health(entries)
        assert summary.system_status == "EXCELLENT"

    def test_analyze_system_health_fair(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(), level="WARN", message="issue",
                extension="Ext", event_type="MULTIMODAL HALLUCINATION DETECTED"
            )
            for _ in range(3)
        ]
        summary = reporter.analyze_system_health(entries)
        assert summary.system_status in ["FAIR", "GOOD"]

    def test_rnj1_forensic_analysis_with_watermarks(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(), level="INFO", message="Watermark found",
                extension="Stetho", event_type="PROVENANCE IDENTIFIED"
            )
        ]
        conclusion = reporter._rnj1_forensic_analysis(
            health_score=75.0,
            system_status="FAIR",
            detected_count=1,
            resolved_count=0,
            hallucination_events=[],
            replication_events=[],
            watermark_events=entries,
            extension_activity={"Stetho": 5},
        )
        assert "Watermark Detection" in conclusion

    def test_rnj1_forensic_analysis_all_events(self, reporter):
        entries = [
            ExtensionLogEntry(
                timestamp=datetime.now(), level="WARN", message="Hallucination detected",
                extension="Cross-Modal", event_type="MULTIMODAL HALLUCINATION DETECTED"
            ),
            ExtensionLogEntry(
                timestamp=datetime.now(), level="ERROR", message="Replication detected",
                extension="Ghost Trap", event_type="POTENTIAL SELF-REPLICATION EVENT"
            ),
            ExtensionLogEntry(
                timestamp=datetime.now(), level="INFO", message="Watermark found",
                extension="Stetho", event_type="PROVENANCE IDENTIFIED"
            ),
        ]
        conclusion = reporter._rnj1_forensic_analysis(
            health_score=60.0,
            system_status="POOR",
            detected_count=3,
            resolved_count=0,
            hallucination_events=[entries[0]],
            replication_events=[entries[1]],
            watermark_events=[entries[2]],
            extension_activity={"Cross-Modal": 1, "Ghost Trap": 1, "Stetho": 1},
        )
        assert "Multimodal Hallucination Detection" in conclusion
        assert "Self-Replication" in conclusion
        assert "Watermark Detection" in conclusion

    def test_calculate_health_score_all_event_types(self, reporter):
        event_counts = {
            "Ext-POTENTIAL SELF-REPLICATION EVENT": 1,
            "Ext-MULTIMODAL HALLUCINATION DETECTED": 1,
            "Ext-PROVENANCE IDENTIFIED": 1,
            "Ext-DETECTION BLOCKED": 1,
            "Ext-MULTIMODAL SYNC VERIFIED": 1,
        }
        score = reporter._calculate_health_score(event_counts, 10)
        assert 0.0 <= score <= 100.0


@pytest.mark.phase1
class TestForensicIntelligenceReporterFullCoverage:
    """Additional tests for full coverage of ForensicIntelligenceReporter."""

    @pytest.fixture
    def reporter(self, tmp_path):
        reporter = ForensicIntelligenceReporter.__new__(ForensicIntelligenceReporter)
        reporter.report_directory = tmp_path
        reporter._model_signatures_cache = None
        reporter._cache_lock = MagicMock()
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

    def test_analyze_model_signatures_empty(self, reporter):
        with patch.object(reporter, "_load_model_signatures", return_value={"model_signatures": {}, "metadata": {}}):
            result = reporter._analyze_model_signatures({"god_term_density": 0.03, "devil_term_density": 0.01, "distance_markers_count": 0})
            assert "Unknown" in result

    def test_generate_report_content_with_ghost_trap_override(self, reporter, tmp_path):
        analysis = ForensicAnalysis(
            text_sample="test text",
            behavior_audit_results={"sentiment_volatility": 0.2},
            provenance_profiler_results={"god_term_density": 0.03},
            intelligence_bucket=IntelligenceBucket.COMMERCIAL_SAFE,
            confidence_score=0.8,
            analysis_timestamp=datetime.now(),
            supporting_evidence=["evidence 1"],
            risk_assessment="LOW RISK",
            source_characteristics={"text_length": 9, "sentiment_volatility": 0.2, "lexical_diversity": 0.8, "emphatic_qualifiers": 0, "non_contracted_denials": 0, "synthetic_repetitiveness": 0.1, "god_term_density": 0.03, "devil_term_density": 0.01, "distance_markers": 0, "anomaly_detected": False, "profile_detected": False},
        )
        content = reporter._create_report_content(analysis, "Test Origin", ghost_trap_override=True)
        assert "CRITICAL" in content or "Ghost-Trap" in content or "CRITICAL SECURITY EVENTS" in content