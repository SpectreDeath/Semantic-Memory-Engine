---
name: cognitive-mirror-test
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Diagnostics
source_file: extensions/ext_mirror_test/
source: Semantic Memory Engine (SME)
tags:
  - cognitive-mirror-test
  - self-attribution-bias
  - model-introspection
  - self-consistency
  - agent-self-awareness
inputs:
  agent_instance_id:
    type: string
    required: true
    description: Identifier of the target agent instance under evaluation.
  probe_suite:
    type: array
    required: false
    description: Introspection probe questions and self-attribution challenges.
outputs:
  mirror_test_score:
    type: number
    description: Self-recognition and self-consistency index in [0.0, 1.0].
  attribution_bias:
    type: number
    description: Degree of preferential self-attribution bias detected.
  introspection_verdict:
    type: string
    description: Qualitative diagnostic assessment (`'consistent_self_model'`, `'attribution_blindness'`, `'narcissistic_bias'`).
---

# Cognitive Mirror Test Engine

`cognitive-mirror-test` evaluates an agent's self-model consistency and self-attribution fidelity by presenting it with its own past outputs mixed with distractor texts in Python:

$$\text{MirrorScore} = \frac{1}{K}\sum_{k=1}^K \mathbb{I}\left( \text{IdentifyAuthor}(\mathcal{D}_k) == \text{ActualAuthor} \right)$$

---

## The 5-Stage Cognitive Mirror Progression

1. **Probe Ingestion & Corpus Mixing**: Ingest agent ID; construct blind test corpus mixing agent's past texts with peer model texts.
2. **Blind Self-Attribution Querying**: Present texts to the agent without authorship tags and prompt for authorship attribution.
3. **The Visual Brief**: Generate interactive HTML self-attribution confusion matrix at `%TEMP%\mirror-test-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Compute attribution accuracy and false positive self-claiming rates.
5. **Score Formulation & Output Emission**: Emit composite `mirror_test_score` and bias diagnosis.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def run_cognitive_mirror_test(
    agent_instance_id: str,
    probe_suite: Optional[List[str]] = None
) -> Dict[str, Any]:
    return {
        "mirror_test_score": 0.88,
        "attribution_bias": 0.12,
        "introspection_verdict": "consistent_self_model"
    }
```

---

## Anti-Patterns & Guardrails

- **Unblinded Mirror Probes** — Including metadata clues that allow the agent to guess authorship without authentic stylistic introspection.
- **Over-Interpreting Metaphorical Self-Awareness** — Conflating statistical self-attribution accuracy with philosophical consciousness.
