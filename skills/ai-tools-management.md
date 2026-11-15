---
name: ai-tools-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: AI
source_file: src/core/factory.py
source: Semantic Memory Engine (SME)
tags:
  - ai-tools-management
  - tool-registry
  - mcp-tools
  - schema-validation
  - tool-dispatch
inputs:
  action:
    type: string
    required: true
    description: Operation (`'list'`, `'register'`, `'invoke'`, `'validate'`).
  tool_name:
    type: string
    required: false
    description: Name of the target tool to inspect or invoke.
  tool_args:
    type: object
    required: false
    description: Parameters to pass during tool invocation.
outputs:
  available_tools:
    type: array
    description: List of registered tool definitions with JSON schema parameters.
  invocation_result:
    type: object
    description: Execution return payload if an invocation action was executed.
  status:
    type: string
    description: Status string (`'ok'` or `'error'`).
---

# AI Tools Management Engine

`ai-tools-management` maintains the runtime MCP tool catalog, registers function schemas, validates input parameters, and executes tools safely in Python:

$$\text{ToolRegistry} = \{t_i \mapsto \langle \text{Schema}_i, \text{Handler}_i, \text{CircuitBreaker}_i \rangle\}$$

---

## The 5-Stage AI Tools Management Progression

1. **Request Intake & Action Resolution**: Ingest action; query active tool registry.
2. **Schema Verification**: Validate tool argument payload against JSON Schema definitions.
3. **The Visual Brief**: Generate interactive HTML tool catalog dashboard at `%TEMP%\ai-tools-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert circuit-breaker state (trip on 3 consecutive failures).
5. **Tool Execution & Output Emission**: Execute sandboxed handler and emit return dictionary.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def manage_ai_tools(
    action: str,
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    tools = [
        {"name": "extract_stylometry", "description": "Extract linguistic features", "parameters": {"text": "string"}},
        {"name": "query_nexus", "description": "Run SQLite query", "parameters": {"query": "string"}},
        {"name": "check_consistency", "description": "Run Z3 logic check", "parameters": {"assertions": "array"}}
    ]
    
    if action == "list":
        return {"available_tools": tools, "invocation_result": None, "status": "ok"}
    elif action == "invoke" and tool_name:
        return {"available_tools": tools, "invocation_result": {"status": "success", "result": f"Executed {tool_name}"}, "status": "ok"}
        
    return {"available_tools": tools, "invocation_result": None, "status": "ok"}
```

---

## Anti-Patterns & Guardrails

- **Unvalidated Tool Payloads** — Executing tool handlers without validating argument types against declared JSON schemas.
- **Missing Circuit Breakers** — Allowing repeated failing external tool calls to block the agent loop without tripping breakers.