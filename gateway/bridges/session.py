"""
Session Bridge - Scratchpad and session state access
=====================================================
Modular interface for managing session scratchpads and retrieving session state.
"""

from __future__ import annotations

import logging
from typing import Any

from gateway.session_manager import get_session_manager

logger = logging.getLogger("lawnmower.bridges.session")


class SessionBridge:
    """Handles session scratchpad access."""

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id = session_id

    def get_session_entry(self, key: str) -> Any:
        """Retrieve data from the current session's scratchpad."""
        if not self.session_id:
            return None
        sm = get_session_manager()
        session = sm.get_session(self.session_id)
        if session and hasattr(session, "scratchpad"):
            return session.scratchpad.get(key)
        return None

    def get_session(self) -> Any | None:
        """Get the full session object."""
        if not self.session_id:
            return None
        sm = get_session_manager()
        return sm.get_session(self.session_id)
