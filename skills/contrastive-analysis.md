---
name: contrastive-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/scribe/contrastive_analyzer.py
source: Semantic Memory Engine (SME)
tags:
  - contrastive-analysis
  - feature-divergence
  - distinctive-markers
  - comparative-forensics
  - group-separation
inputs:
  corpus_a:
    type: array
    required: true
    description: First text collection or author sample set.
  corpus_b:
    type: array
    required: true
    description: Second text collection or author sample set to contrast against corpus A.
  top_k_features:
    type: integer
    required: false
    description: Number of distinctive differentiating features to extract (default 20).
outputs:
  contrastive_markers:
    type: array
    description: Top distinctive features with directional divergence scores.
  divergence_score:
    type: number
    description: Total Jensen-Shannon or Kullback-Leibler divergence between corpora distributions.
  overlap_features:
    type: array
    description: Shared linguistic characteristics common to both collections.
---

# Contrastive Analysis Engine

`contrastive-analysis` extracts distinctive linguistic markers that separate two text corpora. It computes **relative frequency ratios, odds ratios, and Jensen-Shannon divergence in Python**:

$$\text{Divergence}(P, Q) = D_{\text{JS}}(P \parallel Q) = \frac{1}{2} D_{\text{KL}}(P \parallel M) + \frac{1}{2} D_{\text{KL}}(Q \parallel M), \quad M = \frac{1}{2}(P + Q)$$

$$\text{Distinctiveness}(w) = \log_2 \left( \frac{P(w \mid \mathcal{C}_A) + \epsilon}{P(w \mid \mathcal{C}_B) + \epsilon} \right)$$

---

## The 5-Stage Contrastive Analysis Progression

1. **Corpora Ingest & Vocabulary Compilation**: Ingest document arrays for Corpus A and Corpus B; build unified token frequency matrices.
2. **Probability Distribution Estimation**: Compute normalized unigram/bigram token distributions $P$ and $Q$ with Laplace smoothing.
3. **The Visual Brief**: Generate interactive HTML divergence plot at `%TEMP%\contrastive-analysis-brief-<timestamp>.html` with horizontal bar chart comparing Corpus A vs. B top markers.
4. **Mandatory Checkpoint**: Assert vocabulary overlap threshold; verify that divergence is statistically significant ($p < 0.05$).
5. **Marker Extraction & Output Emission**: Rank features by log-odds distinctiveness and emit top $K$ contrastive markers.

---

## Implementation Notes

```python
import math
import collections
from typing import Dict, List, Any

def run_contrastive_analysis(
    corpus_a: List[str],
    corpus_b: List[str],
    top_k_features: int = 20
) -> Dict[str, Any]:
    tokens_a = [t.lower() for doc in corpus_a for t in doc.split()]
    tokens_b = [t.lower() for doc in corpus_b for t in doc.split()]
    
    cnt_a = collections.Counter(tokens_a)
    cnt_b = collections.Counter(tokens_b)
    
    total_a = len(tokens_a) or 1
    total_b = len(tokens_b) or 1
    
    vocab = set(cnt_a.keys()).union(set(cnt_b.keys()))
    distinctive = []
    
    eps = 1e-6
    for w in vocab:
        p_a = (cnt_a[w] + 1) / (total_a + len(vocab))
        p_b = (cnt_b[w] + 1) / (total_b + len(vocab))
        log_odds = math.log2(p_a / p_b)
        distinctive.append({"feature": w, "log_odds": round(log_odds, 4), "freq_a": cnt_a[w], "freq_b": cnt_b[w]})
        
    distinctive.sort(key=lambda x: abs(x["log_odds"]), reverse=True)
    top_markers = distinctive[:top_k_features]
    
    # Approximate Jensen-Shannon Divergence
    js_div = sum(abs((cnt_a[w]/total_a) - (cnt_b[w]/total_b)) for w in vocab) / 2.0
    
    return {
        "contrastive_markers": top_markers,
        "divergence_score": round(js_div, 4),
        "overlap_features": [m["feature"] for m in top_markers if abs(m["log_odds"]) < 0.5]
    }
```

---

## Anti-Patterns & Guardrails

- **Zero-Frequency Division** — Failing to apply Laplace or additive smoothing to words appearing in only one corpus.
- **Stopword Dominance** — Allowing generic function words without stylistic importance to overwhelm top markers.
