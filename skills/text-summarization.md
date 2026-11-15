---
name: text-summarization
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Analysis
source_file: src/core/text_summarizer.py
source: Semantic Memory Engine (SME)
tags:
  - text-summarization
  - extractive-summarization
  - abstractive-summarization
  - key-point-extraction
  - compression-ratio
inputs:
  document_text:
    type: string
    required: true
    description: Input document or corpus to summarize.
  summary_type:
    type: string
    required: false
    description: Mode (`'extractive'`, `'abstractive'`, `'bullet_points'`, default `'abstractive'`).
  max_length_words:
    type: integer
    required: false
    description: Target length ceiling for the generated summary (default 150).
outputs:
  summary_text:
    type: string
    description: Concise, coherent summary of the primary document arguments and findings.
  key_takeaways:
    type: array
    description: Bulleted list of salient conclusions and takeaways.
  compression_ratio:
    type: number
    description: Ratio of summary length to original document length in [0.0, 1.0].
---

# Text Summarization Engine

`text-summarization` distills lengthy multi-page reports into concise executive summaries and key takeaways using **extractive TextRank and abstractive LLM synthesis in Python**:

$$\text{Summary} = \arg\max_{S \subset D, |S| \le L} \left( \text{Coverage}(S, D) - \lambda \cdot \text{Redundancy}(S) \right)$$

---

## The 5-Stage Text Summarization Progression

1. **Document Intake & Chunking**: Ingest document text; segment into coherent paragraph chunks if exceeding context limits.
2. **Salience & TextRank Scoring**: Score sentence importance based on central entity connectivity and graph centrality.
3. **The Visual Brief**: Generate interactive HTML summary compression brief at `%TEMP%\summarization-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that key numeric metrics and central forensic findings are preserved without factual distortion.
5. **Synthesis & Output Emission**: Generate coherent summary text and extract top 3-5 bulleted takeaways.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def summarize_text(
    document_text: str,
    summary_type: str = "abstractive",
    max_length_words: int = 150
) -> Dict[str, Any]:
    words = document_text.split()
    orig_len = len(words)
    
    # Mock summarization
    summary = " ".join(words[:min(max_length_words, len(words))]) + "..." if len(words) > max_length_words else document_text
    ratio = round(len(summary.split()) / max(1, orig_len), 3)
    
    return {
        "summary_text": summary,
        "key_takeaways": ["Primary finding extracted", "Key conclusion summarized"],
        "compression_ratio": ratio
    }
```

---

## Anti-Patterns & Guardrails

- **Hallucinated Key Figures** — Introducing synthetic numerical figures or statistics not present in the original document.
- **Extreme Over-Compression** — Summarizing a 50-page complex legal report into a single generic sentence that omits critical qualifications.