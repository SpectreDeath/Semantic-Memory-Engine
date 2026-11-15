---
name: factory-pattern
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: src/core/factory.py
source: Semantic Memory Engine (SME)
tags:
  - factory-pattern
  - dynamic-instantiation
  - object-creation
  - component-builder
  - polymorphic-dispatch
inputs:
  component_type:
    type: string
    required: true
    description: Target component class category (e.g. `'analyzer'`, `'storage_engine'`, `'llm_provider'`).
  config_params:
    type: object
    required: false
    description: Constructor arguments and configuration overrides.
outputs:
  instance_metadata:
    type: object
    description: Instantiated component class name, capabilities, and configuration signature.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Factory Pattern Engine

`factory-pattern` provides polymorphic instantiation for analyzers, storage backends, and connectors in Python:

$$\text{CreateComponent}(\text{Type}, \text{Config}) \to \text{Registry}[\text{Type}](\text{Config})$$

---

## The 5-Stage Factory Pattern Progression

1. **Component Request Intake**: Ingest requested component type identifier and parameter dictionary.
2. **Registry Lookup & Dependency Injection**: Resolve target class in component registry; inject required services.
3. **The Visual Brief**: Generate interactive HTML component factory registry brief at `%TEMP%\factory-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that instantiated component implements the required abstract base interface.
5. **Instance Construction & Metadata Emission**: Instantiate object and emit configuration summary.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def create_component_instance(
    component_type: str,
    config_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "instance_metadata": {
            "component_type": component_type,
            "class_name": f"{component_type.title().replace('_', '')}Engine",
            "initialized": True
        },
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Hard-Coded If-Else Instantiation** — Using fragile giant switch-case blocks instead of a dynamic registration dictionary.
- **Unvalidated Configuration Injection** — Passing untyped dictionaries to constructors without Pydantic validation.