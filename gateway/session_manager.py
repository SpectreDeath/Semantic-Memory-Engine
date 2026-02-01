"""
Session Manager - Context Persistence for Project Lawnmower Man

Handles cross-call state, temporary knowledge retention, and result history.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "storage", "laboratory.db"))

class Session:
    """Individual user/agent session."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.history: List[Dict[str, Any]] = []  # Last 10 tool results
        self.scratchpad: Dict[str, Any] = {}     # Temporary facts/context
        self.metadata: Dict[str, Any] = {}       # Intent tracking, user info
        
    def add_history(self, tool_name: str, result: Any):
        """Add record to history, maintaining max 10 entries."""
        self.history.append({
            "id": f"res_{len(self.history)}",
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "result": result
        })
        if len(self.history) > 10:
            self.history.pop(0)
        self.last_accessed = datetime.now()
        
        # Persist to forensic_events table for visualization (The Beacon)
        self._log_to_db(tool_name, result)

    def _log_to_db(self, tool_name: str, result: Any):
        """Internal helper to persist events for the visualization layer."""
        try:
            # Extract common fields from result if possible
            event_type = "Analysis"
            target = "General"
            confidence = 1.0
            
            if isinstance(result, dict):
                event_type = result.get("status", result.get("event", "Analysis"))
                # Try to find a target (author, entity, etc.)
                target = result.get("target", result.get("subject", result.get("entity", result.get("claim", "General"))))
                # Try to find confidence (match_likelihood, certainty_quotient, etc.)
                confidence = result.get("certainty_quotient", result.get("match_likelihood", result.get("centrality", 1.0)))
                # Handle "High"/"Low" confidence strings
                if isinstance(confidence, str):
                    confidence = 0.9 if confidence == "High" else 0.4

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO forensic_events (session_id, tool_name, event_type, target, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.session_id, tool_name, event_type, str(target)[:100], float(confidence), json.dumps(result)))
            conn.commit()
            conn.close()
        except Exception as e:
            # We don't want session logic to fail just because logging failed
            pass

    def update_scratchpad(self, key: str, value: Any):
        """Store info in scratchpad."""
        self.scratchpad[key] = value
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to serializable dict."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "history_count": len(self.history),
            "scratchpad": self.scratchpad,
            "metadata": self.metadata
        }

class SessionManager:
    """Manages multiple sessions."""
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        
    def get_session(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create new one."""
        if not session_id or session_id not in self._sessions:
            new_id = session_id or str(uuid.uuid4())
            self._sessions[new_id] = Session(new_id)
            return self._sessions[new_id]
        
        session = self._sessions[session_id]
        session.last_accessed = datetime.now()
        return session

    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())

    def cleanup(self, max_age_hours: int = 24):
        """Remove old sessions."""
        now = datetime.now()
        to_delete = []
        for sid, session in self._sessions.items():
            age = (now - session.last_accessed).total_seconds() / 3600
            if age > max_age_hours:
                to_delete.append(sid)
        
        for sid in to_delete:
            del self._sessions[sid]

# Global session manager instance
_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get global SessionManager singleton."""
    return _manager
