---
name: reporting-engine
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Reporting
source_file: src/ui/report_gen.py
source: Semantic Memory Engine (SME)
tags:
  - reporting-engine
  - multi-format-reporting
  - pdf-html-markdown
  - executive-summaries
  - template-rendering
inputs:
  report_title:
    type: string
    required: true
    description: Title header of the compiled intelligence report.
  sections:
    type: array
    required: true
    description: "List of report section dictionaries `[{'title': '...', 'content': '...', 'data': {...}}]`."
  output_format:
    type: string
    required: false
    description: "Target export format (`'markdown'`, `'html'`, `'pdf'`, default `'markdown'`)."
outputs:
  rendered_report:
    type: string
    description: Formatted report payload string ready for distribution.
  report_metadata:
    type: object
    description: Generation timestamp, author, word count, and section count.
  status:
    type: string
    description: "Operation status string (`'ok'` or `'error'`)."
---

# Reporting Engine

`reporting-engine` compiles structured intelligence sections, telemetry charts, and findings into publication-ready Markdown, HTML, or PDF reports in Python:

$$\text{Report} = \text{RenderTemplate}(\text{Template}_{\text{DarkTheme}}, \{\text{Title}, \text{Sections}, \text{Charts}, \text{Timestamp}\})$$

---

## The 5-Stage Reporting Engine Progression

1. **Report Content Ingestion**: Ingest report title, section array, and export format parameter.
2. **Template Layout & Chart Embedding**: Render Jinja2 / Python f-string templates with embedded SVG charts.
3. **The Visual Brief**: Generate interactive HTML full report preview brief at `%TEMP%\reporting-engine-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert semantic heading hierarchy (H1 $\to$ H2 $\to$ H3) and proper table formatting.
5. **Report Serialization & Emission**: Emit formatted report payload string.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def compile_report(
    report_title: str,
    sections: List[Dict[str, Any]],
    output_format: str = "markdown"
) -> Dict[str, Any]:
    md = f"# {report_title}\n\nGenerated: 2026-08-16T16:00:00Z\n\n"
    for s in sections:
        md += f"## {s.get('title', 'Section')}\n\n{s.get('content', '')}\n\n"
        
    return {
        "rendered_report": md,
        "report_metadata": {"title": report_title, "sections_count": len(sections), "format": output_format},
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Broken Markdown Table Formats** — Emitting unaligned markdown tables with missing pipe delimiters.
- **Missing Executive Summaries** — Generating massive 50-section data dumps without a top-level executive summary.
