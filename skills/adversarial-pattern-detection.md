---
name: adversarial-pattern-detection
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: AI Detection
source_file: extensions/ext_adversarial_breaker/
source: Semantic Memory Engine (SME)
tags:
  - adversarial-pattern-detection
  - ai-detection
  - burstiness-variance
  - perplexity-scoring
  - synthetic-watermarking
  - linguistic-smoothing
inputs:
  document_text:
    type: string
    required: true
    description: Raw target text payload to inspect for synthetic or AI-assisted generation patterns.
  min_token_length:
    type: integer
    required: false
    description: Minimum required token count for statistical stability (default 50).
  confidence_threshold:
    type: number
    required: false
    description: Decision threshold for classification as synthetic text (default 0.75).
outputs:
  is_synthetic:
    type: boolean
    description: Binary verdict indicating whether the text exhibits synthetic/AI generation signatures.
  synthetic_probability:
    type: number
    description: Calibrated probability score in [0.0, 1.0] of AI generation.
  burstiness_score:
    type: number
    description: Coefficient of variation of sentence lengths sigma_len / mu_len.
  perplexity_estimate:
    type: number
    description: Estimated n-gram cross-entropy perplexity of the token sequence.
  detected_signatures:
    type: array
    description: List of flagged synthetic artifacts (e.g. uniform sentence length, lack of stylistic idiosyncrasies).
---

# Adversarial Pattern Detection Engine

`adversarial-pattern-detection` detects AI-generated, AI-smoothed, or watermarked text. It calculates **sentence-length burstiness variance, n-gram perplexity, and synthetic signature entropy in Python**:

$$\text{Burstiness} = \frac{\sigma_{\text{sentence\_length}}}{\mu_{\text{sentence\_length}}}, \quad \text{Perplexity} = \exp\left( -\frac{1}{N}\sum_{i=1}^N \ln P(w_i \mid w_{i-1}, \dots) \right)$$

$$\text{Synthetic Probability: } P(\text{AI}) = \sigma\left( \beta_0 - \beta_1 \cdot \text{Burstiness} + \beta_2 \cdot \text{RepetitionIndex} - \beta_3 \cdot \text{Entropy} \right)$$

---

## The 5-Stage Adversarial Detection Progression

1. **Tokenisation & Sentence Segmentation**: Segment document into sentence boundaries and clean token sequences; assert $N \ge N_{\text{min}}$.
2. **Burstiness & Perplexity Analysis**: Compute sentence length standard deviation, mean length, and transition entropy.
3. **The Visual Brief**: Generate interactive HTML distribution brief at `%TEMP%\adversarial-detection-brief-<timestamp>.html` comparing sample metrics against baseline human vs. LLM corpora.
4. **Mandatory Checkpoint**: Evaluate multi-factor threshold gate; cross-check low burstiness ($< 0.25$) with high transition uniformity.
5. **Verdict & Anomaly Emission**: Synthesize final `synthetic_probability` and emit detailed forensic report with flagged tokens.

---

## Implementation Notes

```python
import math
import re
from typing import Dict, List, Any

def detect_adversarial_patterns(
    document_text: str,
    min_token_length: int = 50,
    confidence_threshold: float = 0.75
) -> Dict[str, Any]:
    # 1. Segment sentences and tokens
    sentences = [s.strip() for s in re.split(r"[.!?]+", document_text) if len(s.strip()) > 3]
    tokens = [t.lower() for t in re.findall(r"\b\w+\b", document_text)]
    
    if len(tokens) < min_token_length:
        return {
            "is_synthetic": False,
            "synthetic_probability": 0.0,
            "burstiness_score": 0.0,
            "perplexity_estimate": 0.0,
            "detected_signatures": ["insufficient_token_length"]
        }

    # 2. Burstiness: CV of sentence lengths
    s_lens = [len(s.split()) for s in sentences]
    mu_len = sum(s_lens) / len(s_lens) if s_lens else 1.0
    var_len = sum((l - mu_len)**2 for l in s_lens) / (len(s_lens) if len(s_lens) > 1 else 1)
    sigma_len = math.sqrt(var_len)
    burstiness = sigma_len / mu_len if mu_len > 0 else 0.0

    # 3. Vocabulary richness / Type-Token Ratio (TTR)
    unique_tokens = set(tokens)
    ttr = len(unique_tokens) / len(tokens)

    # Heuristic synthetic indicator: Low burstiness + moderate-to-low TTR
    synthetic_score = max(0.0, min(1.0, (1.0 - min(1.0, burstiness * 1.5)) * 0.6 + (1.0 - ttr) * 0.4))
    signatures = []
    if burstiness < 0.28:
        signatures.append("low_sentence_length_variance")
    if ttr < 0.45:
        signatures.append("repetitive_lexical_distribution")

    return {
        "is_synthetic": synthetic_score >= confidence_threshold,
        "synthetic_probability": round(synthetic_score, 4),
        "burstiness_score": round(burstiness, 4),
        "perplexity_estimate": round(math.exp(max(1.0, 4.0 - burstiness)), 2),
        "detected_signatures": signatures
    }
```

---

## Anti-Patterns & Guardrails

- **Short-Snippet False Positives** — Running statistical burstiness checks on short snippets ($< 50$ tokens) where variance cannot be stably measured.
- **Single-Metric Reliance** — Classifying text as AI-generated purely based on vocabulary richness without sentence-structure burstiness cross-validation.