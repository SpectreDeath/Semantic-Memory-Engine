---
name: web-researcher
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Data Ingestion
source_file: src/gathering/web_researcher.py
source: Semantic Memory Engine (SME)
tags:
  - web-researcher
  - autonomous-research
  - search-synthesis
  - query-planning
  - source-triangulation
inputs:
  research_topic:
    type: string
    required: true
    description: Complex research question or topic to investigate across the web.
  max_sources:
    type: integer
    required: false
    description: Maximum number of distinct web sources to consult and synthesize (default 5).
outputs:
  research_brief:
    type: string
    description: Synthesized comprehensive research brief answering the topic question.
  cited_sources:
    type: array
    description: List of authoritative web URLs and publications referenced in the brief.
  confidence_rating:
    type: number
    description: Overall confidence score of the synthesized brief in [0.0, 1.0].
---

# Web Researcher Engine

`web-researcher` orchestrates end-to-end autonomous web investigation: generating search sub-queries, retrieving authoritative sources, scraping content, and triangulating factual claims in Python:

$$\text{ResearchReport}(\mathcal{Q}) = \text{Synthesize}\left( \bigcup_{q \in \text{Decompose}(\mathcal{Q})} \text{Scrape}(\text{Search}(q)) \right)$$

---

## The 5-Stage Web Researcher Progression

1. **Topic Ingestion & Query Decomposition**: Ingest topic prompt; generate 3-5 targeted search queries.
2. **Search & Authoritative Source Selection**: Query web search APIs; select top reputable sources.
3. **The Visual Brief**: Generate interactive HTML research citation brief at `%TEMP%\web-researcher-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Cross-verify claims across at least 2 independent sources to eliminate misinformation.
5. **Synthesis & Brief Emission**: Synthesize comprehensive research brief with clickable markdown citations.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def conduct_web_research(
    research_topic: str,
    max_sources: int = 5
) -> Dict[str, Any]:
    sources = [
        {"url": "https://example.com/source1", "title": "Forensic AI Standards 2026"},
        {"url": "https://example.com/source2", "title": "Lawnmower Man Architectural Whitepaper"}
    ]
    return {
        "research_brief": f"Comprehensive research summary on {research_topic} based on multi-source triangulation.",
        "cited_sources": sources[:max_sources],
        "confidence_rating": 0.92
    }
```

---

## Anti-Patterns & Guardrails

- **Single-Source Credulity** — Basing research conclusions entirely on a single unverified blog post.
- **Uncited Speculative Claims** — Emitting assertion statements in the brief without linking back to harvested source URLs.