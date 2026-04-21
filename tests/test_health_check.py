"""
Tests for gateway/health_check.py - Health monitoring checks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import os
from unittest.mock import MagicMock, patch

import pytest

from gateway.health_check import (
    REQUIRED_ENV_VARS,
    _check_ai_provider,
    _check_disk_space,
    _check_environment,
    _check_postgresql,
    _check_sqlite,
)


def test_check_postgresql_success():
    mock_conn = MagicMock()
    with patch("psycopg2.connect", return_value=mock_conn) as mock_connect:
        result = _check_postgresql()
        assert result["status"] == "pass"
        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()


def test_check_postgresql_operational_error():
    import psycopg2

    with patch("psycopg2.connect", side_effect=psycopg2.OperationalError("connection refused")):
        result = _check_postgresql()
        assert result["status"] == "fail"
        assert "connection failed" in result["message"]


def test_check_sqlite_success(tmp_path):
    db_file = tmp_path / "forensic_nexus.db"
    import sqlite3

    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.close()
    with patch.dict(os.environ, {"SME_DATA_DIR": str(tmp_path)}):
        result = _check_sqlite()
        assert result["status"] == "pass"


def test_check_sqlite_not_found():
    with patch.dict(os.environ, {"SME_DATA_DIR": "/nonexistent"}):
        result = _check_sqlite()
        assert result["status"] == "fail"
        assert "not found" in result["message"]


def test_check_ai_provider_success():
    mock_provider = MagicMock()
    mock_provider.__class__ = type("MockProvider", (), {})
    with patch("src.ai.providers.factory.get_provider", return_value=mock_provider):
        result = _check_ai_provider()
        assert result["status"] == "pass"
        assert "MockProvider" in result["message"]


def test_check_ai_provider_failure():
    with patch("src.ai.providers.factory.get_provider", side_effect=Exception("init error")):
        result = _check_ai_provider()
        assert result["status"] == "fail"


def test_check_environment_all_present():
    env = dict.fromkeys(REQUIRED_ENV_VARS, "value")
    with patch.dict(os.environ, env, clear=False):
        result = _check_environment()
        assert result["status"] == "pass"


def test_check_environment_missing():
    # Ensure only a couple are set; SME_HSM_SECRET missing -> should fail
    env = {"SME_GATEWAY_SECRET": "secret", "SME_ADMIN_PASSWORD": "pass"}
    with patch.dict(os.environ, env, clear=True):
        result = _check_environment()
        assert result["status"] == "fail"
        assert "SME_HSM_SECRET" in result["message"]


def test_check_disk_space_success(tmp_path):
    # Ensure tmp_path exists and is accessible
    with patch.dict(os.environ, {"SME_DATA_DIR": str(tmp_path)}):
        result = _check_disk_space()
        # Should pass checks for existence
        assert result["status"] == "pass"


def test_check_disk_space_missing():
    with patch.dict(os.environ, {"SME_DATA_DIR": "/nonexistent_dir_12345"}):
        result = _check_disk_space()
        assert result["status"] == "fail"
        assert "not found" in result["message"]
