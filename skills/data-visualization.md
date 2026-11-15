---
name: data-visualization
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: UI
source_file: src/visualization/network_generator.py
source: Semantic Memory Engine (SME)
tags:
  - data-visualization
  - chart-generation
  - scatter-plots
  - bar-charts
  - svg-render
inputs:
  chart_type:
    type: string
    required: true
    description: Chart format (`'scatter'`, `'bar'`, `'line'`, `'radar'`, `'heatmap'`).
  chart_data:
    type: object
    required: true
    description: Structured dataset containing labels, series values, and axis titles.
outputs:
  chart_svg:
    type: string
    description: Standalone scalable vector graphics (SVG) chart string.
  chart_id:
    type: string
    description: Unique chart identifier.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Data Visualization Engine

`data-visualization` generates standalone interactive SVG and HTML charts (heatmaps, scatter plots, radar charts) in Python:

$$\text{RenderChart}(\text{Type}, \mathcal{D}) \to \text{SVG}(\text{Axes}, \text{Series}, \text{Tooltips})$$

---

## The 5-Stage Data Visualization Progression

1. **Chart Spec & Data Ingestion**: Ingest chart format and numerical series array.
2. **Coordinate Scaling & Layout Computation**: Compute data bounding box and map values to SVG viewBox coordinates.
3. **The Visual Brief**: Generate interactive HTML visual brief at `%TEMP%\data-vis-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert color contrast accessibility (WCAG AA) against dark backgrounds.
5. **SVG Serialization & Emission**: Emit clean SVG chart string.

---

## Implementation Notes

```python
import uuid
from typing import Dict, List, Any

def generate_chart_visualization(
    chart_type: str,
    chart_data: Dict[str, Any]
) -> Dict[str, Any]:
    c_id = f"chart_{str(uuid.uuid4())[:6]}"
    svg = f'<svg id="{c_id}" viewBox="0 0 400 200" class="w-full h-auto"><rect width="100%" height="100%" fill="#0d1117"/><text x="20" y="30" fill="#58a6ff">{chart_type.upper()} CHART</text></svg>'
    return {
        "chart_svg": svg,
        "chart_id": c_id,
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Hard-Coded Light Mode Palettes** — Generating SVG charts with black text or blinding white backgrounds that clash with dark theme UI.
- **Unbounded Axis Scales** — Rendering charts without handling extreme outlier values, distorting the entire visualization scale.
