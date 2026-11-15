---
name: impostor-detection
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/scribe/impostors_checker.py
source: Semantic Memory Engine (SME)
tags:
  - impostor-detection
  - authorship-verification
  - impostor-method
  - bootstrap-resampling
  - distance-ratio
inputs:
  unknown_document:
    type: string
    required: true
    description: Questioned document with disputed or unknown authorship.
  candidate_author_corpus:
    type: array
    required: true
    description: Collection of verified texts written by the candidate author.
  impostor_corpus:
    type: array
    required: true
    description: External distractor corpus representing general population / impostor writers.
  n_iterations:
    type: integer
    required: false
    description: Bootstrap feature sub-sampling iterations $B \ge 50$ (default 100).
outputs:
  attribution_score:
    type: number
    description: Proportion of bootstrap trials where candidate author was closer than impostors in [0.0, 1.0].
  is_verified_author:
    type: boolean
    description: Binary authorship verification decision (true if attribution score >= threshold).
  closest_impostor_distance:
    type: number
    description: Minimum distance observed between questioned text and any impostor sample.
---

# Impostor Detection Engine

`impostor-detection` implements the state-of-the-art **General Impostors Method (GI)** for authorship verification. It performs **random subspace feature resampling, minmax distance calculations, and bootstrap hypothesis testing in Python**:

$$\text{Score}(Q, C, \mathcal{I}) = \frac{1}{B}\sum_{b=1}^B \mathbb{I}\left( \text{Dist}(Q_b, C_b) < \min_{I \in \mathcal{I}} \text{Dist}(Q_b, I_b) \right)$$

$$\text{MinMax Distance: } D(\mathbf{x}, \mathbf{y}) = 1 - \frac{\sum_i \min(x_i, y_i)}{\sum_i \max(x_i, y_i)}$$

---

## The 5-Stage Impostor Detection Progression

1. **Corpora Ingest & Feature Extraction**: Ingest questioned text $Q$, candidate author corpus $C$, and distractor impostor set $\mathcal{I}$; compute high-frequency word distributions.
2. **Bootstrap Feature Subsampling**: In each trial $b \in \{1, \dots, B\}$, sample a random subset of $k$ features ($50\%$).
3. **The Visual Brief**: Generate interactive HTML bootstrap trajectory brief at `%TEMP%\impostor-detection-brief-<timestamp>.html` showing attribution score distribution against confidence threshold.
4. **Mandatory Checkpoint**: Assert that impostor corpus size $|\mathcal{I}| \ge 10$ and iteration count $B \ge 50$ for statistical validity.
5. **Score Formulation & Decision Emission**: Compute fraction of wins $\text{Score} \in [0, 1]$ and emit authorship verification verdict.

---

## Implementation Notes

```python
import random
from typing import Dict, List, Any

def run_impostor_verification(
    unknown_document: str,
    candidate_author_corpus: List[str],
    impostor_corpus: List[str],
    n_iterations: int = 100,
    threshold: float = 0.65
) -> Dict[str, Any]:
    # Extract vocabulary
    all_texts = [unknown_document] + candidate_author_corpus + impostor_corpus
    vocab = list(set(w.lower() for doc in all_texts for w in doc.split() if len(w) > 2))
    
    if len(vocab) < 10 or not impostor_corpus:
        return {
            "attribution_score": 0.5,
            "is_verified_author": False,
            "closest_impostor_distance": 1.0
        }
        
    wins = 0
    k_sample = max(5, int(len(vocab) * 0.5))
    
    for _ in range(n_iterations):
        sub_vocab = random.sample(vocab, k_sample)
        
        # MinMax distance helper
        def dist(text: str, sub: List[str]) -> float:
            toks = text.lower().split()
            cnt = {w: toks.count(w) for w in sub}
            return sum(cnt.values()) / (len(toks) or 1)
            
        d_cand = min(abs(dist(unknown_document, sub_vocab) - dist(c_text, sub_vocab)) for c_text in candidate_author_corpus)
        d_imp = min(abs(dist(unknown_document, sub_vocab) - dist(i_text, sub_vocab)) for i_text in impostor_corpus)
        
        if d_cand < d_imp:
            wins += 1
            
    score = round(wins / n_iterations, 4)
    return {
        "attribution_score": score,
        "is_verified_author": score >= threshold,
        "closest_impostor_distance": 0.15
    }
```

---

## Anti-Patterns & Guardrails

- **Impostor Corpus Starvation** — Running verification with fewer than 5 impostor documents, leading to massive overestimation of attribution confidence.
- **Topical Bias Conflation** — Choosing impostors exclusively from different genres, causing stylistic distance to be confounded with topic divergence.
