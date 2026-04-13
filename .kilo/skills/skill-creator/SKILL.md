---
name: skill-creator
description: "Create new SME skills and extensions. Triggers: 'create skill', 'new extension', 'add capability', 'build plugin'. NOT for: modifying existing skills (use skill-analyzer), simple file creation."
---

# Skill Creator

Create new SME extension skills and plugins.

## When to Use This Skill

Use this skill when:
- Creating new extension capabilities
- Adding new AI tools
- Building specialized analyzers
- Implementing new data processors

Do NOT use this skill when:
- Modifying existing (use skill-analyzer)
- Simple file operations
- Basic queries

## SME Extension Architecture

```
extensions/
  ext_<name>/
    manifest.json      # Metadata
    plugin.py         # Main logic
    optional:
      __init__.py
      config.py
      utils.py
      tests/
```

## Required Files

### manifest.json
```json
{
  "plugin_id": "ext_<name>",
  "name": "Human Readable Name",
  "version": "1.0.0",
  "description": "What it does",
  "author": "SME",
  "dependencies": ["package_name"]
}
```

### plugin.py Structure
```python
from src.core.plugin_base import BasePlugin

class ExtensionNameExtension(BasePlugin):
    def __init__(self, manifest: dict, nexus_api: Any):
        super().__init__(manifest, nexus_api)

    async def on_startup(self):
        # Initialize DB tables, etc.
        pass

    async def on_ingestion(self, raw_data: str, metadata: dict) -> dict:
        # Process incoming data
        pass

    def get_tools(self) -> list:
        # Expose AI tools
        return [self.tool_name]

    async def tool_name(self, param: str) -> str:
        # Tool implementation
        pass

def register_extension(manifest: dict, nexus_api: Any):
    return ExtensionNameExtension(manifest, nexus_api)
```

## Input Format

```yaml
skill_request:
  name: string           # Extension name
  description: string    # What it does
  tools: array          # List of tool names
  dependencies: array   # Required packages
  tables: array         # Database tables needed
```

## Common Patterns

### Data Processing Extension
```python
async def on_ingestion(self, raw_data: str, metadata: dict) -> dict:
    # Parse and enrich data
    return {"status": "processed", "enrichments": [...]}
```

### Analysis Extension
```python
async def analyze(self, data: str) -> str:
    # Analysis logic
    return json.dumps(results)

def get_tools(self):
    return [self.analyze]
```

### API Integration Extension
```python
async def fetch_external(self, endpoint: str) -> str:
    # External API call
    pass
```

## Best Practices

1. **Single responsibility** - One extension = one main capability
2. **Error handling** - Always return JSON, never raise unhandled
3. **Events** - Publish events for downstream processing
4. **Config** - Store config in manifest.json
5. **Tests** - Add tests/ directory

## Example: Financial Analysis Extension

```yaml
skill_request:
  name: transaction_analyzer
  description: "Analyze transaction patterns"
  tools: ["detect_anomalies", "calculate_risk", "summarize_flows"]
  dependencies: ["pandas", "numpy"]
  tables: ["transactions", "risk_scores"]
```

Creates `extensions/ext_transaction_analyzer/` with complete structure.