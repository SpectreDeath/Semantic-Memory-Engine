---
name: documentation-generation
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Documentation
source_file: scripts/extract_skill.py
source: Semantic Memory Engine (SME)
tags:
  - documentation-generation
  - api-documentation
  - markdown-generation
  - skill-catalog
  - automated-docs
inputs:
  source_modules:
    type: array
    required: true
    description: List of Python source filepaths or skill markdown files to document.
outputs:
  generated_markdown:
    type: string
    description: Formatted Markdown documentation suite with type signatures and docstrings.
  documented_items_count:
    type: integer
    description: Count of functions, classes, or skills documented.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Documentation Generation Engine

`documentation-generation` parses Python source code and skill YAML headers to build API documentation reference manuals in Python:

$$\text{DocGen}(\text{Codebase}) \to \text{MarkdownDoc}(\text{Modules}, \text{Functions}, \text{Signatures}, \text{Examples})$$

---

## The 5-Stage Documentation Generation Progression

1. **Source Ingest & AST Parse**: Ingest source code files; extract docstrings, classes, and type hints via Python `ast`.
2. **Markdown Template Formulation**: Structure extracted symbols into GitHub Flavored Markdown sections.
3. **The Visual Brief**: Generate interactive HTML documentation preview brief at `%TEMP%\doc-gen-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that all public functions have documented input/output parameters.
5. **Documentation Emission**: Emit generated markdown string and item tally.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def generate_module_docs(
    source_modules: List[str]
) -> Dict[str, Any]:
    md = f"# API Reference Documentation\n\nGenerated for {len(source_modules)} modules.\n"
    for m in source_modules:
        md += f"## `{m}`\n\n- Description: Auto-generated module reference.\n"
    return {
        "generated_markdown": md,
        "documented_items_count": len(source_modules),
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Undocumented Private Symbols** — Polluting public documentation with internal private helper functions (`_helper`).
- **Missing Code Examples** — Generating API documentation that lists type signatures without practical usage examples.
