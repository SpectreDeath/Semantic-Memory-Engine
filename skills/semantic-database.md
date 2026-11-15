---
name: semantic-database
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Storage
source_file: src/core/semantic_db.py
source: Semantic Memory Engine (SME)
tags:
  - semantic-database
  - vector-store
  - embedding-storage
  - similarity-search
  - sqlite-vec
inputs:
  action:
    type: string
    required: true
    description: Operation (`'insert'`, `'query'`, `'delete'`, `'compact'`).
  records:
    type: array
    required: false
    description: Document payloads and dense embedding vectors to insert.
  query_vector:
    type: array
    required: false
    description: Dense vector query for nearest-neighbor similarity search.
  top_k:
    type: integer
    required: false
    description: Number of nearest neighbors to retrieve (default 5).
outputs:
  results:
    type: array
    description: Retrieved nearest-neighbor records with cosine similarity distances.
  affected_count:
    type: integer
    description: Number of records inserted, modified, or deleted.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Semantic Database Engine

`semantic-database` manages vector embeddings and nearest-neighbor indices in SQLite:

$$\text{NearestNeighbors}(\mathbf{q}) = \arg\min_{\mathbf{v}_i \in \mathcal{V}} (1 - \cos(\mathbf{q}, \mathbf{v}_i))$$

---

## The 5-Stage Semantic Database Progression

1. **Request Intake & Schema Audit**: Ingest action and vectors; assert uniform embedding dimension $D$.
2. **Vector Index Query or Mutation**: Execute brute-force / SQLite-vec cosine similarity or batch vector inserts.
3. **The Visual Brief**: Generate interactive HTML vector space projection brief at `%TEMP%\semantic-db-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert vector normalization $\|\mathbf{v}\|_2 = 1.0$ for fast dot-product cosine metrics.
5. **Results Formatting & Output Emission**: Sort records by similarity and emit structured payload.

---

## Implementation Notes

```python
import math
from typing import Dict, List, Any, Optional

def query_semantic_database(
    action: str,
    records: Optional[List[Dict[str, Any]]] = None,
    query_vector: Optional[List[float]] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    # In-memory vector store simulation
    store = [
        {"id": "doc_1", "text": "Forensic stylometry", "vector": [0.8, 0.2, 0.1]},
        {"id": "doc_2", "text": "MCP Gateway", "vector": [0.1, 0.9, 0.2]},
        {"id": "doc_3", "text": "Z3 SMT logic", "vector": [0.2, 0.3, 0.9]}
    ]
    
    if action == "query" and query_vector:
        def cos_sim(v1: List[float], v2: List[float]) -> float:
            dot = sum(a * b for a, b in zip(v1, v2))
            n1 = math.sqrt(sum(a**2 for a in v1)) or 1.0
            n2 = math.sqrt(sum(b**2 for b in v2)) or 1.0
            return dot / (n1 * n2)
            
        scored = []
        for r in store:
            sim = cos_sim(query_vector, r["vector"])
            scored.append({**r, "similarity": round(sim, 4)})
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return {"results": scored[:top_k], "affected_count": len(scored), "status": "ok"}
        
    return {"results": [], "affected_count": len(records or []), "status": "ok"}
```

---

## Anti-Patterns & Guardrails

- **Dimension Mismatch Crashes** — Querying vector indices with vectors of unequal dimension ($D_{\text{query}} \neq D_{\text{index}}$).
- **Un-Normalized Dot Products** — Computing dot products without verifying unit vector norms.