---
name: logging-system
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: extensions/ext_logging/plugin.py
source: Semantic Memory Engine (SME)
tags:
  - logging-system
  - structured-logging
  - log-rotation
  - contextual-tracing
  - correlation-id
inputs:
  action:
    type: string
    required: true
    description: Operation (`'log'`, `'query_logs'`, `'rotate'`, `'set_level'`).
  level:
    type: string
    required: false
    description: Log severity (`'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'`, default `'INFO'`).
  message:
    type: string
    required: false
    description: Log message string.
  context:
    type: object
    required: false
    description: Structured context dictionary (correlation ID, agent ID, session ID).
outputs:
  logged_entry:
    type: object
    description: Formatted JSON structured log entry with timestamp and correlation metadata.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Logging System Engine

`logging-system` manages structured JSON telemetry, log rotation, and cross-subsystem correlation ID tracking in Python:

$$\text{LogRecord} = \langle t_{\text{ISO}}, \text{Level}, \text{CorrelationID}, \text{AgentID}, \text{Message}, \text{Context} \rangle$$

---

## The 5-Stage Logging System Progression

1. **Log Request Ingest & Correlation Attachment**: Ingest message, severity level, and attach active `correlation_id`.
2. **JSON Serialization & Formatting**: Format record into single-line structured JSON.
3. **The Visual Brief**: Generate interactive HTML log stream waterfall brief at `%TEMP%\logging-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that log file rotation triggers at 50MB limits to prevent disk exhaustion.
5. **Log Emission**: Write log line to file / stdout and emit confirmation record.

---

## Implementation Notes

```python
import time
import uuid
from typing import Dict, List, Any, Optional

def dispatch_log_entry(
    action: str,
    level: str = "INFO",
    message: Optional[str] = "System event",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    entry = {
        "timestamp": "2026-08-16T16:00:00Z",
        "level": level.upper(),
        "correlation_id": context.get("correlation_id", str(uuid.uuid4())[:8]) if context else str(uuid.uuid4())[:8],
        "message": message,
        "context": context or {}
    }
    return {
        "logged_entry": entry,
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Unstructured Plaintext Logs** — Emitting arbitrary unstructured text strings that cannot be indexed or parsed by log analytics tools.
- **Unbounded Single-File Logs** — Writing logs to a single ever-growing file without automated size rotation.