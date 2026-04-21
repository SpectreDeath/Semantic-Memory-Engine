"""
Tests for gateway/harvester.py - Evidence harvesting and fingerprinting.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import os
import tempfile

import pytest

from gateway.harvester import EvidenceHarvester


def test_clean_text_removes_urls():
    h = EvidenceHarvester()
    text = "Visit https://example.com and http://test.org for info."
    cleaned = h.clean_text(text)
    assert "[URL]" in cleaned
    assert "example.com" not in cleaned


def test_clean_text_removes_emails():
    h = EvidenceHarvester()
    text = "Contact admin@example.com or support@test.org."
    cleaned = h.clean_text(text)
    assert "[EMAIL]" in cleaned
    assert "admin@example.com" not in cleaned


def test_clean_text_removes_jargon():
    h = EvidenceHarvester()
    text = "This API returns JSON via HTTPS using an SDK."
    cleaned = h.clean_text(text)
    assert "[JARGON]" in cleaned
    assert "API" not in cleaned
    assert "JSON" not in cleaned


def test_clean_text_combined():
    h = EvidenceHarvester()
    text = "Check http://site.com or email test@test.com. Uses MCP."
    cleaned = h.clean_text(text)
    assert "[URL]" in cleaned and "[EMAIL]" in cleaned and "[JARGON]" in cleaned


def test_walk_directory(tmp_path):
    # Create temp files
    f1 = tmp_path / "a.txt"
    f1.write_text("Hello world")
    f2 = tmp_path / "b.log"
    f2.write_text("Log entry")
    sub = tmp_path / "sub"
    sub.mkdir()
    f3 = sub / "c.md"
    f3.write_text("# Markdown header")

    h = EvidenceHarvester()
    combined = h.walk_directory(str(tmp_path))
    assert "Hello world" in combined
    assert "Log entry" in combined
    assert "# Markdown header" in combined
    # unsupported extension .py ignored
    f4 = tmp_path / "d.py"
    f4.write_text("print('python')")
    combined2 = h.walk_directory(str(tmp_path))
    assert "print" not in combined2


def test_walk_directory_not_found():
    h = EvidenceHarvester()
    with pytest.raises(FileNotFoundError):
        h.walk_directory("/nonexistent/path")


def test_generate_fingerprint_basic():
    h = EvidenceHarvester()
    text = "hello world hello"
    fp = h.generate_stylometric_fingerprint(text)
    assert fp["total_tokens"] == 3
    assert fp["vocabulary_size"] == 2
    assert ("hello", 2) in fp["top_tokens"]
    assert "world" in dict(fp["top_tokens"])


def test_generate_fingerprint_empty():
    h = EvidenceHarvester()
    fp = h.generate_stylometric_fingerprint("")
    assert fp["total_tokens"] == 0
    assert fp["vocabulary_size"] == 0
    assert fp["token_counts"] == {}
    assert fp["top_tokens"] == []


def test_harvest_integration(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("Test data with some content.")
    h = EvidenceHarvester()
    result = h.harvest(str(tmp_path))
    assert "token_counts" in result
    assert result["total_tokens"] > 0
