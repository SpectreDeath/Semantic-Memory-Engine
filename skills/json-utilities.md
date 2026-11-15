---
name: json-utilities
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Utilities
source_file: src/utils/json_utils.py
source: Semantic Memory Engine (SME)
tags:
  - json-utilities
  - json-repair
  - jsonl-streaming
  - fast-serialization
  - schema-validation
inputs:
  action:
    type: string
    required: true
    description: Operation (`'parse'`, `'repair'`, `'stream_jsonl'`, `'canonical_dumps'`).
  raw_json_str:
    type: string
    required: false
    description: Potentially malformed or un-escaped JSON string to parse/repair.
outputs:
  parsed_data:
    type: object
    description: Clean parsed JSON object or array.
  was_repaired:
    type: boolean
    description: True if repair heuristics fixed syntax errors (trailing commas, single quotes).
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# JSON Utilities Engine

`json-utilities` provides robust JSON parsing, automatic repair for LLM-generated malformed JSON, and deterministic canonical sorting in Python:

$$\text{CanonicalJSON}(O) = \text{dumps}(O, \text{sort\_keys}=\text{True}, \text{separators}=(',', ':'))$$

---

## The 5-Stage JSON Utilities Progression

1. **String Intake & Syntax Probing**: Ingest raw JSON string; test standard `json.loads`.
2. **Automatic Syntax Repair**: If parsing fails, strip trailing commas, fix unescaped quotes, and balance closing braces.
3. **The Visual Brief**: Generate interactive HTML JSON syntax tree brief at `%TEMP%\json-utils-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that repaired string deserializes into a valid Python dictionary or list.
5. **Output Emission**: Emit parsed dictionary and repair flag.

---

## Implementation Notes

```python
import json
import re
from typing import Dict, List, Any, Optional

def process_json_utility(
    action: str,
    raw_json_str: Optional[str] = None
) -> Dict[str, Any]:
    if not raw_json_str:
        return {"parsed_data": {}, "was_repaired": False, "status": "ok"}
        
    try:
        data = json.loads(raw_json_str)
        return {"parsed_data": data, "was_repaired": False, "status": "ok"}
    except Exception:
        # Repair trailing commas and single quotes
        cleaned = re.sub(r",\s*([\]}])", r"\1", raw_json_str).replace("'", '"')
        data = json.loads(cleaned)
        return {"parsed_data": data, "was_repaired": True, "status": "ok"}
```

---

## Anti-Patterns & Guardrails

- **Crashing on Minor Syntax Flaws** — Rejecting LLM JSON outputs outright due to a single trailing comma.
- **Un-Deterministic Serialization** — Generating hash keys from JSON strings without sorting dictionary keys.