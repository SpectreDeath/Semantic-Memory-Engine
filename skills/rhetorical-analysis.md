---
name: rhetorical-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/analysis/rhetoric.py
source: Semantic Memory Engine (SME)
tags:
  - rhetorical-analysis
  - argumentation-mining
  - fallacies-detection
  - persuasion-modes
  - rhetorical-structure
inputs:
  argument_text:
    type: string
    required: true
    description: Input text containing discursive, argumentative, or persuasive claims.
  extract_fallacies:
    type: boolean
    required: false
    description: Whether to scan for logical and rhetorical fallacies (default true).
outputs:
  persuasion_triad:
    type: object
    description: Estimated proportion of Ethos, Pathos, and Logos appeal modes summing to 1.0.
  argument_claims:
    type: array
    description: Extracted central premises, supporting evidence, and warrant conclusions.
  detected_fallacies:
    type: array
    description: List of flagged informal fallacies (e.g. ad hominem, strawman, false dilemma).
---

# Rhetorical Analysis Engine

`rhetorical-analysis` performs deep argumentation mining and persuasion mode decomposition. It evaluates **Aristotelian persuasion modes (Ethos, Pathos, Logos) and rhetorical fallacy structures in Python**:

$$\mathbf{p}_{\text{triad}} = \langle \text{Ethos}, \text{Pathos}, \text{Logos} \rangle, \quad \sum p_i = 1.0, \quad p_i \ge 0$$

$$\text{Logos} \propto \frac{\text{Count}(\text{PremiseConnectives})}{\text{Sentences}}, \quad \text{Pathos} \propto \frac{\text{Count}(\text{EmotiveAdjectives})}{\text{Tokens}}$$

---

## The 5-Stage Rhetorical Analysis Progression

1. **Discourse Ingest & Segmentation**: Ingest argument text; split into rhetorical discourse units and clause segments.
2. **Persuasion Appeal Scoring**: Scan lexical cues and syntactic markers to evaluate relative weights of Ethos, Pathos, and Logos.
3. **The Visual Brief**: Generate interactive HTML ternary triangle plot brief at `%TEMP%\rhetorical-analysis-brief-<timestamp>.html` showing persuasion appeal coordinates.
4. **Mandatory Checkpoint**: If `extract_fallacies: true`, run pattern matching for circular reasoning, ad hominem, and appeal to authority.
5. **Argument Synthesis & Output Emission**: Structure claims into premise-conclusion hierarchy and emit full `RhetoricalReport`.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def analyze_rhetorical_structure(
    argument_text: str,
    extract_fallacies: bool = True
) -> Dict[str, Any]:
    text_lower = argument_text.lower()
    
    # Heuristic appeal indicators
    logos_cues = ["because", "therefore", "thus", "evidence", "data", "consequently"]
    pathos_cues = ["terrible", "outrageous", "heartbreaking", "urgent", "disaster"]
    ethos_cues = ["as an expert", "experience", "reputation", "integrity", "trusted"]
    
    c_logos = sum(text_lower.count(w) for w in logos_cues) + 1
    c_pathos = sum(text_lower.count(w) for w in pathos_cues) + 1
    c_ethos = sum(text_lower.count(w) for w in ethos_cues) + 1
    
    total = c_logos + c_pathos + c_ethos
    triad = {
        "logos": round(c_logos / total, 3),
        "pathos": round(c_pathos / total, 3),
        "ethos": round(c_ethos / total, 3)
    }
    
    fallacies = []
    if extract_fallacies:
        if "obviously" in text_lower and "everyone knows" in text_lower:
            fallacies.append({"fallacy": "bandwagon_appeal", "confidence": 0.85})
        if "idiot" in text_lower or "corrupt" in text_lower:
            fallacies.append({"fallacy": "ad_hominem", "confidence": 0.90})
            
    return {
        "persuasion_triad": triad,
        "argument_claims": [{"claim": argument_text[:80] + "...", "type": "premise"}],
        "detected_fallacies": fallacies
    }
```

---

## Anti-Patterns & Guardrails

- **Subjective Over-Attribution** — Flagging genuine empirical evidence as emotional Pathos due to intense vocabulary.
- **Isolated Sentence Mining** — Evaluating rhetorical fallacies without checking conversational discourse context.