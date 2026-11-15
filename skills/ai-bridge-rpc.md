---
name: ai-bridge-rpc
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Integration
source_file: gateway/mcp_server.py
source: Semantic Memory Engine (SME)
tags:
  - ai-bridge-rpc
  - mcp-rpc-protocol
  - json-rpc-20
  - session-bridge
  - low-latency-ipc
inputs:
  rpc_method:
    type: string
    required: true
    description: Target JSON-RPC 2.0 method name (e.g. `'sme/query_nexus'`, `'sme/transduce_sensor'`).
  params:
    type: object
    required: false
    description: Parameter dictionary for the remote method invocation.
  session_id:
    type: string
    required: false
    description: Optional active session token for stateful context persistence.
outputs:
  rpc_result:
    type: object
    description: Return payload from the remote RPC bridge method.
  rpc_status:
    type: string
    description: RPC status (`'ok'`, `'error'`, `'timeout'`).
  latency_ms:
    type: number
    description: Round-trip execution latency in milliseconds.
---

# AI Bridge RPC Engine

`ai-bridge-rpc` provides the core JSON-RPC 2.0 communication bridge connecting the SME Lawnmower Man MCP Gateway to external agents and tool runners in Python:

$$\text{Request} = \langle \text{id}, \text{method}, \text{params}, \text{jsonrpc: "2.0"} \rangle \xrightarrow{\text{IPC}} \text{BridgeHandler}() \to \text{Response}$$

---

## The 5-Stage AI Bridge RPC Progression

1. **RPC Message Intake & Framing**: Ingest JSON-RPC envelope; assert valid `jsonrpc`, `method`, and `id` keys.
2. **Session Context Binding**: Attach active SQLite WAL session scratchpad and security token.
3. **The Visual Brief**: Generate interactive HTML RPC message sequence diagram at `%TEMP%\ai-bridge-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Validate parameter schema and authenticate caller permissions.
5. **Method Dispatch & Response Emission**: Route call to internal SME engine and emit standard JSON-RPC response.

---

## Implementation Notes

```python
import time
from typing import Dict, List, Any, Optional

def dispatch_ai_bridge_rpc(
    rpc_method: str,
    params: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    # Mock JSON-RPC dispatch
    result_data = {"method": rpc_method, "executed": True, "session": session_id or "default"}
    elapsed = (time.perf_counter() - t0) * 1000.0
    
    return {
        "rpc_result": result_data,
        "rpc_status": "ok",
        "latency_ms": round(elapsed + 2.5, 2)
    }
```

---

## Anti-Patterns & Guardrails

- **Malformed JSON-RPC Envelopes** — Sending raw payloads without standard `jsonrpc: "2.0"` headers and error objects.
- **Unbounded RPC Blocking** — Allowing synchronous RPC calls to hang without client-side timeout deadlines ($T \le 30\text{s}$).