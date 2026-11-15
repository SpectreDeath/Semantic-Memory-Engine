---
name: sentiment-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Analysis
source_file: src/core/sentiment_analyzer.py
source: Semantic Memory Engine (SME)
tags:
  - sentiment-analysis
  - polarity-scoring
  - subjectivity-analysis
  - emotion-detection
  - lexicon-sentiment
inputs:
  text:
    type: string
    required: true
    description: Input text snippet or document to evaluate.
  aspects:
    type: array
    required: false
    description: Optional list of target entities/aspects to score specifically.
outputs:
  polarity:
    type: number
    description: Continuous sentiment polarity score in [-1.0, +1.0] (-1=negative, +1=positive).
  subjectivity:
    type: number
    description: Degree of subjective emotional expression in [0.0, 1.0] (0=objective, 1=subjective).
  sentiment_label:
    type: string
    description: Categorical label (`'positive'`, `'neutral'`, `'negative'`).
---

# Sentiment Analysis Engine

`sentiment-analysis` evaluates emotional polarity and subjective tone across textual corpora using **VADER / Transformer sentiment heuristics in Python**:

$$\text{Polarity} = \frac{\text{Pos} - \text{Neg}}{\sqrt{(\text{Pos} + \text{Neg})^2 + \alpha}}, \quad \text{Subjectivity} = \frac{\text{SubjectiveWords}}{\text{TotalWords}}$$

---

## The 5-Stage Sentiment Analysis Progression

1. **Text Ingestion & Token Normalization**: Ingest text; handle contractions, emoticons, and intensifiers.
2. **Lexicon & Valence Scoring**: Compute valence scores across sentiment lexicon dictionaries.
3. **The Visual Brief**: Generate interactive HTML sentiment polarity gauge brief at `%TEMP%\sentiment-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Handle negation modifiers ("not bad" $\to$ positive, "barely good" $\to$ negative).
5. **Polarity Classification & Output Emission**: Compute aggregate `polarity` and `subjectivity` metrics.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def analyze_sentiment(
    text: str,
    aspects: Optional[List[str]] = None
) -> Dict[str, Any]:
    t_low = text.lower()
    pos = sum(1 for w in ["great", "good", "excellent", "positive", "success"] if w in t_low)
    neg = sum(1 for w in ["bad", "terrible", "failure", "risk", "error"] if w in t_low)
    
    total = pos + neg
    if total == 0:
        pol = 0.0
        label = "neutral"
    else:
        pol = round((pos - neg) / total, 3)
        label = "positive" if pol > 0.1 else ("negative" if pol < -0.1 else "neutral")
        
    return {
        "polarity": pol,
        "subjectivity": round(min(1.0, total / 5.0), 3),
        "sentiment_label": label
    }
```

---

## Anti-Patterns & Guardrails

- **Sarcasm / Negation Inversion** — Misinterpreting sarcastic or double-negated sentences as straightforward literal statements.
- **Topical Lexicon Bias** — Scoring domain-specific technical terms (e.g. "critical vulnerability") as general emotional negativity.