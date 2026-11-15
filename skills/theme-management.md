---
name: theme-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: UI
source_file: frontend/src/contexts/ThemeContextProvider.jsx
source: Semantic Memory Engine (SME)
tags:
  - theme-management
  - dark-theme
  - design-tokens
  - css-variables
  - color-palette
inputs:
  action:
    type: string
    required: true
    description: "Operation (`'get_tokens'`, `'set_theme'`, `'export_css'`)."
  theme_name:
    type: string
    required: false
    description: "Name of theme (`'dark'`, `'matrix'`, `'cyberpunk'`, default `'dark'`)."
outputs:
  design_tokens:
    type: object
    description: Color tokens, font families, border radii, and elevation shadows.
  css_variables:
    type: string
    description: "Root CSS variable definitions block (`:root { --bg: #0d1117; ... }`)."
  status:
    type: string
    description: "Operation status string (`'ok'` or `'error'`)."
---

# Theme Management Engine

`theme-management` enforces consistent design tokens, dark theme color palettes (`#0d1117`, `#161b22`, `#58a6ff`), and CSS variables across all SME web interfaces and visual briefs in Python:

$$\text{ThemeCSS} = \text{CompileRootTokens}(\text{Colors}, \text{Typography}, \text{Elevations})$$

---

## The 5-Stage Theme Management Progression

1. **Theme Request Ingestion**: Ingest requested theme identifier (defaulting to dark theme).
2. **Token Compilation**: Assemble color tokens for surface backgrounds, text contrast, borders, and accent highlights.
3. **The Visual Brief**: Generate interactive HTML theme token preview brief at `%TEMP%\theme-management-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that contrast ratio between text (`#c9d1d9`) and background (`#0d1117`) exceeds WCAG AAA (7:1).
5. **CSS Emission**: Emit token dictionary and formatted `:root` CSS variables block.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def manage_ui_theme(
    action: str,
    theme_name: Optional[str] = "dark"
) -> Dict[str, Any]:
    tokens = {
        "bg_dark": "#0d1117",
        "bg_surface": "#161b22",
        "border": "#30363d",
        "text_primary": "#c9d1d9",
        "accent_blue": "#58a6ff",
        "accent_purple": "#bc8cff",
        "accent_green": "#3fb950"
    }
    css = ":root {\n" + "\n".join(f"  --{k}: {v};" for k, v in tokens.items()) + "\n}"
    
    return {
        "design_tokens": tokens,
        "css_variables": css,
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Hard-Coded Inline Hex Colors** — Using un-tokenized ad-hoc hex values across UI components rather than CSS variables.
- **Low Contrast Accessibility Violations** — Using dark gray text on black surfaces that fails accessibility readability checks.
