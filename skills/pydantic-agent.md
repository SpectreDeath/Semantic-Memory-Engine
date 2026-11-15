---
name: pydantic-agent
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: AI
source_file: src/ai/pydantic_ai_agent.py
source: Semantic Memory Engine (SME)
tags:
  - pydantic-agent
  - structured-outputs
  - schema-validation
  - type-safe-agents
  - pydantic-v2
inputs:
  prompt:
    type: string
    required: true
    description: Input prompt or task instruction for the Pydantic agent.
  output_schema_name:
    type: string
    required: true
    description: Target Pydantic model name (e.g. `'ForensicReportSchema'`, `'AttributionResultSchema'`).
outputs:
  structured_data:
    type: object
    description: Validated JSON object strictly conforming to the target Pydantic schema.
  validation_passed:
    type: boolean
    description: True if schema validation passed without field errors.
  raw_response:
    type: string
    description: Raw unparsed LLM completion text before validation.
---

# Pydantic Agent Engine

`pydantic-agent` enforces strict type-safe structured generation by constraining LLM completions with Pydantic V2 schemas and automatic retry loops in Python:

$$\text{Validate}(\mathbf{y}) = \begin{cases} \text{Schema}(\mathbf{y}) & \text{if Valid} \\ \text{PromptRetry}(\text{ErrorTrace}) & \text{if Invalid} \end{cases}$$

---

## The 5-Stage Pydantic Agent Progression

1. **Prompt Ingest & Schema Compilation**: Ingest task prompt and resolve target Pydantic model class.
2. **JSON-Mode LLM Completion**: Dispatch completion request with embedded JSON schema instructions.
3. **The Visual Brief**: Generate interactive HTML schema validation brief at `%TEMP%\pydantic-agent-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Validate response against schema; if validation fails, execute up to 2 corrective re-prompts.
5. **Structured Emission**: Emit validated dictionary conforming to the Pydantic schema.

---

## Implementation Notes

```python
import json
from typing import Dict, List, Any

def run_pydantic_agent(
    prompt: str,
    output_schema_name: str
) -> Dict[str, Any]:
    # Mock schema validation
    mock_data = {
        "title": "Forensic Summary",
        "confidence": 0.94,
        "findings": ["Distinctive Yule K value", "Consistent burstiness pattern"],
        "schema": output_schema_name
    }
    return {
        "structured_data": mock_data,
        "validation_passed": True,
        "raw_response": json.dumps(mock_data)
    }
```

---

## Anti-Patterns & Guardrails

- **Silent Schema Truncation** — Returning partially parsed JSON dictionaries when required fields fail validation.
- **Unbounded Correction Loops** — Retrying failed schema generations indefinitely without a maximum retry cap ($R \le 2$).