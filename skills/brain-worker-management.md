---
name: brain-worker-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: AI
source_file: src/ai/brain_worker.py
source: Semantic Memory Engine (SME)
tags:
  - brain-worker-management
  - task-workers
  - asynchronous-agents
  - worker-pool
  - job-scheduling
inputs:
  action:
    type: string
    required: true
    description: Operation (`'spawn'`, `'status'`, `'kill'`, `'list'`).
  task_payload:
    type: object
    required: false
    description: Task configuration and instruction prompt for a new background worker.
  worker_id:
    type: string
    required: false
    description: Specific worker ID to inspect or terminate.
outputs:
  active_workers:
    type: array
    description: List of running worker IDs, assigned tasks, and CPU/memory telemetry.
  task_status:
    type: object
    description: Execution state of the targeted worker (`'running'`, `'completed'`, `'failed'`).
  status:
    type: string
    description: Operation confirmation status string (`'ok'` or `'error'`).
---

# Brain Worker Management Engine

`brain-worker-management` manages isolated asynchronous background worker agents in Python:

$$\text{WorkerPool} = \{w_k \mapsto \langle \text{Task}_k, \text{Thread}_k, \text{Status}_k \rangle\}_{k=1}^{W_{\text{max}}}$$

---

## The 5-Stage Brain Worker Management Progression

1. **Task Request Intake & Worker Capacity Check**: Ingest task configuration; assert active workers $< W_{\text{max}}$.
2. **Asynchronous Worker Thread Initialization**: Spawn isolated sub-agent worker thread with sandboxed session context.
3. **The Visual Brief**: Generate interactive HTML worker pool status board at `%TEMP%\brain-worker-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Monitor worker health; enforce heartbeat timeouts to prevent orphaned threads.
5. **Telemetry Aggregation & Output Emission**: Emit active worker inventory and task execution status.

---

## Implementation Notes

```python
import uuid
from typing import Dict, List, Any, Optional

def manage_brain_workers(
    action: str,
    task_payload: Optional[Dict[str, Any]] = None,
    worker_id: Optional[str] = None
) -> Dict[str, Any]:
    active = [
        {"worker_id": "worker_01", "task": "harvester_crawl", "status": "running", "uptime_s": 120},
        {"worker_id": "worker_02", "task": "polars_index", "status": "completed", "uptime_s": 45}
    ]
    
    if action == "spawn" and task_payload:
        new_id = f"worker_{str(uuid.uuid4())[:6]}"
        active.append({"worker_id": new_id, "task": task_payload.get("task", "custom"), "status": "running", "uptime_s": 0})
        return {"active_workers": active, "task_status": {"worker_id": new_id, "status": "running"}, "status": "ok"}
        
    return {"active_workers": active, "task_status": {"worker_id": worker_id or "all", "status": "ok"}, "status": "ok"}
```

---

## Anti-Patterns & Guardrails

- **Thread Pool Exhaustion** — Spawning background workers without concurrency caps, exhausting system RAM/CPU.
- **Silent Worker Deadlocks** — Allowing background threads to stall indefinitely without timeout circuit-breakers.