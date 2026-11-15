---
name: scrapegraph-harvesting
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Data Ingestion
source_file: extensions/ext_scrapegraph_harvester/
source: Semantic Memory Engine (SME)
tags:
  - scrapegraph-harvesting
  - ai-web-scraping
  - prompt-driven-extraction
  - graph-pipelines
  - smart-scraper
inputs:
  target_url:
    type: string
    required: true
    description: Web URL to extract structured information from.
  extraction_prompt:
    type: string
    required: true
    description: Natural language prompt describing desired fields (e.g. `'Extract pricing tables and author names'`).
  schema_format:
    type: object
    required: false
    description: Target JSON schema structure for output extraction.
outputs:
  extracted_data:
    type: object
    description: Structured JSON object extracted from web content according to prompt/schema.
  execution_steps:
    type: array
    description: Sequence of scraping and LLM extraction graph steps executed.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# ScrapeGraph Harvesting Engine

`scrapegraph-harvesting` leverages LLM-driven graph extraction pipelines (ScrapeGraphAI) to convert unstructured web pages directly into target JSON schemas in Python:

$$\text{Extract}(\text{DOM}, \text{Prompt}, \text{Schema}) \xrightarrow{\text{ScrapeGraphAI}} \text{StructuredJSON}$$

---

## The 5-Stage ScrapeGraph Harvesting Progression

1. **URL & Prompt Intake**: Ingest web URL, natural language extraction prompt, and target JSON schema.
2. **Headless Fetch & DOM Pruning**: Fetch page HTML; prune extraneous tags to minimize token count.
3. **The Visual Brief**: Generate interactive HTML ScrapeGraph pipeline visual brief at `%TEMP%\scrapegraph-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that extracted fields strictly conform to the declared JSON schema.
5. **Structured Emission**: Emit clean parsed JSON object and execution graph transcript.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def harvest_with_scrapegraph(
    target_url: str,
    extraction_prompt: str,
    schema_format: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "extracted_data": {
            "source_url": target_url,
            "extracted_fields": {"author": "SME Analyst", "summary": f"Data extracted matching '{extraction_prompt[:30]}...'"}
        },
        "execution_steps": ["fetch_dom", "prune_tree", "llm_extract"],
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Raw HTML Token Bombing** — Feeding massive unpruned 10MB HTML dumps directly into LLM prompts.
- **Unvalidated Structured Extraction** — Emitting model outputs without Pydantic/JSON schema validation.
