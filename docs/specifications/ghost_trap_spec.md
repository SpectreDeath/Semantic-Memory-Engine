# Ghost Trap Extension Specification

## Overview

Ghost Trap monitors file system for persistence mechanisms and suspicious changes that may indicate unauthorized modifications or malware behavior.

## Purpose

Detect and alert on:
- Autorun entries
- Scheduled tasks
- Registry modifications
- Service installations
- Boot persistence
- Launch agents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ghost Trap Extension                      │
├─────────────────────────────────────────────────────────────┤
│  File System Watcher                                         │
│  ├── inotify (Linux)                                        │
│  └── FSEvents (macOS) / ReadDirectoryChanges (Windows)     │
├─────────────────────────────────────────────────────────────┤
│  Event Processor                                            │
│  ├── Pattern Matcher                                        │
│  ├── Signature Library                                      │
│  └── Risk Assessor                                          │
├─────────────────────────────────────────────────────────────┤
│  Output                                                     │
│  ├── events.jsonl (all events)                             │
│  └── alerts.jsonl (filtered high-risk)                      │
└─────────────────────────────────────────────────────────────┘
```

## Data Schema

### Event
```json
{
  "timestamp": "2026-02-21T10:30:00Z",
  "event_type": "file_create|file_modify|file_delete|registry_change|...",
  "path": "/path/to/file",
  "risk_level": "low|medium|high|critical",
  "description": "Human-readable description",
  "metadata": {
    "process": "explorer.exe",
    "user": "SYSTEM",
    "hash": "sha256..."
  }
}
```

### Alert
```json
{
  "timestamp": "2026-02-21T10:30:00Z",
  "severity": "high",
  "event_type": "persistence_suspected",
  "path": "/path/to/file",
  "recommendation": "Investigate this file for malware",
  "related_events": ["event_id_1", "event_id_2"]
}
```

## Patterns Detected

| Pattern | Description | Risk |
|---------|-------------|------|
| Autorun | Files in startup folders | High |
| Scheduled Task | New scheduled tasks | Medium |
| Registry | Changes to Run/RunOnce keys | Critical |
| Service | New Windows service installation | Critical |
| Boot | Files in boot directories | High |
| LaunchAgent | macOS launch agents | Medium |

## API Integration

```python
from extensions.ext_ghost_trap.ghost_trap_client import get_ghost_trap

# Get recent persistence events
gt = get_ghost_trap()
events = gt.get_persistence_events(hours=24)

# Check specific path
result = gt.check_path("/path/to/check")
if result["flagged"]:
    print("Path flagged by Ghost Trap!")
```

## Configuration

Environment variables:
- `SME_GHOST_TRAP_DATA_DIR` - Data directory (default: `data/ghost_trap`)
- `SME_GHOST_TRAP_LOG_LEVEL` - Logging level (default: INFO)

## Integration with Other Extensions

### NUR (Nuclear Usage Reporter)
- NUR can query Ghost Trap for persistence events
- Correlate usage anomalies with file system changes

### Epistemic Gatekeeper
- Use Ghost Trap data for trust scoring
- Flag files with persistence mechanisms as suspicious

## Testing

```bash
# Run Ghost Trap tests
pytest tests/test_ghost_trap.py -v
```
