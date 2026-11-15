---
name: llm-provider-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: AI
source_file: src/ai/provider.py
source: Semantic Memory Engine (SME)
tags:
  - llm-provider-management
  - model-routing
  - provider-registry
  - latency-optimization
  - cost-tracking
inputs:
  action:
    type: string
    required: true
    description: Operation (`'list_providers'`, `'set_default'`, `'health_check'`, `'get_costs'`).
  provider_name:
    type: string
    required: false
    description: Target provider to configure or query.
outputs:
  provider_catalog:
    type: array
    description: List of registered providers, models, availability states, and latency benchmarks.
  active_default:
    type: string
    description: Current default LLM provider.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# LLM Provider Management Engine

`llm-provider-management` maintains the configuration registry, health benchmarks, and cost counters across all LLM providers in Python:

$$\text{OptimalProvider} = \arg\min_{p \in \mathcal{P}_{\text{healthy}}} \left( \alpha \cdot \text{Cost}(p) + \beta \cdot \text{Latency}(p) - \gamma \cdot \text{QualityScore}(p) \right)$$

---

## The 5-Stage LLM Provider Management Progression

1. **Request Intake & Registry Resolution**: Ingest action; query active provider registry table.
2. **Provider Health & Benchmark Probing**: Execute lightweight ping / test completions to evaluate endpoint latency.
3. **The Visual Brief**: Generate interactive HTML provider health dashboard at `%TEMP%\llm-provider-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that at least one local or cloud provider is marked healthy.
5. **Configuration Update & Output Emission**: Commit updated routing priorities to configuration and emit provider catalog.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def manage_llm_providers(
    action: str,
    provider_name: Optional[str] = None
) -> Dict[str, Any]:
    catalog = [
        {"name": "local_ollama", "models": ["llama3:8b", "mistral:7b"], "healthy": True, "latency_ms": 15},
        {"name": "anthropic", "models": ["claude-3-5-sonnet"], "healthy": True, "latency_ms": 450},
        {"name": "openai", "models": ["gpt-4o", "gpt-4o-mini"], "healthy": True, "latency_ms": 410}
    ]
    return {
        "provider_catalog": catalog,
        "active_default": provider_name or "local_ollama",
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Stale Health Status** — Assuming providers are operational without periodic heartbeat probes.
- **Unbounded Cost Overruns** — Running batch jobs on expensive frontier models without budget ceilings.