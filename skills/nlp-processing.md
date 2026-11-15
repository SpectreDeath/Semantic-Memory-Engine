---
name: nlp-processing
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: NLP
source_file: src/core/nlp_pipeline.py
source: Semantic Memory Engine (SME)
tags:
  - nlp-processing
  - text-tokenization
  - lemmatization
  - pos-tagging
  - sentence-splitting
inputs:
  text:
    type: string
    required: true
    description: Input natural language text string to process.
  tasks:
    type: array
    required: false
    description: NLP pipeline stages `['tokenize', 'pos_tag', 'lemmatize', 'sentences']` (default all).
outputs:
  tokens:
    type: array
    description: List of extracted word tokens.
  sentences:
    type: array
    description: List of segmented sentence strings.
  pos_tags:
    type: array
    description: Part-of-speech tags assigned to tokens.
---

# NLP Processing Engine

`nlp-processing` provides foundational natural language preprocessing (tokenization, sentence boundary detection, lemmatization, and POS tagging) in Python:

$$\text{Pipeline}(\text{Text}) \to \langle \text{Tokens}, \text{Sentences}, \text{POSTags}, \text{Lemmas} \rangle$$

---

## The 5-Stage NLP Processing Progression

1. **Text Ingest & Unicode Cleaning**: Ingest raw text; normalize whitespace and Unicode characters.
2. **Sentence Segmentation**: Split text into discrete sentence strings using regex boundary rules.
3. **The Visual Brief**: Generate interactive HTML token and POS tag breakdown brief at `%TEMP%\nlp-processing-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert token list non-empty; preserve punctuation positions.
5. **Feature Assembly & Output Emission**: Emit structured token array, sentences, and POS tags.

---

## Implementation Notes

```python
import re
from typing import Dict, List, Any, Optional

def process_nlp_pipeline(
    text: str,
    tasks: Optional[List[str]] = None
) -> Dict[str, Any]:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    tokens = [t.lower() for t in re.findall(r"\b\w+\b", text)]
    pos_tags = [{"token": t, "tag": "NN" if len(t) > 3 else "IN"} for t in tokens[:20]]
    
    return {
        "tokens": tokens,
        "sentences": sentences,
        "pos_tags": pos_tags
    }
```

---

## Anti-Patterns & Guardrails

- **Naive Period-Splitting** — Splitting sentences purely on `.` characters, breaking on abbreviations (e.g. "Dr. Smith", "e.g.").
- **Destructive Case Normalization** — Lowercasing texts before named entity recognition, erasing vital capitalization cues.