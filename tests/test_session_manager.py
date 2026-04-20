"""
Tests for gateway/session_manager.py - Session management and persistence.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import os
import json
import sqlite3
import tempfile
from unittest.mock import patch
import pytest

from gateway.session_manager import (
    Session,
    SessionManager,
    DB_PATH,
    MAX_HISTORY,
    get_session_manager,
)


@pytest.fixture
def temp_db():
    """Use a temporary directory for session DB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_session.db")
        with patch.dict(os.environ, {"SME_SESSION_DB_PATH": db_path}):
            yield db_path


def test_session_creation():
    sess = Session("sid123")
    assert sess.session_id == "sid123"
    assert sess.history == []
    assert sess.scratchpad == {}


def test_add_history_appends_and_respects_limit():
    sess = Session("sid")
    # MAX_HISTORY default 50; add 55 entries
    for i in range(55):
        sess.add_history("tool_x", {"val": i})
    assert len(sess.history) == 50
    # First entry should be the 5th added (since popped)
    assert sess.history[0]["result"]["val"] == 5
    # Last entry should be 54
    assert sess.history[-1]["result"]["val"] == 54


def test_update_and_get_scratchpad():
    sess = Session("sid")
    sess.update_scratchpad("key1", "value1")
    sess.update_scratchpad("num", 42)
    assert sess.get_scratchpad() == {"key1": "value1", "num": 42}
    # Overwrite
    sess.update_scratchpad("key1", "new")
    assert sess.get_scratchpad()["key1"] == "new"


def test_add_history_logs_to_db(temp_db):
    # Patch the module's DB_PATH to use temp_db
    import gateway.session_manager as sm

    sm.DB_PATH = temp_db
    # Ensure table exists
    conn = sqlite3.connect(temp_db)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forensic_events (
            session_id TEXT, tool_name TEXT, event_type TEXT, target TEXT,
            confidence REAL, metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

    sess = Session("sid123")
    sess.add_history("my_tool", {"status": "ok", "certainty_quotient": 0.9})
    # Check row inserted
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM forensic_events WHERE session_id=?", ("sid123",))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row[1] == "my_tool"
    assert row[2] == "ok"
    assert row[5] is not None  # metadata JSON


def test_session_manager_singleton():
    a = get_session_manager()
    b = get_session_manager()
    assert a is b


def test_session_manager_creates_sessions():
    mgr = get_session_manager()
    sid = "test-session"
    sess = mgr.get_session(sid)
    assert isinstance(sess, Session)
    assert sess.session_id == sid
