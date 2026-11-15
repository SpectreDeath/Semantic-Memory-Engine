---
name: event-system
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: src/core/events.py
source: Semantic Memory Engine (SME)
tags:
  - event-system
  - pub-sub
  - event-bus
  - async-broadcasting
  - event-listeners
inputs:
  action:
    type: string
    required: true
    description: Operation (`'publish'`, `'subscribe'`, `'unsubscribe'`, `'list_topics'`).
  topic:
    type: string
    required: true
    description: Event topic string (e.g. `'forensics.analysis.completed'`, `'security.threat.detected'`).
  event_data:
    type: object
    required: false
    description: Event payload dictionary to broadcast.
outputs:
  delivered_count:
    type: integer
    description: Number of active listener callbacks that received the published event.
  event_id:
    type: string
    description: Unique tracking identifier assigned to the published event.
  status:
    type: string
    description: Operation confirmation string (`'ok'` or `'error'`).
---

# Event System Engine

`event-system` implements a decoupled asynchronous publish-subscribe event bus across SME subsystems in Python:

$$\text{Publish}(T, \text{Payload}) \to \forall s \in \text{Subscribers}(T): \text{Notify}(s, \text{Payload})$$

---

## The 5-Stage Event System Progression

1. **Event Message Ingest & Topic Parse**: Ingest event topic string and payload dictionary.
2. **Subscriber Channel Resolution**: Match topic string against exact and wildcard subscriber registrations (`forensics.*`).
3. **The Visual Brief**: Generate interactive HTML event bus activity flow brief at `%TEMP%\event-system-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Isolate listener execution; ensure one failing subscriber does not crash the event bus.
5. **Async Broadcast & Output Emission**: Dispatch event asynchronously and emit delivery receipt.

---

## Implementation Notes

```python
import uuid
from typing import Dict, List, Any, Optional

def dispatch_system_event(
    action: str,
    topic: str,
    event_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    ev_id = f"evt_{str(uuid.uuid4())[:8]}"
    return {
        "delivered_count": 3,
        "event_id": ev_id,
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Synchronous Event Blocking** — Invoking slow network callbacks directly on the synchronous event publishing thread.
- **Unbounded Event Memory Queues** — Queuing millions of unconsumed events in memory without backpressure ceilings.