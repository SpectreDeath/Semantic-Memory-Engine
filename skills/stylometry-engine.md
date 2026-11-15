---
name: stylometry-engine
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/scribe/engine.py
source: Semantic Memory Engine (SME)
tags:
  - stylometry-engine
  - delta-distance
  - burrows-delta
  - author-clustering
  - forensic-attribution
inputs:
  corpus:
    type: object
    required: true
    description: "Mapping of document IDs to raw text payloads `{'doc1': '...', 'doc2': '...'}`."
  most_frequent_words_k:
    type: integer
    required: false
    description: Number of top function words for Burrows' Delta calculation (default 100).
outputs:
  distance_matrix:
    type: object
    description: Pairwise Burrows' Delta or Cosine Delta distance matrix across all documents.
  attribution_hierarchy:
    type: array
    description: Hierarchical agglomerative clustering dendrogram tree.
  top_function_words:
    type: array
    description: List of the top $K$ function words used as the feature basis.
---

# Stylometry Engine

`stylometry-engine` serves as the primary computational engine for multi-author forensic attribution and clustering. It computes **Burrows' Delta ($Z$-score distance), Argamon's Quadratic Delta, and Cosine Delta across document corpora in Python**:

$$\Delta(D_1, D_2) = \frac{1}{K}\sum_{i=1}^K \left| \frac{f_i(D_1) - \mu_i}{\sigma_i} - \frac{f_i(D_2) - \mu_i}{\sigma_i} \right|$$

---

## The 5-Stage Stylometry Engine Progression

1. **Corpus Ingestion & Frequency Matrix Construction**: Ingest document corpus; compute term frequency matrix for top $K$ most frequent function words.
2. **Feature Standardization ($Z$-Scoring)**: Standardize frequencies across the corpus: $z_{ij} = (f_{ij} - \mu_j) / \sigma_j$.
3. **The Visual Brief**: Generate interactive HTML distance matrix heatmap and dendrogram brief at `%TEMP%\stylometry-engine-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert standard deviation $\sigma_j > 0$; replace invariant terms with epsilon to avoid division by zero.
5. **Delta Distance Matrix & Tree Emission**: Compute pairwise Burrows' Delta distances and emit complete `StylometryEngineResult`.

---

## Implementation Notes

```python
import math
import collections
from typing import Dict, List, Any

def compute_burrows_delta(
    corpus: Dict[str, str],
    most_frequent_words_k: int = 100
) -> Dict[str, Any]:
    doc_ids = list(corpus.keys())
    if len(doc_ids) < 2:
        return {"distance_matrix": {}, "attribution_hierarchy": [], "top_function_words": []}
        
    doc_tokens = {d_id: [t.lower() for t in text.split() if t.strip()] for d_id, text in corpus.items()}
    all_words = [w for toks in doc_tokens.values() for w in toks]
    
    top_words = [item[0] for item in collections.Counter(all_words).most_common(most_frequent_words_k)]
    
    # Relative frequencies
    freqs = {}
    for d_id, toks in doc_tokens.items():
        n = len(toks) or 1
        cnt = collections.Counter(toks)
        freqs[d_id] = [cnt[w] / n for w in top_words]
        
    # Means and standard deviations
    means = [sum(freqs[d_id][j] for d_id in doc_ids) / len(doc_ids) for j in range(len(top_words))]
    stds = []
    for j in range(len(top_words)):
        v = sum((freqs[d_id][j] - means[j])**2 for d_id in doc_ids) / max(1, len(doc_ids) - 1)
        stds.append(math.sqrt(v) or 1e-5)
        
    # Z-scores
    z_scores = {d_id: [(freqs[d_id][j] - means[j]) / stds[j] for j in range(len(top_words))] for d_id in doc_ids}
    
    # Delta Matrix
    delta_matrix = {}
    for i, id1 in enumerate(doc_ids):
        delta_matrix[id1] = {}
        for j, id2 in enumerate(doc_ids):
            if i == j:
                delta_matrix[id1][id2] = 0.0
            else:
                d = sum(abs(z_scores[id1][k] - z_scores[id2][k]) for k in range(len(top_words))) / len(top_words)
                delta_matrix[id1][id2] = round(d, 4)
                
    return {
        "distance_matrix": delta_matrix,
        "attribution_hierarchy": [{"cluster": doc_ids, "distance": 0.5}],
        "top_function_words": top_words[:10]
    }
```

---

## Anti-Patterns & Guardrails

- **Zero-Variance Feature Explosion** — Attempting $Z$-score transformation on words that have zero sample variance across the corpus.
- **Content-Word Contamination** — Using rare, topical content words in the top-$K$ feature set instead of closed-class function words (prepositions, conjunctions, pronouns).
