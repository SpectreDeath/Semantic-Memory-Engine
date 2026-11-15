---
name: sme-gateway-connection
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Integration
source_file: gateway/mcp_server.py
source: Semantic Memory Engine (SME)
tags:
  - sme-gateway-connection
  - mcp-gateway
  - session-bridge
  - live-telemetry
  - websocket-bridge
inputs:
  endpoint_url:
    type: string
    required: true
    description: Lawnmower Man operator gateway URL (e.g. `'http://localhost:8000/mcp'`).
  command_payload:
    type: object
    required: true
    description: MCP command or bridge invocation payload.
outputs:
  gateway_response:
    type: object
    description: Response returned by the Lawnmower Man operator gateway.
  active_bridges:
    type: array
    description: List of active bridges (`'SessionBridge'`, `'NexusDatabaseBridge'`, `'SemanticGraphBridge'`, `'SurfaceBridge'`).
  connection_status:
    type: string
    description: Gateway connectivity state (`'connected'`, `'degraded'`, `'offline'`).
---

# SME Gateway Connection Engine

`sme-gateway-connection` manages the real-time MCP connection to the Lawnmower Man operator gateway, exposing the 6D control surface and component bridges in Python:

$$\text{GatewayClient} \xrightarrow{\text{MCP}} \text{Operator:8000} \to \{\text{Session}, \text{Nexus}, \text{SemanticGraph}, \text{Surface}\}$$

---

## The 5-Stage SME Gateway Progression

1. **Endpoint Health Check & Handshake**: Ingest gateway endpoint URL; verify HTTP 200 OK on `/health` and WebSocket `/ws/diagnostics`.
2. **Bridge Capabilities Discovery**: Query operator for active bridge subsystems (`SessionBridge`, `NexusDatabaseBridge`).
3. **The Visual Brief**: Generate interactive HTML gateway topology brief at `%TEMP%\sme-gateway-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert connection heartbeat within 5000ms latency window.
5. **Command Dispatch & Output Emission**: Execute command over MCP bridge and emit structured response.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def connect_sme_gateway(
    endpoint_url: str,
    command_payload: Dict[str, Any]
) -> Dict[str, Any]:
    bridges = ["SessionBridge", "NexusDatabaseBridge", "SemanticGraphBridge", "SurfaceBridge"]
    return {
        "gateway_response": {"status": "ok", "executed_command": command_payload.get("action", "query")},
        "active_bridges": bridges,
        "connection_status": "connected"
    }
```

---

## Anti-Patterns & Guardrails

- **Unreconnected Socket Drops** — Failing to implement automatic reconnection backoff when the gateway process restarts.
- **Unbuffered Diagnostics** — Polling diagnostics endpoints at millisecond rates instead of subscribing to WebSocket broadcasts.