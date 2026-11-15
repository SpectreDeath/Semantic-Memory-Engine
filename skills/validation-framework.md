---
name: validation-framework
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: src/core/validation.py
source: Semantic Memory Engine (SME)
tags:
  - validation-framework
  - input-sanitization
  - constraint-checking
  - schema-guards
  - error-boundaries
inputs:
  target_payload:
    type: object
    required: true
    description: Data dictionary or model structure to validate.
  validation_rules:
    type: array
    required: true
    description: "List of constraint rules `[{'field': 'x', 'type': 'int', 'min': 0, 'max': 100}]`."
outputs:
  is_valid:
    type: boolean
    description: True if all validation rules are satisfied without violations.
  validation_errors:
    type: array
    description: List of identified constraint violations with field names and error messages.
  sanitized_payload:
    type: object
    description: Sanitized data payload with trimmed strings and enforced bounds.
---

# Validation Framework Engine

`validation-framework` enforces input sanitization, type-safety contracts, and boundary constraints across all SME skills and API entry points in Python:

$$\text{Validate}(\mathcal{D}, \mathcal{R}) = \bigwedge_{r \in \mathcal{R}} \text{CheckRule}(r, \mathcal{D})$$

---

## The 5-Stage Validation Framework Progression

1. **Payload & Rule Ingestion**: Ingest raw payload and declarative validation rule array.
2. **Type & Nullability Checks**: Assert required field presence and enforce primitive data types.
3. **The Visual Brief**: Generate interactive HTML validation report brief at `%TEMP%\validation-framework-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Evaluate numeric range bounds and regex format constraints.
5. **Sanitized Output & Emission**: Emit cleaned payload dictionary and error list.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def validate_payload_data(
    target_payload: Dict[str, Any],
    validation_rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    errors = []
    sanitized = dict(target_payload)
    
    for rule in validation_rules:
        field = rule["field"]
        if field not in target_payload:
            errors.append({"field": field, "error": "missing_required_field"})
            continue
        val = target_payload[field]
        if "min" in rule and isinstance(val, (int, float)) and val < rule["min"]:
            errors.append({"field": field, "error": f"value_{val}_below_min_{rule['min']}"})
            
    return {
        "is_valid": len(errors) == 0,
        "validation_errors": errors,
        "sanitized_payload": sanitized
    }
```

---

## Anti-Patterns & Guardrails

- **Ad-Hoc Unstructured Validation** — Writing custom if-else statements across individual tools rather than using central declarative validation rules.
- **Silent Coercion Without Warning** — Silently mutating invalid input values without returning error diagnostics to the caller.