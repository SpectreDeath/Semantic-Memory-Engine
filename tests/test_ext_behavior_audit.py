"""Tests for ext_behavior_audit extension modules."""

import json
from unittest.mock import MagicMock, patch

import pytest

from extensions.ext_behavior_audit.provenance_profiler import (
    ProvenanceProfile,
    ProvenanceProfiler,
    profile_rhetorical_motive,
)
from extensions.ext_behavior_audit.rhetorical_behavior_audit import (
    RhetoricalAnalysis,
    RhetoricalBehaviorAuditor,
    audit_rhetorical_behavior,
)

# ============================================================
# Phase 1: Data classes and simple initialization tests
# ============================================================


@pytest.mark.phase1
class TestRhetoricalAnalysis:
    """Tests for RhetoricalAnalysis dataclass."""

    def test_rhetorical_analysis_creation(self):
        analysis = RhetoricalAnalysis(
            sentiment_volatility=0.5,
            type_token_ratio=0.6,
            lexical_diversity_score=0.7,
            emphatic_qualifiers_count=2,
            non_contracted_denials_count=1,
            synthetic_repetitiveness_score=0.4,
            deceptive_indicators=["emphatic"],
            anomaly_detected=True,
            confidence_score=0.85,
            timestamp=None,
        )
        assert analysis.sentiment_volatility == 0.5
        assert analysis.anomaly_detected is True
        assert "emphatic" in analysis.deceptive_indicators


@pytest.mark.phase1
class TestProvenanceProfile:
    """Tests for ProvenanceProfile dataclass."""

    def test_provenance_profile_creation(self):
        from datetime import datetime

        profile = ProvenanceProfile(
            god_term_density=0.1,
            devil_term_density=0.05,
            total_ultimate_term_density=0.15,
            distance_markers_count=3,
            god_terms_found=["truth", "justice"],
            devil_terms_found=["evil"],
            distance_markers_found=["The Model"],
            profile_detected=True,
            confidence_score=0.8,
            processing_time=0.123,
            timestamp=datetime.now(),
        )
        assert profile.god_term_density == 0.1
        assert profile.profile_detected is True
        assert len(profile.god_terms_found) == 2


# ============================================================
# Phase 1: RhetoricalBehaviorAuditor simple method tests
# ============================================================


@pytest.mark.phase1
class TestRhetoricalBehaviorAuditorSimple:
    """Simple tests for RhetoricalBehaviorAuditor without NLTK."""

    def test_auditor_creation(self):
        auditor = RhetoricalBehaviorAuditor()
        assert auditor.emphatic_qualifiers is not None
        assert len(auditor.emphatic_qualifiers) > 0
        assert (
            "truth" in auditor.emphatic_qualifiers or "in all candor" in auditor.emphatic_qualifiers
        )

    def test_detect_emphatic_qualifiers_found(self):
        auditor = RhetoricalBehaviorAuditor()
        text = "In all candor, I must tell you the truth"
        detected = auditor.detect_emphatic_qualifiers(text)
        assert "in all candor" in detected or "truth" in detected

    def test_detect_emphatic_qualifiers_none(self):
        auditor = RhetoricalBehaviorAuditor()
        text = "This is plain ordinary text without qualifiers"
        detected = auditor.detect_emphatic_qualifiers(text)
        assert len(detected) == 0 or "in all candor" not in detected

    def test_detect_non_contracted_denials_found(self):
        auditor = RhetoricalBehaviorAuditor()
        text = "I do not agree with this position"
        detected = auditor.detect_non_contracted_denials(text)
        assert "i do not" in detected

    def test_detect_non_contracted_denials_none(self):
        auditor = RhetoricalBehaviorAuditor()
        text = "This is simple text with no denials"
        detected = auditor.detect_non_contracted_denials(text)
        assert len(detected) == 0


# ============================================================
# Phase 1: ProvenanceProfiler tests
# ============================================================


@pytest.mark.phase1
class TestProvenanceProfilerSimple:
    """Simple tests for ProvenanceProfiler."""

    def test_profiler_creation(self):
        profiler = ProvenanceProfiler()
        assert profiler.god_terms is not None
        assert profiler.devil_terms is not None
        assert profiler.distance_markers is not None
        assert "truth" in profiler.god_terms
        assert "evil" in profiler.devil_terms

    def test_find_god_terms(self):
        profiler = ProvenanceProfiler()
        text = "This is the truth and justice we seek"
        found = profiler._find_god_terms(text.lower())
        assert "truth" in found or "justice" in found

    def test_find_god_terms_none(self):
        profiler = ProvenanceProfiler()
        text = "ordinary text without ultimate terms"
        found = profiler._find_god_terms(text.lower())
        assert len(found) == 0

    def test_find_devil_terms(self):
        profiler = ProvenanceProfiler()
        text = "This evil corruption must end"
        found = profiler._find_devil_terms(text.lower())
        assert "evil" in found or "corruption" in found

    def test_find_devil_terms_none(self):
        profiler = ProvenanceProfiler()
        text = "ordinary text without negative connotations whatsoever today"
        found = profiler._find_devil_terms(text.lower())
        assert len(found) == 0

    def test_find_distance_markers(self):
        profiler = ProvenanceProfiler()
        text = "The model responded with accuracy"
        found = profiler._find_distance_markers(text.lower())
        assert len(found) > 0
        assert "The Model" in found

    def test_find_distance_markers_none(self):
        profiler = ProvenanceProfiler()
        text = "I responded myself personally"
        found = profiler._find_distance_markers(text.lower())
        assert len(found) == 0

    def test_detect_commercial_policy_profile_true(self):
        profiler = ProvenanceProfiler()
        result = profiler._detect_commercial_policy_profile(
            0.1, 5
        )  # High god term density + many markers
        assert result is True

    def test_detect_commercial_policy_profile_false_low_density(self):
        profiler = ProvenanceProfiler()
        result = profiler._detect_commercial_policy_profile(0.01, 5)  # Low god term density
        assert result is False

    def test_detect_commercial_policy_profile_false_low_markers(self):
        profiler = ProvenanceProfiler()
        result = profiler._detect_commercial_policy_profile(
            0.1, 1
        )  # High god term density but few markers
        assert result is False


@pytest.mark.phase1
class TestProvenanceProfilerIntegration:
    """Integration tests for ProvenanceProfiler."""

    def test_profile_rhetorical_motive_high_god_terms(self):
        text = "the truth and justice and wisdom and knowledge guide us"
        result = profile_rhetorical_motive(text)
        assert "god_term_density" in result
        assert "devil_term_density" in result
        assert "status" in result

    def test_profile_rhetorical_motive_with_distance_markers(self):
        text = "the model responded. the system processed. the algorithm computed."
        result = profile_rhetorical_motive(text)
        assert result["distance_markers_count"] >= 3


# ============================================================
# Phase 1: Helper method tests
# ============================================================


@pytest.mark.phase1
class TestRhetoricalAuditorHelpers:
    """Tests for RhetoricalBehaviorAuditor helper methods."""

    def test_calculate_lexical_diversity_high(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor.calculate_lexical_diversity_score(0.8)
        assert result == 1.0

    def test_calculate_lexical_diversity_medium(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor.calculate_lexical_diversity_score(0.6)
        assert result == 0.8

    def test_calculate_lexical_diversity_low(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor.calculate_lexical_diversity_score(0.25)
        assert result == 0.3  # ttr >= 0.1 returns 0.3

    def test_calculate_lexical_diversity_very_low(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor.calculate_lexical_diversity_score(0.05)
        assert result == 0.1

    def test_detect_rhetorical_anomaly_true_low_diversity_high_emphatic(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor._detect_rhetorical_anomaly(0.3, 2, 0.5)
        assert result is True

    def test_detect_rhetorical_anomaly_true_low_diversity_high_repetitive(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor._detect_rhetorical_anomaly(0.3, 0, 0.8)
        assert result is True

    def test_detect_rhetorical_anomaly_false_high_diversity(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor._detect_rhetorical_anomaly(0.7, 2, 0.5)
        assert result is False

    def test_calculate_confidence_score(self):
        auditor = RhetoricalBehaviorAuditor()
        result = auditor._calculate_confidence_score(0.6, 0.1, 2, 1, 0.5, True)
        assert 0.0 <= result <= 1.0


# ============================================================
# Phase 2: Main function tests with mocked NLTK
# ============================================================


@pytest.mark.phase2
class TestRhetoricalBehaviorAuditMain:
    """Tests for main audit_rhetorical_behavior function."""

    def test_audit_rhetorical_behavior_clean(self):
        text = "This is plain ordinary text for testing purposes"
        result = audit_rhetorical_behavior(text)
        assert "sentiment_volatility" in result
        assert "anomaly_detected" in result
        assert "status" in result

    def test_audit_rhetorical_behavior_returns_json(self):
        text = "Test text for audit"
        result = audit_rhetorical_behavior(text)
        json_str = json.dumps(result)
        assert json_str is not None
