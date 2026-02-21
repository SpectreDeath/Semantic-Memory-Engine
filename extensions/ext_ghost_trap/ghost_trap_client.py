"""
Ghost Trap Client - Persistence Event Detection

Provides integration with Ghost-Trap extension for detecting
persistence events, file system changes, and anomaly patterns.

This module can be used by other extensions (like NUR) to query
Ghost-Trap events.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("lawnmower.ghost_trap")

# Default paths for Ghost-Trap data
DEFAULT_DATA_DIR = os.environ.get("SME_DATA_DIR", "data")
GHOST_TRAP_DIR = os.path.join(DEFAULT_DATA_DIR, "ghost_trap")


class GhostTrapClient:
    """
    Client for querying Ghost-Trap persistence events.
    
    Ghost-Trap monitors the file system for suspicious changes
    that may indicate persistence mechanisms or unauthorized modifications.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or GHOST_TRAP_DIR
        self.events_file = os.path.join(self.data_dir, "events.jsonl")
        self.alerts_file = os.path.join(self.data_dir, "alerts.jsonl")

    def _read_jsonl(self, filepath: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Read entries from a JSONL file."""
        events = []
        if not os.path.exists(filepath):
            return events
            
        try:
            with open(filepath, 'r') as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    try:
                        events.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"GhostTrap: Failed to read {filepath}: {e}")
            
        return events

    def get_recent_events(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get events from the last N hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of events to return
        
        Returns:
            List of event dictionaries
        """
        events = self._read_jsonl(self.events_file, limit)
        
        # Filter by time
        cutoff = datetime.now() - timedelta(hours=hours)
        filtered = []
        
        for event in events:
            try:
                event_time = datetime.fromisoformat(
                    event.get('timestamp', '').replace('Z', '+00:00')
                )
                if event_time.replace(tzinfo=None) >= cutoff:
                    filtered.append(event)
            except (ValueError, TypeError):
                # If timestamp parsing fails, include the event
                filtered.append(event)
                
        return filtered

    def get_alerts(
        self,
        hours: int = 24,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get alerts from Ghost-Trap.
        
        Args:
            hours: Number of hours to look back
            severity: Filter by severity (high, medium, low)
        
        Returns:
            List of alert dictionaries
        """
        alerts = self._read_jsonl(self.alerts_file, 100)
        
        # Filter by time
        cutoff = datetime.now() - timedelta(hours=hours)
        filtered = []
        
        for alert in alerts:
            # Apply severity filter
            if severity and alert.get('severity') != severity:
                continue
                
            # Apply time filter
            try:
                alert_time = datetime.fromisoformat(
                    alert.get('timestamp', '').replace('Z', '+00:00')
                )
                if alert_time.replace(tzinfo=None) >= cutoff:
                    filtered.append(alert)
            except (ValueError, TypeError):
                filtered.append(alert)
                
        return filtered

    def get_persistence_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get events specifically flagged as persistence mechanisms.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of persistence-related events
        """
        events = self.get_recent_events(hours)
        
        persistence_keywords = [
            'persistence', 'autorun', 'startup', 'registry',
            'scheduled_task', 'service', 'boot', 'launch_agent'
        ]
        
        return [
            e for e in events
            if any(kw in e.get('event_type', '').lower() for kw in persistence_keywords)
            or any(kw in e.get('description', '').lower() for kw in persistence_keywords)
        ]

    def check_path(self, path: str) -> Dict[str, Any]:
        """
        Check if a specific path has been flagged by Ghost-Trap.
        
        Args:
            path: File or directory path to check
        
        Returns:
            Dict with 'flagged' boolean and event details if flagged
        """
        events = self._read_jsonl(self.events_file, limit=1000)
        
        # Normalize path for comparison
        path = os.path.normpath(path).lower()
        
        for event in events:
            event_path = os.path.normpath(
                event.get('path', event.get('target', ''))
            ).lower()
            
            if path in event_path or event_path in path:
                return {
                    "flagged": True,
                    "event": event
                }
                
        return {"flagged": False}

    def get_status(self) -> Dict[str, Any]:
        """Get Ghost-Trap status."""
        events = self._read_jsonl(self.events_file, limit=10)
        alerts = self._read_jsonl(self.alerts_file, limit=10)
        
        return {
            "ghost_trap": "active",
            "data_dir": self.data_dir,
            "recent_events_count": len(self._read_jsonl(self.events_file, 1000)),
            "recent_alerts_count": len(self._read_jsonl(self.alerts_file, 1000)),
            "last_event": events[0] if events else None,
            "last_alert": alerts[0] if alerts else None
        }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------
_client: Optional[GhostTrapClient] = None


def get_ghost_trap(data_dir: Optional[str] = None) -> GhostTrapClient:
    """Get the GhostTrapClient singleton."""
    global _client
    if _client is None:
        _client = GhostTrapClient(data_dir)
    return _client
