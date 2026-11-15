---
name: trust-score-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Forensic Analysis
source_file: extensions/ext_epistemic_gatekeeper/
source: Semantic Memory Engine (SME)
tags:
  - trust-score-analysis
  - credibility-scoring
  - source-reputation
  - multi-factor-trust
  - provenance-weighting
inputs:
  source_metadata:
    type: object
    required: true
    description: Information source metadata including domain age, historical accuracy, and citation provenance.
outputs:
  composite_trust_score:
    type: number
    description: Multi-factor trust coefficient in [0.0, 1.0].
  factor_breakdown:
    type: object
    description: Individual scores for provenance, consistency, domain reputation, and citation volume.
  trust_tier:
    type: string
    description: Categorical confidence tier (`'high_trust'`, `'moderate_trust'`, `'untrusted'`).
---

# Trust Score Analysis Engine

`trust-score-analysis` evaluates the multi-factor credibility and reliability index of information sources in Python:

$$\text{TrustScore} = w_1 \cdot \text{Provenance} + w_2 \cdot \text{Consistency} + w_3 \cdot \text{Reputation} + w_4 \cdot \text{Transparency}$$

---

## The 5-Stage Trust Score Progression

1. **Source Ingestion & Provenance Audit**: Ingest source metadata and historical publication track record.
2. **Multi-Factor Score Aggregation**: Compute sub-scores for citation density, domain authority, and consistency.
3. **The Visual Brief**: Generate interactive HTML trust score radial gauge at `%TEMP%\trust-score-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert non-negative weights summing to 1.0; flag newly registered unverified domains.
5. **Tier Classification & Emission**: Map score to categorical trust tier and emit full audit record.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def compute_trust_score(
    source_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    provenance = 0.90 if source_metadata.get("has_doi", True) else 0.50
    reputation = 0.85 if source_metadata.get("domain_age_years", 5) > 2 else 0.40
    consistency = 0.95
    
    comp = round(0.4 * provenance + 0.3 * reputation + 0.3 * consistency, 3)
    tier = "high_trust" if comp >= 0.80 else ("moderate_trust" if comp >= 0.50 else "untrusted")
    
    return {
        "composite_trust_score": comp,
        "factor_breakdown": {"provenance": provenance, "reputation": reputation, "consistency": consistency},
        "trust_tier": tier
    }
```

---

## Anti-Patterns & Guardrails

- **Domain Age Blindness** — Assigning high trust to anonymous brand-new web domains without historical publication archives.
- **Uncalibrated Weighting** — Computing composite trust scores without empirical calibration against known ground truth corpora.