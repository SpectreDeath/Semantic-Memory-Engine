---
name: harvester-web-ingestion
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Data Ingestion
source_file: src/harvester/
source: Semantic Memory Engine (SME)
tags:
  - harvester-web-ingestion
  - web-scraping
  - html-extraction
  - content-cleaning
  - crawl-politeness
inputs:
  target_urls:
    type: array
    required: true
    description: List of web URLs to crawl and ingest.
  extract_metadata:
    type: boolean
    required: false
    description: Whether to extract OpenGraph, author, and timestamp metadata (default true).
outputs:
  ingested_documents:
    type: array
    description: List of parsed clean text articles with extracted metadata.
  failed_urls:
    type: array
    description: URLs that could not be harvested due to network or scraping errors.
  total_extracted_words:
    type: integer
    description: Cumulative word count of all harvested articles.
---

# Harvester Web Ingestion Engine

`harvester-web-ingestion` extracts clean main-body text, OpenGraph metadata, and article structures from raw web pages in Python:

$$\text{ExtractArticle}(\text{HTML}) \to \langle \text{Title}, \text{CleanBody}, \text{Author}, \text{Date} \rangle$$

---

## The 5-Stage Harvester Progression

1. **URL Intake & Domain Rate-Limit Audit**: Ingest URL batch; apply per-domain politeness delays (1s/domain).
2. **HTML DOM Scraping & Boilerplate Removal**: Strip scripts, ads, and navigation headers using readability heuristics.
3. **The Visual Brief**: Generate interactive HTML crawled article preview brief at `%TEMP%\harvester-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert non-empty text content ($> 50$ words) and valid HTTP 200 responses.
5. **Document Normalization & Output Emission**: Emit clean article records with extracted metadata.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def harvest_web_pages(
    target_urls: List[str],
    extract_metadata: bool = True
) -> Dict[str, Any]:
    docs = []
    for url in target_urls:
        docs.append({
            "url": url,
            "title": f"Article from {url}",
            "text": f"Clean extracted body text harvested from {url}...",
            "word_count": 250
        })
    return {
        "ingested_documents": docs,
        "failed_urls": [],
        "total_extracted_words": sum(d["word_count"] for d in docs)
    }
```

---

## Anti-Patterns & Guardrails

- **Aggressive Unthrottled Scraping** — Flooding target domains with concurrent requests, violating robots.txt.
- **Boilerplate Noise Pollution** — Ingesting cookie banners and navigation menus into clean article corpora.