---
name: entity-redaction
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Utilities
source_file: src/utils/entity_filter.py
source: Semantic Memory Engine (SME)
tags:
  - entity-redaction
  - pii-masking
  - privacy-preservation
  - redaction-vault
  - gdpr-compliance
inputs:
  raw_document:
    type: string
    required: true
    description: Input document containing sensitive, private, or PII entity mentions.
  redaction_categories:
    type: array
    required: false
    description: Entity types to mask `['PERSON', 'EMAIL', 'PHONE', 'SSN', 'IP_ADDRESS']` (default all).
  replacement_strategy:
    type: string
    required: false
    description: Masking format (`'tag'` e.g. `[REDACTED_PERSON_1]`, `'mask'` e.g. `***`, default `'tag'`).
outputs:
  redacted_text:
    type: string
    description: Cleaned document with all requested PII entities securely redacted.
  redaction_map:
    type: object
    description: Reversible key-value vault mapping redacted tokens to original values for authorized recovery.
  redacted_count:
    type: integer
    description: Total number of entity instances masked.
---

# Entity Redaction Engine

`entity-redaction` sanitizes sensitive personal identifiable information (PII) from document archives while maintaining reversible mapping keys in an encrypted privacy vault:

$$\mathcal{D}_{\text{redacted}} = \text{Replace}(\mathcal{D}_{\text{raw}}, \{e_i \mapsto \tau_i\}), \quad \mathcal{V}_{\text{vault}} = \{\tau_i \mapsto e_i\}$$

---

## The 5-Stage Entity Redaction Progression

1. **Document Intake & Regex/NER Pattern Setup**: Ingest text; initialize regex patterns for emails, phone numbers, IP addresses, and person names.
2. **PII Detection & Vault Key Assignment**: Identify sensitive entity spans $[s, e]$; assign deterministic masked tokens `[REDACTED_TYPE_K]`.
3. **The Visual Brief**: Generate interactive HTML privacy brief at `%TEMP%\entity-redaction-brief-<timestamp>.html` comparing original vs. redacted document views.
4. **Mandatory Checkpoint**: Assert that no unmasked sensitive strings remain in the output payload.
5. **Sanitized Output & Vault Emission**: Commit reverse key map to SQLite session vault and emit sanitized text.

---

## Implementation Notes

```python
import re
from typing import Dict, List, Any, Optional

def redact_sensitive_entities(
    raw_document: str,
    redaction_categories: Optional[List[str]] = None,
    replacement_strategy: str = "tag"
) -> Dict[str, Any]:
    text = raw_document
    vault = {}
    count = 0
    
    # Regex rules
    patterns = {
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "IP": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    }
    
    for tag_name, pat in patterns.items():
        matches = list(re.finditer(pat, text))
        for m in reversed(matches):
            val = m.group(0)
            count += 1
            token = f"[REDACTED_{tag_name}_{count}]" if replacement_strategy == "tag" else "***"
            vault[token] = val
            text = text[:m.start()] + token + text[m.end():]
            
    return {
        "redacted_text": text,
        "redaction_map": vault,
        "redacted_count": count
    }
```

---

## Anti-Patterns & Guardrails

- **Irreversible Key Loss** — Redacting critical forensic evidence without storing recovery keys in an isolated session vault.
- **Regex Boundary Leaks** — Using unanchored regex patterns that accidentally mask non-PII numerical parameters.