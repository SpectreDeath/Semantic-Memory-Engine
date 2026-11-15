---
name: dashboard-components
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: UI
source_file: frontend/src/pages/Dashboard.jsx
source: Semantic Memory Engine (SME)
tags:
  - dashboard-components
  - ui-widgets
  - telemetry-cards
  - reactive-ui
  - chart-components
inputs:
  component_name:
    type: string
    required: true
    description: UI widget name (`'metric_card'`, `'gauge_chart'`, `'sparkline_panel'`, `'table_grid'`).
  props:
    type: object
    required: true
    description: Component configuration properties and data bindings.
outputs:
  rendered_html:
    type: string
    description: Sanitized HTML/SVG snippet ready for frontend injection.
  component_id:
    type: string
    description: Unique DOM element identifier.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Dashboard Components Engine

`dashboard-components` renders reusable, accessible HTML/SVG dashboard widgets with dark theme styling and responsive layouts in Python:

$$\text{RenderWidget}(\text{Type}, \text{Props}) \to \text{HTMLString}(\text{TailwindDarkTheme}, \text{InteractiveSVG})$$

---

## The 5-Stage Dashboard Components Progression

1. **Component Name & Props Ingestion**: Ingest component identifier and data properties.
2. **Prop Validation & Sanitization**: Ensure data binds strictly conform to widget schemas.
3. **The Visual Brief**: Generate interactive HTML component preview at `%TEMP%\dashboard-components-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert XSS safety; escape all user-generated text strings.
5. **HTML Generation & Output Emission**: Emit clean HTML/SVG component string.

---

## Implementation Notes

```python
import uuid
import html
from typing import Dict, List, Any

def render_dashboard_component(
    component_name: str,
    props: Dict[str, Any]
) -> Dict[str, Any]:
    c_id = f"widget_{str(uuid.uuid4())[:6]}"
    title = html.escape(str(props.get("title", "Metric")))
    val = html.escape(str(props.get("value", "0")))
    
    html_out = f'<div id="{c_id}" class="bg-[#161b22] border border-[#30363d] p-4 rounded-xl text-[#c9d1d9]"><h4 class="text-xs uppercase text-[#8b949e]">{title}</h4><div class="text-2xl font-bold text-[#58a6ff] mt-1">{val}</div></div>'
    
    return {
        "rendered_html": html_out,
        "component_id": c_id,
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Unescaped XSS Injection** — Rendering user-supplied text strings directly into HTML templates without sanitization.
- **Hard-Coded Fixed Dimensions** — Using rigid fixed pixel widths that break responsive dashboard layouts.
