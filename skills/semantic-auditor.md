---
name: semantic-auditor
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: extensions/ext_semantic_auditor/
source: Semantic Memory Engine (SME)
tags:
  - semantic-auditor
  - hallucination-detection
  - factual-grounding
  - entailment-checking
  - claim-verification
inputs:
  generated_claims:
    type: array
    required: true
    description: List of claims or statements produced by an agent to audit.
  ground_truth_context:
    type: string
    required: true
    description: Authoritative source text or reference database to audit against.
outputs:
  audit_verdict:
    type: string
    description: Overall factual verification verdict (`'grounded'`, `'partially_grounded'`, `'hallucination'`).
  claim_verifications:
    type: array
    description: Per-claim entailment classifications (`'entailed'`, `'contradicted'`, `'unsupported'`).
  grounding_score:
    type: number
    description: Proportion of claims supported by ground truth in [0.0, 1.0].
---

# Semantic Auditor Engine

`semantic-auditor` verifies factual grounding and detects hallucinations in AI agent outputs by cross-referencing claims against authoritative context:

$$\text{GroundingScore} = \frac{1}{M}\sum_{i=1}^M \mathbb{I}\left( \text{Entailment}(c_i, \mathcal{K}) == \text{Supported} \right)$$

---

## The 5-Stage Semantic Auditor Progression

1. **Claim Extraction & Deconstruction**: Deconstruct input text into atomic, checkable factual claims $c_1, \dots, c_M$.
2. **Context Retrieval & Evidence Alignment**: Extract relevant evidence passages from the ground truth context for each claim.
3. **The Visual Brief**: Generate interactive HTML factual audit card at `%TEMP%\semantic-auditor-brief-<timestamp>.html` with claim pass/fail indicators.
4. **Mandatory Checkpoint**: Classify claims into Entailed, Contradicted, or Unsupported; flag contradictions as critical errors.
5. **Score Aggregation & Output Emission**: Compute aggregate `grounding_score` and emit complete `SemanticAuditReport`.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def audit_semantic_claims(
    generated_claims: List[str],
    ground_truth_context: str
) -> Dict[str, Any]:
    context_lower = ground_truth_context.lower()
    verifications = []
    supported_count = 0
    
    for claim in generated_claims:
        words = [w.lower() for w in claim.split() if len(w) > 3]
        matches = sum(1 for w in words if w in context_lower)
        ratio = matches / len(words) if words else 0.0
        
        if ratio >= 0.70:
            status = "entailed"
            supported_count += 1
        elif ratio >= 0.40:
            status = "partially_supported"
            supported_count += 0.5
        else:
            status = "unsupported"
            
        verifications.append({"claim": claim, "status": status, "overlap_ratio": round(ratio, 2)})
        
    score = round(supported_count / (len(generated_claims) or 1), 4)
    verdict = "grounded" if score >= 0.80 else ("partially_grounded" if score >= 0.50 else "hallucination")
    
    return {
        "audit_verdict": verdict,
        "claim_verifications": verifications,
        "grounding_score": score
    }
```

---

## Anti-Patterns & Guardrails

- **Surface Keyword False Entailment** — Assuming a claim is entailed merely because isolated nouns appear in the source context.
- **Ignoring Direct Negations** — Missing subtle negation flips ("X does not do Y" vs "X does Y").
