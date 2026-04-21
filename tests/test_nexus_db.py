"""
Tests for gateway/nexus_db.py - Unified forensic database layer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from gateway.nexus_db import ForensicNexus, get_nexus


def test_nexus_initialization_creates_data_dir(tmp_path):
    base = tmp_path / "data"
    nexus = ForensicNexus(base_dir=str(base))
    assert os.path.exists(base)
    assert os.path.exists(nexus.primary_path)


def test_nexus_attach_subordinates(tmp_path):
    base = tmp_path / "data"
    nexus = ForensicNexus(base_dir=str(base))
    # Subordinate DB files should be created/attached
    # We can check status
    status = nexus.get_status()
    assert "primary" in status
    assert "attached" in status
    # The attached list should include lab, prov, core at minimum
    attached_names = [row["name"] for row in status["attached"]]
    for schema in ("lab", "prov", "core"):
        assert schema in attached_names


def test_nexus_query_select(tmp_path):
    base = tmp_path / "data"
    nexus = ForensicNexus(base_dir=str(base))
    # Create a simple table in primary to test query
    nexus.execute("CREATE TABLE test (id INTEGER, value TEXT)")
    nexus.execute("INSERT INTO test VALUES (1, 'hello')")
    results = nexus.query("SELECT * FROM test")
    assert len(results) == 1
    assert results[0]["id"] == 1
    assert results[0]["value"] == "hello"


def test_nexus_execute_commit(tmp_path):
    base = tmp_path / "data"
    nexus = ForensicNexus(base_dir=str(base))
    nexus.execute("CREATE TABLE foo (id INTEGER)")
    # verify by query
    rows = nexus.query("SELECT name FROM sqlite_master WHERE type='table' AND name='foo'")
    assert len(rows) == 1


def test_nexus_query_error_returns_empty(tmp_path):
    nexus = ForensicNexus(base_dir=str(tmp_path))
    results = nexus.query("SELECT * FROM nonexistent_table")
    assert results == []


def test_nexus_execute_rollback_on_error(tmp_path):
    nexus = ForensicNexus(base_dir=str(tmp_path))
    nexus.execute("CREATE TABLE bar (id INTEGER)")
    # This will fail due to syntax error
    with pytest.raises(Exception):
        nexus.execute("INVALID SQL")
    # Table should still exist (commit didn't happen)
    # But rollback after error ensures no partial commit
    rows = nexus.query("SELECT name FROM sqlite_master WHERE type='table' AND name='bar'")
    assert len(rows) == 1  # table exists, create was before error


def test_get_unified_forensic_feed(tmp_path):
    base = tmp_path / "data"
    nexus = ForensicNexus(base_dir=str(base))
    # Populate lab.forensic_events and prov.source_provenance minimally
    nexus.execute(
        "CREATE TABLE lab.forensic_events (timestamp TEXT, tool_name TEXT, event_type TEXT, target TEXT, confidence REAL)"
    )
    nexus.execute(
        "CREATE TABLE prov.source_provenance (source_id TEXT, reliability_tier TEXT, acquisition_method TEXT)"
    )
    nexus.execute(
        "INSERT INTO lab.forensic_events VALUES ('2024-01-01', 'tool1', 'event1', 'src1', 0.9)"
    )
    nexus.execute("INSERT INTO prov.source_provenance VALUES ('src1', 'high', 'acquired')")
    feed = nexus.get_unified_forensic_feed(limit=10)
    assert len(feed) == 1
    assert feed[0]["tool_name"] == "tool1"
    assert feed[0]["reliability_tier"] == "high"


def test_nexus_singleton():
    a = get_nexus()
    b = get_nexus()
    assert a is b
