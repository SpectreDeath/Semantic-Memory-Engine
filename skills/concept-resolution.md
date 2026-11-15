---
name: concept-resolution
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Query
source_file: src/query/concept_resolver.py
source: Semantic Memory Engine (SME)
tags:
  - concept-resolution
  - ontology-mapping
  - entity-disambiguation
  - semantic-grounding
  - concept-graph
inputs:
  concept_term:
    type: string
    required: true
    description: Raw surface phrase, ambiguous term, or concept mention to resolve.
  domain_context:
    type: string
    required: false
    description: Surrounding domain or document context for semantic disambiguation.
outputs:
  canonical_concept_id:
    type: string
    description: Grounded ontology URI or canonical concept identifier.
  confidence_score:
    type: number
    description: Disambiguation confidence score in [0.0, 1.0].
  synonyms:
    type: array
    description: Associated aliases, synonyms, and hypernyms.
---

# Concept Resolution Engine

`concept-resolution` disambiguates raw surface mentions into canonical ontological concepts. It maps **mentions to ontology nodes using cosine similarity over semantic embeddings and WordNet graphs in Python**:

$$\hat{c} = \arg\max_{c \in \mathcal{C}} \left( \alpha \cdot \cos(\mathbf{e}(\text{term}), \mathbf{e}(c)) + (1 - \alpha) \cdot \text{ContextRelevance}(c, \text{Context}) \right)$$

---

## The 5-Stage Concept Resolution Progression

1. **Mention Intake & Normalization**: Ingest concept term and context; apply lemmatization and casing normalisation.
2. **Candidate Retrieval**: Query the ontology graph for fuzzy string and synset candidate matches.
3. **The Visual Brief**: Generate interactive HTML concept tree brief at `%TEMP%\concept-resolution-brief-<timestamp>.html` mapping candidate semantic distances.
4. **Mandatory Checkpoint**: Evaluate top candidate margin $\Delta = s_1 - s_2$; flag low-confidence ambiguous queries if $\Delta < 0.10$.
5. **Ontology Binding & Output Emission**: Bind mention to `canonical_concept_id` and emit structured resolution payload.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def resolve_concept(
    concept_term: str,
    domain_context: Optional[str] = None
) -> Dict[str, Any]:
    norm_term = concept_term.strip().lower()
    
    # Mock ontology lookup table
    ONTOLOGY = {
        "mcp": ("sme:mcp_gateway", ["model context protocol", "mcp bridge"], 0.95),
        "iesds": ("sme:iterated_dominance", ["iterated elimination", "iesds solver"], 0.98),
        "stylometry": ("sme:forensic_stylometry", ["authorship attribution", "burrows delta"], 0.92)
    }
    
    if norm_term in ONTOLOGY:
        cid, syns, conf = ONTOLOGY[norm_term]
    else:
        cid = f"sme:concept_{hash(norm_term) % 10000}"
        syns = [norm_term]
        conf = 0.70
        
    return {
        "canonical_concept_id": cid,
        "confidence_score": conf,
        "synonyms": syns
    }
```

---

## Anti-Patterns & Guardrails

- **Out-of-Context Over-Matching** — Disambiguating polysemous words (e.g. "bank", "apple") without inspecting the surrounding domain context.
- **Unchecked Ambiguity Propagation** — Returning arbitrary candidate bindings when confidence scores fall below acceptable certainty thresholds.