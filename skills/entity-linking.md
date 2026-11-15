---
name: entity-linking
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/core/entity_linker.py
source: Semantic Memory Engine (SME)
tags:
  - entity-linking
  - named-entity-disambiguation
  - knowledge-graph-linking
  - wikidata-grounding
  - ner-linking
inputs:
  text:
    type: string
    required: true
    description: Input document containing named entity mentions.
  knowledge_base_scope:
    type: string
    required: false
    description: Target knowledge base (`'sme_internal'`, `'wikidata'`, `'dbpedia'`, default `'sme_internal'`).
outputs:
  linked_entities:
    type: array
    description: List of detected entities with character spans, entity types, and linked knowledge base identifiers.
  unlinked_mentions:
    type: array
    description: Named entities detected in text that could not be confidently grounded.
---

# Entity Linking Engine

`entity-linking` recognizes named entity mentions and grounds them in a structured knowledge base graph in Python:

$$\hat{e} = \arg\max_{e \in \mathcal{E}} \left( P(e \mid \text{Mention}) \cdot \prod_{e' \in \text{Context}} \text{Coherence}(e, e') \right)$$

---

## The 5-Stage Entity Linking Progression

1. **Text Ingestion & NER Span Extraction**: Extract surface entity mentions (Person, Organization, Location) with character offsets $[s, e]$.
2. **Candidate Generation**: Retrieve potential knowledge base entity matches for each surface mention.
3. **The Visual Brief**: Generate interactive HTML entity relationship graph brief at `%TEMP%\entity-linking-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Evaluate graph coherence across co-occurring entities; filter out low-confidence linkages ($P < 0.60$).
5. **Entity Binding & Output Emission**: Emit resolved entity mapping array with canonical URIs and unlinked mention list.

---

## Implementation Notes

```python
import re
from typing import Dict, List, Any, Optional

def link_entities(
    text: str,
    knowledge_base_scope: str = "sme_internal"
) -> Dict[str, Any]:
    # Mock NER & Linking
    linked = []
    unlinked = []
    
    patterns = {
        r"\b(Lawnmower Man|SME)\b": ("sme:system:lawnmower_man", "SYSTEM"),
        r"\b(SQLite|Python|Z3)\b": ("sme:tech:runtime", "TECHNOLOGY"),
        r"\b(John Doe|Alice)\b": ("sme:person:unknown", "PERSON")
    }
    
    for pat, (uri, ent_type) in patterns.items():
        for m in re.finditer(pat, text, re.IGNORECASE):
            linked.append({
                "mention": m.group(0),
                "span": [m.start(), m.end()],
                "entity_type": ent_type,
                "kb_id": uri,
                "confidence": 0.92
            })
            
    return {
        "linked_entities": linked,
        "unlinked_mentions": unlinked
    }
```

---

## Anti-Patterns & Guardrails

- **Local-Only Disambiguation** — Linking entities independently without considering global cross-entity topic coherence.
- **Ambiguous Acronym Collision** — Linking short acronyms (e.g. "SME", "API") to incorrect global domains without context gating.