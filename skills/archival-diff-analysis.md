---
name: archival-diff-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: extensions/ext_archival_diff/
source: Semantic Memory Engine (SME)
tags:
  - archival-diff-analysis
  - document-evolution
  - text-diffing
  - semantic-shift
  - revision-forensics
inputs:
  baseline_document:
    type: string
    required: true
    description: Initial historical/baseline text version.
  revised_document:
    type: string
    required: true
    description: Subsequent revised version of the document.
  granularity:
    type: string
    required: false
    description: Diff comparison level (`'word'`, `'sentence'`, `'paragraph'`, default `'sentence'`).
outputs:
  similarity_ratio:
    type: number
    description: Overall text similarity coefficient in [0.0, 1.0].
  insertions:
    type: array
    description: List of added content blocks.
  deletions:
    type: array
    description: List of removed content blocks.
  semantic_shift_score:
    type: number
    description: Quantitative metric measuring semantic divergence between versions.
---

# Archival Diff Analysis Engine

`archival-diff-analysis` tracks the temporal evolution and modification history of text artifacts. It computes **syntactic diffs (LCS/Levenshtein) and semantic shift vectors in Python**:

$$\text{Similarity} = \frac{2 \cdot |\text{LCS}(D_1, D_2)|}{|D_1| + |D_2|}, \quad \text{Semantic Shift} = 1 - \cos(\mathbf{e}(D_1), \mathbf{e}(D_2))$$

---

## The 5-Stage Archival Diff Progression

1. **Document Ingest & Normalization**: Tokenize baseline and revised texts into structured semantic blocks according to `granularity`.
2. **Longest Common Subsequence (LCS) Alignment**: Compute optimal string alignment to identify exact additions, deletions, and replacements.
3. **The Visual Brief**: Generate interactive HTML side-by-side diff viewer at `%TEMP%\archival-diff-brief-<timestamp>.html` with green insertion and red deletion highlights.
4. **Mandatory Checkpoint**: Verify semantic coherence; detect stealth redactions or subtle manipulative wording modifications.
5. **Report & Shift Metric Emission**: Calculate composite `semantic_shift_score` and emit structured change log.

---

## Implementation Notes

```python
import difflib
from typing import Dict, List, Any

def compute_archival_diff(
    baseline_document: str,
    revised_document: str,
    granularity: str = "sentence"
) -> Dict[str, Any]:
    b_lines = [s.strip() for s in baseline_document.splitlines() if s.strip()]
    r_lines = [s.strip() for s in revised_document.splitlines() if s.strip()]
    
    matcher = difflib.SequenceMatcher(None, b_lines, r_lines)
    sim_ratio = matcher.ratio()
    
    insertions = []
    deletions = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            insertions.extend(r_lines[j1:j2])
        elif tag == "delete":
            deletions.extend(b_lines[i1:i2])
        elif tag == "replace":
            deletions.extend(b_lines[i1:i2])
            insertions.extend(r_lines[j1:j2])
            
    semantic_shift = round(1.0 - sim_ratio, 4)
    
    return {
        "similarity_ratio": round(sim_ratio, 4),
        "insertions": insertions,
        "deletions": deletions,
        "semantic_shift_score": semantic_shift
    }
```

---

## Anti-Patterns & Guardrails

- **Character-Level Diff Bloat** — Running character-level diffs on large archival corpora, causing massive output payloads and lost semantic context.
- **Ignoring Semantic Equivalence** — Flagging superficial whitespace or punctuation formatting adjustments as substantive document revisions.
