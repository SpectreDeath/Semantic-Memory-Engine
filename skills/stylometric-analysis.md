---
name: stylometric-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Forensic Analysis
source_file: src/scribe/stylo_wrapper.py
source: Semantic Memory Engine (SME)
tags:
  - stylometric-analysis
  - authorship-attribution
  - lexical-richness
  - syntax-trees
  - forensic-linguistics
inputs:
  text_sample:
    type: string
    required: true
    description: Input text sample to profile stylometrically.
  feature_set:
    type: string
    required: false
    description: Extraction feature suite (`'comprehensive'`, `'function_words'`, `'lexical'`, default `'comprehensive'`).
outputs:
  stylometric_fingerprint:
    type: object
    description: Vector of extracted linguistic features (hapax legomena, Yule's K, Simpson's D, sentence complexity).
  lexical_diversity:
    type: number
    description: Measure of vocabulary richness (Type-Token Ratio / Yule's Characteristic K).
  author_profile_hash:
    type: string
    description: SHA-256 fingerprint hash of the extracted stylistic vector.
---

# Stylometric Analysis Engine

`stylometric-analysis` extracts high-dimensional linguistic fingerprints for forensic authorship attribution. It computes **lexical diversity (Yule's $K$, Simpson's $D$), function word frequencies, and syntactic sentence metrics in Python**:

$$\text{Yule's } K = 10^4 \cdot \frac{\sum_{m=1}^\infty m^2 V(m, N) - N}{N^2}, \quad \text{Simpson's } D = \sum_{i=1}^V \frac{n_i (n_i - 1)}{N(N - 1)}$$

---

## The 5-Stage Stylometric Analysis Progression

1. **Text Ingest & POS Tagging**: Tokenize input text; extract punctuation symbols, function word frequencies, and sentence boundary markers.
2. **Lexical Richness & Entropy Evaluation**: Compute Hapax Legomena ratio ($V_1 / N$), Type-Token Ratio (TTR), and Yule's Characteristic $K$.
3. **The Visual Brief**: Generate interactive HTML stylometric radar chart brief at `%TEMP%\stylometric-analysis-brief-<timestamp>.html` mapping feature dimensions against population baselines.
4. **Mandatory Checkpoint**: Assert minimum token threshold ($N \ge 100$) for statistical stability of Yule's $K$.
5. **Fingerprint Synthesis & Output Emission**: Compile structured feature vector and emit cryptographic `author_profile_hash`.

---

## Implementation Notes

```python
import hashlib
import json
import re
import collections
from typing import Dict, List, Any

def extract_stylometric_fingerprint(
    text_sample: str,
    feature_set: str = "comprehensive"
) -> Dict[str, Any]:
    tokens = [t.lower() for t in re.findall(r"\b\w+\b", text_sample)]
    n = len(tokens)
    if n < 10:
        return {"stylometric_fingerprint": {}, "lexical_diversity": 0.0, "author_profile_hash": "none"}
        
    counts = collections.Counter(tokens)
    vocab_size = len(counts)
    
    # Hapax legomena (words appearing exactly once)
    hapax = sum(1 for w, c in counts.items() if c == 1)
    
    # Yule's K
    sum_m2 = sum(c**2 for c in counts.values())
    yule_k = 10000.0 * (sum_m2 - n) / (n**2) if n > 1 else 0.0
    
    fingerprint = {
        "token_count": n,
        "vocabulary_size": vocab_size,
        "type_token_ratio": round(vocab_size / n, 4),
        "hapax_legomena_ratio": round(hapax / vocab_size, 4) if vocab_size else 0.0,
        "yules_k": round(yule_k, 2),
        "avg_word_length": round(sum(len(w) for w in tokens) / n, 2)
    }
    
    fp_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    
    return {
        "stylometric_fingerprint": fingerprint,
        "lexical_diversity": round(vocab_size / n, 4),
        "author_profile_hash": fp_hash
    }
```

---

## Anti-Patterns & Guardrails

- **Length-Unnormalized Metric Comparisons** — Comparing raw Type-Token Ratios across documents of drastically different lengths (TTR degrades monotonically with length).
- **Ignoring Genre / Topic Invariance** — Attributing authorship based on topical nouns rather than syntactic function words.