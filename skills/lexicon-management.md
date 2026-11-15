---
name: lexicon-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Utilities
source_file: src/scribe/lexicon_importer.py
source: Semantic Memory Engine (SME)
tags:
  - lexicon-management
  - vocabulary-curation
  - stopwords-management
  - domain-dictionaries
  - token-lookup
inputs:
  lexicon_name:
    type: string
    required: true
    description: Identifier name for the target lexicon (e.g. `'forensic_cues'`, `'academic_stopwords'`).
  action:
    type: string
    required: true
    description: Operation (`'add'`, `'remove'`, `'query'`, `'export'`).
  terms:
    type: array
    required: false
    description: List of vocabulary entries or phrases to modify.
outputs:
  total_entries:
    type: integer
    description: Current total number of vocabulary terms in the lexicon.
  matched_terms:
    type: array
    description: Terms matched during query operations.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Lexicon Management Engine

`lexicon-management` maintains domain-specific vocabularies, stopword collections, and forensic dictionary terms in SQLite and Python:

$$\mathcal{L} \leftarrow \mathcal{L} \cup \mathcal{T}_{\text{new}}, \quad \text{Lookup}(w) \iff w \in \mathcal{L}$$

---

## The 5-Stage Lexicon Management Progression

1. **Request Intake & Lexicon Resolution**: Ingest lexicon identifier and action parameter; load active dictionary table.
2. **Vocabulary Mutation or Search**: Execute set operations (union, difference, membership query) in memory.
3. **The Visual Brief**: Generate interactive HTML lexicon frequency cloud brief at `%TEMP%\lexicon-management-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert UTF-8 normalization and deduplication across terms.
5. **Persistence & Output Emission**: Commit updated lexicon state to SQLite and emit confirmation summary.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def manage_lexicon(
    lexicon_name: str,
    action: str,
    terms: Optional[List[str]] = None
) -> Dict[str, Any]:
    # In-memory store
    store = {"forensic_cues": {"burstiness", "perplexity", "hapax", "yule"}, "stopwords": {"the", "and", "is"}}
    current = store.setdefault(lexicon_name, set())
    
    input_terms = set(t.lower().strip() for t in (terms or []) if t.strip())
    
    if action == "add":
        current.update(input_terms)
    elif action == "remove":
        current.difference_update(input_terms)
        
    matched = list(current.intersection(input_terms)) if action == "query" else list(current)[:20]
    
    return {
        "total_entries": len(current),
        "matched_terms": matched,
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Un-Normalized Duplicate Terms** — Storing mixed-case or un-stripped duplicate entries in lexicon sets.
- **Unbounded In-Memory Dictionaries** — Loading multi-million term lexicons without SQLite backing and indexing.
