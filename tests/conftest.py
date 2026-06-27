"""
Pytest Configuration for Tests

Note: Pydantic v2 is used natively. No patches needed.
"""

import logging
import sys

import pytest

logging.basicConfig(level=logging.INFO)


def pytest_collection_modifyitems(config, items):
    """Skip test_advanced_nlp.py on Python 3.14+ due to spacy/pydantic incompatibility."""
    if sys.version_info >= (3, 14):
        items[:] = [item for item in items if "test_advanced_nlp" not in str(item.fspath)]

    for item in items:
        nodeid = item.nodeid
        markers = list(item.iter_markers())
        existing_phases = [m for m in markers if m.name.startswith("phase")]

        if not existing_phases:
            # Phase 1: Core extensions, plugins, infrastructure
            if any(x in nodeid for x in [
                "test_ext_", "test_extension_matrix.py", "test_health_check.py",
                "test_auth.py", "test_security.py", "test_logging.py", "test_rate_limiter.py",
                "test_python_version.py", "test_events.py", "test_harvester.py",
                "test_scribe.py", "test_crawler_sling.py", "test_apb_logic.py",
                "test_factory_thread_safety.py", "test_nexus_db.py", "test_metrics.py"
            ]):
                item.add_marker(pytest.mark.phase1)
            # Phase 2: Processing, NLP, math algorithms, analysis
            elif any(x in nodeid for x in [
                "test_phase_", "test_nlp", "test_forensic", "test_significance",
                "test_graph_walk.py", "test_archival_diff.py", "test_circuit_breaker.py",
                "test_recommendations.py", "test_rolling_delta.py", "test_v2",
                "test_wayback", "test_aether.py", "test_session_manager.py",
                "test_tier1_improvements.py", "test_tools_"
            ]):
                item.add_marker(pytest.mark.phase2)
            # Phase 3: Full integration, skills, end-to-end
            elif any(x in nodeid for x in [
                "test_integration", "test_skills", "test_vindex", "test_omcs",
                "test_scrapegraph", "test_ext_webhook.py", "test_ext_scheduled", "test_ext_api_key"
            ]):
                item.add_marker(pytest.mark.phase3)
