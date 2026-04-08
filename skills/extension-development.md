---
Domain: Plugin Development
Version: 1.0.0
Complexity: Intermediate
Type: development
Category: extensibility
name: Extension Development
Source: SME v3.0.0
Source_File: extensions/
---

# Extension Development Guide

## Purpose
Create hot-swappable plugin extensions for the SME (Semantic Memory Engine) Gateway that expose tools to AI agents via the MCP protocol.

## Description
SME v3.0.0 supports a modular plugin architecture. Extensions are self-contained packages that register tools, handle lifecycle events, and integrate with the Nexus database layer through a standard contract.

## Architecture

```
extensions/
└── ext_my_plugin/
    ├── manifest.json    # Extension metadata
    ├── plugin.py        # Main entry point
    └── __init__.py      # Package init
```

## Workflow

### Step 1: Create Extension Directory
```bash
mkdir extensions/ext_my_plugin
cd extensions/ext_my_plugin
```

### Step 2: Create manifest.json
```json
{
  "plugin_id": "ext_my_plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "Description of what this plugin does",
  "entry_point": "plugin.py",
  "author": "Your Name",
  "category": "analysis",
  "permissions": {
    "network_access": false,
    "filesystem_read": true,
    "filesystem_write": false,
    "subprocess": false
  }
}
```

### Step 3: Implement plugin.py
```python
from __future__ import annotations

import json
import logging
from typing import Any
from collections.abc import Callable

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.MyPlugin")


class MyPlugin(BasePlugin):
    """My custom extension plugin."""

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)

    async def on_startup(self) -> None:
        """Initialize plugin on load."""
        logger.info(f"[{self.plugin_id}] Plugin initialized")

    async def on_shutdown(self) -> None:
        """Clean up on unload."""
        logger.info(f"[{self.plugin_id}] Plugin shutdown")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process incoming data."""
        return {"status": "processed", "length": len(raw_data)}

    def get_tools(self) -> list[Callable[..., Any]]:
        """Expose tools to AI agents."""
        return [self.my_tool]

    async def my_tool(self, text: str) -> str:
        """My custom tool function."""
        return json.dumps({"result": f"Processed: {text}"}, indent=2)


def register_extension(manifest: dict[str, Any], nexus_api: Any) -> MyPlugin:
    """Required entry point for extension loading."""
    return MyPlugin(manifest, nexus_api)
```

### Step 4: Create __init__.py
```python
from .plugin import MyPlugin, register_extension

__all__ = ['MyPlugin', 'register_extension']
```

## Examples

### Using the DAL (Data Access Layer)
```python
async def on_startup(self) -> None:
    """Initialize custom database table."""
    self.dal.create_table("my_table", {
        "id": "PRIMARY_KEY",
        "data": "TEXT",
        "score": "FLOAT",
        "timestamp": "DATETIME"
    })

async def store_result(self, data: str, score: float) -> None:
    """Store analysis result."""
    from datetime import datetime
    self.dal.insert_record("my_table", {
        "data": data,
        "score": score,
        "timestamp": datetime.now().isoformat()
    })
```

### Event Handling
```python
async def on_event(self, event_id: str, payload: dict[str, Any]) -> None:
    """Handle system-wide events."""
    if event_id == 'data_ingested':
        logger.info(f"New data ingested: {payload.get('source')}")
```

### Async Tools
```python
async def async_analysis(self, text: str) -> str:
    """Async tool for heavy processing."""
    import asyncio
    await asyncio.sleep(0.1)  # Simulate work
    return json.dumps({"analyzed": True})
```

## Security Constraints

### Forbidden Imports
Extensions cannot import:
- `ctypes`, `subprocess`, `shutil` (system escape)
- `socket`, `aiohttp` (data exfiltration)
- `multiprocessing` (process spawning)

### Path Validation
- Entry points must be within plugin directory
- No symlink traversal allowed
- Extensions directory must be within project root

## Implementation Notes
- Always inherit from `BasePlugin` at `src.core.plugin_base`
- Use `logger` instead of `print()` for all output
- Return JSON strings from tool functions
- Manifest must include `plugin_id`, `name`, `version`, `description`
- Version must follow semver format: `X.Y.Z`

## Related Skills
- authentication.md - Secure plugin access
- error-handling.md - Plugin error patterns
- data-management.md - Using the DAL