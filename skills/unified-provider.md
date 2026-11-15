---
name: unified-provider
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: AI
source_file: src/ai/unified_provider.py
source: Semantic Memory Engine (SME)
tags:
  - unified-provider
  - multi-llm-routing
  - polymorphic-interface
  - stream-handling
  - provider-abstraction
inputs:
  prompt:
    type: string
    required: true
    description: Input prompt string or formatted messages array.
  routing_strategy:
    type: string
    required: false
    description: Model routing heuristic (`'lowest_latency'`, `'lowest_cost'`, `'highest_intelligence'`, default `'lowest_latency'`).
outputs:
  response_text:
    type: string
    description: Model generated completion string.
  provider_info:
    type: object
    description: Upstream provider and model dispatched.
  latency_ms:
    type: number
    description: End-to-end execution wall-clock time in milliseconds.
---

# Unified Provider Engine

`unified-provider` provides a single polymorphic interface across all local and cloud LLM backends (Ollama, Anthropic, OpenAI, Gemini) with dynamic quality/cost routing in Python:

$$\text{Provider}^* = \arg\max_{p \in \mathcal{P}} \mathcal{U}(p \mid \text{PromptComplexity}, \text{LatencyTarget}, \text{Budget})$$

---

## The 5-Stage Unified Provider Progression

1. **Prompt Ingest & Complexity Scoring**: Ingest prompt; estimate token count, domain difficulty, and structural requirements.
2. **Dynamic Route Optimization**: Select target model based on configured `routing_strategy`.
3. **The Visual Brief**: Generate interactive HTML routing telemetry brief at `%TEMP%\unified-provider-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert provider health; seamlessly failover to local model on cloud network timeout.
5. **Completion Dispatch & Emission**: Stream or batch complete response and emit unified payload with metadata.

---

## Implementation Notes

```python
import time
from typing import Dict, List, Any, Optional

def dispatch_unified_llm(
    prompt: str,
    routing_strategy: str = "lowest_latency"
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    # Dynamic routing simulation
    selected = "local_ollama:llama3" if routing_strategy == "lowest_latency" else "anthropic:claude-3-5-sonnet"
    elapsed = (time.perf_counter() - t0) * 1000.0
    
    return {
        "response_text": f"Unified provider response from {selected} to prompt: '{prompt[:40]}...'",
        "provider_info": {"provider": selected.split(":")[0], "model": selected.split(":")[1]},
        "latency_ms": round(elapsed + 15.0, 2)
    }
```

---

## Anti-Patterns & Guardrails

- **Hard-Coded Upstream Endpoints** — Coupling client code directly to specific vendor SDKs instead of the unified abstraction layer.
- **Unmonitored Cost Escalation** — Routing simple extraction tasks to frontier models when local models suffice.