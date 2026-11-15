---
name: config-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: src/core/config.py
source: Semantic Memory Engine (SME)
tags:
  - config-management
  - environment-variables
  - yaml-configuration
  - settings-validation
  - pydantic-settings
inputs:
  action:
    type: string
    required: true
    description: Operation (`'get'`, `'set'`, `'reload'`, `'dump'`).
  key_path:
    type: string
    required: false
    description: Dot-separated configuration key path (e.g. `'gateway.port'`, `'storage.wal_mode'`).
  value:
    type: object
    required: false
    description: Value to set for the targeted configuration key.
outputs:
  config_value:
    type: object
    description: Retrieved configuration value or dumped settings tree.
  environment:
    type: string
    description: Active environment profile (`'development'`, `'production'`, `'test'`).
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Config Management Engine

`config-management` manages cascading configuration files (`config.yaml`, `.env`, environment variables) with Pydantic type validation in Python:

$$\text{Config} = \text{Merge}(\text{Defaults}, \text{ConfigYAML}, \text{EnvVars}, \text{CLIFlags})$$

---

## The 5-Stage Config Management Progression

1. **Configuration Intake & Source Cascade**: Ingest config files, `.env` variables, and runtime overrides.
2. **Schema & Type Coercion**: Validate all fields using Pydantic `BaseSettings`.
3. **The Visual Brief**: Generate interactive HTML configuration hierarchy brief at `%TEMP%\config-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Mask sensitive passwords, tokens, and private keys before dumping configuration state.
5. **Settings Dispatch & Output Emission**: Emit resolved configuration tree.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def manage_system_config(
    action: str,
    key_path: Optional[str] = None,
    value: Optional[Any] = None
) -> Dict[str, Any]:
    cfg = {
        "gateway": {"host": "0.0.0.0", "port": 8000, "mcp_enabled": True},
        "storage": {"wal_mode": True, "vault_dir": "skills/gold_standard"}
    }
    return {
        "config_value": cfg.get(key_path, cfg) if key_path else cfg,
        "environment": "development",
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Plaintext Secret Exposure** — Dumping un-masked database passwords or API keys in configuration debug output.
- **Unvalidated Runtime Overrides** — Mutating runtime settings without type-checking against Pydantic models.