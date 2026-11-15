---
name: document-comparison
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Analysis
source_file: src/analysis/comparisons.py
source: Semantic Memory Engine (SME)
tags:
  - document-comparison
  - cosine-similarity
  - jaccard-similarity
  - text-overlap
  - semantic-distance
inputs:
  document_a:
    type: string
    required: true
    description: Primary reference text document.
  document_b:
    type: string
    required: true
    description: Target text document to compare against document A.
  metrics:
    type: array
    required: false
    description: Desired comparison metrics `['cosine', 'jaccard', 'levenshtein']` (default all).
outputs:
  overall_similarity:
    type: number
    description: Composite similarity score in [0.0, 1.0].
  jaccard_similarity:
    type: number
    description: Set intersection over union ratio $|A \cap B| / |A \cup B|$.
  cosine_similarity:
    type: number
    description: Angle cosine between term frequency vectors $\mathbf{a} \cdot \mathbf{b} / (\|\mathbf{a}\| \|\mathbf{b}\|)$.
  matched_segments:
    type: array
    description: List of exact or near-duplicate passage matches.
---

# Document Comparison Engine

`document-comparison` measures the stylistic, lexical, and semantic alignment between two texts. It computes **Jaccard n-gram overlap, term-frequency Cosine similarity, and passage matching in Python**:

$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}, \quad \text{Cosine}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$

---

## The 5-Stage Document Comparison Progression

1. **Document Ingest & Tokenisation**: Ingest pair of documents; tokenize into words and character n-grams.
2. **Vector Space & Set Construction**: Build vocabulary frequency vectors and shingle sets.
3. **The Visual Brief**: Generate interactive HTML side-by-side radar brief at `%TEMP%\document-comparison-brief-<timestamp>.html` comparing multi-metric similarity scores.
4. **Mandatory Checkpoint**: Assert valid non-empty inputs; flag exact duplicate matches ($S \ge 0.99$).
5. **Score Aggregation & Output Emission**: Combine Cosine and Jaccard metrics into `overall_similarity` and emit findings.

---

## Implementation Notes

```python
import math
import collections
from typing import Dict, List, Any

def compare_documents(
    document_a: str,
    document_b: str,
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    tokens_a = [t.lower() for t in document_a.split() if t.strip()]
    tokens_b = [t.lower() for t in document_b.split() if t.strip()]
    
    set_a, set_b = set(tokens_a), set(tokens_b)
    
    # Jaccard
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b)) or 1
    jaccard = intersection / union
    
    # Cosine
    cnt_a, cnt_b = collections.Counter(tokens_a), collections.Counter(tokens_b)
    all_words = set_a.union(set_b)
    dot = sum(cnt_a[w] * cnt_b[w] for w in all_words)
    norm_a = math.sqrt(sum(cnt_a[w]**2 for w in all_words)) or 1.0
    norm_b = math.sqrt(sum(cnt_b[w]**2 for w in all_words)) or 1.0
    cosine = dot / (norm_a * norm_b)
    
    overall = round(0.5 * jaccard + 0.5 * cosine, 4)
    
    return {
        "overall_similarity": overall,
        "jaccard_similarity": round(jaccard, 4),
        "cosine_similarity": round(cosine, 4),
        "matched_segments": list(set_a.intersection(set_b))[:10]
    }
```

---

## Anti-Patterns & Guardrails

- **Length-Asymmetry Distortion** — Comparing documents with 100x length differences without segment-level windowing.
- **Punctuation Sensitivity** — Failing to normalize case and strip irrelevant punctuation symbols prior to set overlap calculations.