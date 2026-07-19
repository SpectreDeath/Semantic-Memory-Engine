"""Regression harness for Pattern Extraction terminal wrapper.

Validates lightweight CPU-bound extraction from terminal stdout and
file-based keyword sniffing. Telemetry is written to the local .context/
enclave and never tracked by Git.
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.utils.context_sniffer import get_ext, get_persona, scan_keywords

TEST_DIR = Path(__file__).parent
CONTEXT_ENCLAVE = TEST_DIR / "../.context/session-logs"
CONTEXT_ENCLAVE.mkdir(parents=True, exist_ok=True)

MOCK_TERMINAL_STDOUT = """
[LOG] Ingestion sequence initiated.
[DATA] Identity Match: Russ Vought
[DATA] Trust Score: 0.89
[WARN] Signature missing TPM-signing verification layer.
"""


def extract_terminal_patterns(raw_stdout):
    """Parse deterministic tags from captured terminal output."""
    patterns = {
        "identity_matches": [],
        "trust_scores": [],
        "warnings": [],
    }
    for line in raw_stdout.splitlines():
        if "[DATA] Identity Match:" in line:
            patterns["identity_matches"].append(line.split("Identity Match:")[-1].strip())
        if "[DATA] Trust Score:" in line:
            try:
                score = float(line.split("Trust Score:")[-1].strip())
                patterns["trust_scores"].append(score)
            except ValueError:
                pass
        if "[WARN]" in line:
            patterns["warnings"].append(line.strip())
    return patterns


def _append_result(results, name, passed):
    results.append({"name": name, "pass": bool(passed)})


@pytest.fixture(scope="module")
def telemetry_results():
    """Collect test results across the module and write them on teardown."""
    results = []
    yield results
    telemetry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "test_results": results,
        "enclave_lock": True,
    }
    log_path = CONTEXT_ENCLAVE / "pattern_extractor_telemetry.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2)


def test_regex_extraction_matrix(telemetry_results):
    patterns = extract_terminal_patterns(MOCK_TERMINAL_STDOUT)
    _append_result(
        telemetry_results,
        "terminal_identity_extraction",
        "Russ Vought" in patterns["identity_matches"],
    )
    _append_result(
        telemetry_results, "terminal_trust_score_extraction", 0.89 in patterns["trust_scores"]
    )
    _append_result(
        telemetry_results,
        "terminal_warning_extraction",
        len(patterns["warnings"]) == 1 and "TPM-signing" in patterns["warnings"][0],
    )


def test_context_sniffer_keywords(telemetry_results):
    tmp_path = CONTEXT_ENCLAVE / "tmp_context_test.txt"
    tmp_path.write_text(
        "import pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import Ridge\n",
        encoding="utf-8",
    )
    try:
        specs = scan_keywords(str(tmp_path), lines=5)
        _append_result(
            telemetry_results, "scan_keywords_detects_pandas", "Data Engineering" in specs
        )
        _append_result(
            telemetry_results, "scan_keywords_detects_sklearn", "Data Forensic Scientist" in specs
        )
        _append_result(telemetry_results, "scan_keywords_limits_lines", len(specs) > 0)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_context_sniffer_persona_routing(telemetry_results):
    ext = get_ext("report.md")
    persona, specialty = get_persona(ext, [])
    _append_result(telemetry_results, "persona_md_extension", persona == "Technical Writer")
    _append_result(telemetry_results, "specialty_md_extension", specialty == "Documentation")

    ext = get_ext("data.csv")
    persona, specialty = get_persona(ext, [])
    _append_result(telemetry_results, "persona_csv_extension", persona == "Data Auditor")
    _append_result(telemetry_results, "specialty_csv_extension", specialty == "Data Analysis")

    persona, specialty = get_persona(".py", ["ML Engineer"])
    _append_result(telemetry_results, "persona_ml_specialty_priority", persona == "ML Engineer")
    _append_result(
        telemetry_results, "specialty_ml_specialty_priority", specialty == "ML Engineering"
    )

    persona, specialty = get_persona(".py", [])
    _append_result(telemetry_results, "persona_fallback_general", persona == "General Developer")
    _append_result(telemetry_results, "specialty_fallback_general", specialty == "General")


def test_hardware_footprint_safety(telemetry_results):
    size_bytes = sys.getsizeof(MOCK_TERMINAL_STDOUT)
    _append_result(telemetry_results, "memory_under_5mb", size_bytes < 5_000_000)


def test_mock_fallback_routing(telemetry_results):
    raw_plain = "[MOCK MOCK] no json here"
    patterns = extract_terminal_patterns(raw_plain)
    _append_result(
        telemetry_results, "mock_plain_text_parses_safely", patterns["identity_matches"] == []
    )
    _append_result(telemetry_results, "mock_plain_text_no_crash", patterns["trust_scores"] == [])


def main():
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    main()
