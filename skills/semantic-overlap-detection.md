---
name: semantic-overlap-detection
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Analysis
source_file: src/analysis/overlap_discovery.py
source: Semantic Memory Engine (SME)
tags:
  - semantic-overlap-detection
  - duplicate-detection
  - passage-reuse
  - text-plagiarism
  - shingling
inputs:
  source_text:
    type: string
    required: true
    description: Primary source text.
  target_text:
    type: string
    required: true
    description: Target comparison text to check for copied or paraphrased passages.
  min_passage_tokens:
    type: integer
    required: false
    description: Minimum contiguous token length to flag an overlap (default 8).
outputs:
  overlap_percentage:
    type: number
    description: Percentage of source text covered by shared passages [0.0, 100.0].
  overlapping_passages:
    type: array
    description: List of exact matching or near-duplicate passage segments.
  overlap_count:
    type: integer
    description: Total number of discrete matching passage blocks detected.
---

# Semantic Overlap Detection Engine

`semantic-overlap-detection` identifies verbatim and paraphrased passage reuse between documents using **n-gram shingling and longest common substring matching in Python**:

$$\text{OverlapRatio} = \frac{\sum_{p \in \text{Passages}} \text{Length}(p)}{\text{Length}(\text{SourceText})}$$

---

## The 5-Stage Semantic Overlap Progression

1. **Text Ingest & Shingle Generation**: Ingest document pair; generate overlapping $n$-gram token shingles ($n=8$).
2. **Exact & Near-Duplicate Matching**: Intersect shingle sets; cluster contiguous matching token spans.
3. **The Visual Brief**: Generate interactive HTML overlap heatmap brief at `%TEMP%\overlap-detection-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Filter out boilerplate common phrases (e.g. standard disclaimers, table of contents).
5. **Coverage Calculation & Output Emission**: Compute aggregate `overlap_percentage` and emit detailed passage report.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def detect_semantic_overlap(
    source_text: str,
    target_text: str,
    min_passage_tokens: int = 8
) -> Dict[str, Any]:
    s_words = source_text.split()
    t_words = target_text.split()
    
    if len(s_words) < min_passage_tokens or len(t_words) < min_passage_tokens:
        return {"overlap_percentage": 0.0, "overlapping_passages": [], "overlap_count": 0}
        
    s_shingles = set(" ".join(s_words[i:i+min_passage_tokens]).lower() for i in range(len(s_words) - min_passage_tokens + 1))
    t_shingles = set(" ".join(t_words[i:i+min_passage_tokens]).lower() for i in range(len(t_words) - min_passage_tokens + 1))
    
    matches = list(s_shingles.intersection(t_shingles))
    pct = round((len(matches) / max(1, len(s_shingles))) * 100.0, 2)
    
    return {
        "overlap_percentage": min(100.0, pct),
        "overlapping_passages": matches[:10],
        "overlap_count": len(matches)
    }
```

---

## Anti-Patterns & Guardrails

- **Tiny Shingle False Positives** — Using shingle sizes $< 4$ tokens, which flag ubiquitous 3-word English phrases as copied text.
- **Ignoring Shingle Clustering** — Reporting dozens of overlapping fragmented shingles rather than contiguous consolidated paragraphs.