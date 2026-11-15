---
name: external-ai-connector
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Integration
source_file: src/ai/external_ai_integration.py
source: Semantic Memory Engine (SME)
tags:
  - external-ai-connector
  - model-api-bridge
  - openai-anthropic-gemini
  - provider-fallback
  - token-streaming
inputs:
  provider:
    type: string
    required: true
    description: "External AI provider (`'openai'`, `'anthropic'`, `'gemini'`, `'ollama'`)."
  model:
    type: string
    required: false
    description: "Specific model identifier (e.g. `'claude-3-5-sonnet'`, `'gpt-4o'`)."
  messages:
    type: array
    required: true
    description: "Standard chat completion message array `[{'role': 'user', 'content': '...'}]`."
outputs:
  completion_text:
    type: string
    description: Generated response string returned by the upstream provider.
  usage_metrics:
    type: object
    description: "Token consumption metrics (`prompt_tokens`, `completion_tokens`, `total_cost_usd`)."
  provider_used:
    type: string
    description: Upstream provider and model that successfully answered the request.
---

# External AI Connector Engine

`external-ai-connector` manages upstream model API connectivity, streaming responses, exponential backoff retries, and automatic provider failover in Python:

$$\text{CallLLM}(\mathcal{M}, \text{Params}) \xrightarrow{\text{Failover}} \text{Provider}_1 \to \text{Provider}_2 \to \text{LocalOllama}$$

---

## The 5-Stage External AI Connector Progression

1. **Request Intake & Message Validation**: Ingest message array and requested provider/model; assert non-empty prompt.
2. **Provider Route Selection**: Select primary upstream API; prepare fallback provider cascade.
3. **The Visual Brief**: Generate interactive HTML token latency/cost brief at `%TEMP%\external-ai-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert API key availability and rate-limit quotas; engage local fallback on HTTP 429/500 errors.
5. **Streaming/Completion & Output Emission**: Execute API call, capture token metrics, and emit `completion_text`.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def call_external_ai(
    provider: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None
) -> Dict[str, Any]:
    last_msg = messages[-1]["content"] if messages else ""
    return {
        "completion_text": f"Simulated response from {provider} ({model or 'default'}): Echoing '{last_msg[:40]}...'",
        "usage_metrics": {"prompt_tokens": len(last_msg.split()), "completion_tokens": 20, "total_cost_usd": 0.0004},
        "provider_used": f"{provider}:{model or 'default'}"
    }
```

---

## Anti-Patterns & Guardrails

- **Hard-Coded Single Provider Dependency** — Failing to configure local or secondary fallbacks when upstream cloud APIs experience outages.
- **Uncapped Token Streaming** — Allowing generation loops without max_token boundaries.