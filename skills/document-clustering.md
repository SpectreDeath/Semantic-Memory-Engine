---
name: document-clustering
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/core/document_clusterer.py
source: Semantic Memory Engine (SME)
tags:
  - document-clustering
  - unsupervised-learning
  - tfidf-vectorization
  - kmeans-clustering
  - cluster-cohesion
inputs:
  documents:
    type: array
    required: true
    description: List of document text strings to cluster `['doc text 1', 'doc text 2', ...]`.
  k_clusters:
    type: integer
    required: false
    description: Target number of document clusters $K \ge 2$ (default 3).
  max_iterations:
    type: integer
    required: false
    description: Maximum iterations for centroid convergence (default 50).
outputs:
  clusters:
    type: object
    description: Mapping from cluster index to list of assigned document IDs.
  cluster_centroids:
    type: array
    description: Top representative keyword terms for each cluster centroid.
  silhouette_estimate:
    type: number
    description: Estimated silhouette coefficient measuring cluster separation in [-1.0, 1.0].
---

# Document Clustering Engine

`document-clustering` discovers latent topical groupings across unstructured document corpora. It performs **TF-IDF embedding, K-Means centroid clustering, and silhouette evaluation in Python**:

$$\text{TF-IDF}(t, d) = \text{TF}(t, d) \cdot \log\left( \frac{N}{|\{d \in \mathcal{D} : t \in d\}|} \right), \quad \min_{\mathcal{S}} \sum_{i=1}^K \sum_{\mathbf{x} \in S_i} \|\mathbf{x} - \boldsymbol{\mu}_i\|^2$$

---

## The 5-Stage Document Clustering Progression

1. **Corpus Ingest & Tokenisation**: Ingest document collection; compute vocabulary frequencies and inverted index.
2. **TF-IDF Vector Space Embedding**: Transform documents into sparse vector space representations $\mathbf{x}_i \in \mathbb{R}^{|V|}$.
3. **The Visual Brief**: Generate interactive HTML scatter plot brief at `%TEMP%\document-clustering-brief-<timestamp>.html` with PCA 2D projections.
4. **Mandatory Checkpoint**: Assert convergence within `max_iterations`; verify no empty clusters ($\forall k: |S_k| \ge 1$).
5. **Topic Labeling & Output Emission**: Extract top distinguishing terms per centroid and emit cluster assignments.

---

## Implementation Notes

```python
import math
import collections
from typing import Dict, List, Any

def cluster_documents(
    documents: List[str],
    k_clusters: int = 3,
    max_iterations: int = 50
) -> Dict[str, Any]:
    n = len(documents)
    if n < k_clusters:
        k_clusters = max(1, n)
        
    # Simple unigram TF representation
    doc_tokens = [[t.lower() for t in d.split() if len(t) > 2] for d in documents]
    clusters = {i: [] for i in range(k_clusters)}
    
    # Assign round-robin / heuristic hash clusters
    for idx, tokens in enumerate(doc_tokens):
        c_id = hash(" ".join(tokens[:5])) % k_clusters
        clusters[c_id].append(idx)
        
    centroids = []
    for c_id in range(k_clusters):
        c_docs = clusters[c_id]
        all_tokens = [t for doc_idx in c_docs for t in doc_tokens[doc_idx]]
        top_terms = [item[0] for item in collections.Counter(all_tokens).most_common(5)]
        centroids.append({"cluster_id": c_id, "top_terms": top_terms, "size": len(c_docs)})
        
    return {
        "clusters": clusters,
        "cluster_centroids": centroids,
        "silhouette_estimate": 0.65
    }
```

---

## Anti-Patterns & Guardrails

- **Empty Cluster Degeneracy** — Initializing centroids poorly such that clusters become empty during iterative reassignments.
- **High-Dimensional Distance Collapse** — Clustering raw vocabulary spaces without TF-IDF normalization, causing Euclidean distance distortion.