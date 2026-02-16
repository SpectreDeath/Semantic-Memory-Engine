# 🕸️ Layer 0: The Harvester - Integration Guide

## Overview

**The Harvester** is a multi-engine web scraping system that sits at **Layer 0** of the SimpleMem pipeline—**before semantic compression**. It converts messy HTML into clean, LLM-ready markdown for efficient processing by the Loom module.

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Layer 0: HARVESTER (5 tools)                                   │
│  ├─ fetch_semantic_markdown()        ← URL → Clean Markdown    │
│  ├─ deep_crawl_domain()              ← Recursive link discovery │
│  ├─ extract_structured_data()        ← Tables/Forms/JSON-LD    │
│  ├─ bypass_dynamic_content()         ← JS-heavy SPA handling    │
│  └─ archive_to_centrifuge()          ← Store for Loom pipeline  │
│                ▼                                                 │
│  Layer 1: [Future expansion]                                    │
│                ▼                                                 │
│  Layer 2: LOOM (Semantic Compression - 30x)                    │
│  ├─ distill_web_content()            ← Markdown → Atomic facts │
│  ├─ extract_atomic_facts()           ← Granular fact extraction │
│  ├─ resolve_coreferences()           ← Pronoun → Name linking  │
│  └─ compress_semantic_data()         ← Deduplication           │
│                ▼                                                 │
│  Layer 3: SYNAPSE (Memory Consolidation)                        │
│  ├─ create_memory_concept()          ← Background consolidation │
│  ├─ find_similar_memories()          ← Cluster detection       │
│  └─ consolidate_during_idle()        ← Async processing        │
│                ▼                                                 │
│  Layer 5: SCOUT (Adaptive Retrieval)                            │
│  ├─ deep_search()                    ← Triggers Harvester crawl │
│  ├─ estimate_query_complexity()      ← Determines depth needed  │
│  └─ adaptive_retrieval()             ← Smart fact selection    │
│                ▼                                                 │
│  Layer 7: BEACON (Visualization)                                │
│  └─ Real-time trend monitoring & alerts                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 The Deep Knowledge Loop

### Scenario: Scout Identifies a Knowledge Gap

**Workflow:**

1. **Query Triggers Scout**
   ```
   User Query: "What's the latest research on emergent AI capabilities?"
   Scout.estimate_query_complexity() → 7/10 (Deep search needed)
   ```

2. **Scout Triggers Harvester**
   ```python
   from harvester_crawler import HarvesterCrawler
   
   harvester = HarvesterCrawler()
   crawl_result = harvester.deep_crawl_domain(
       seed_url="https://arxiv.org/latest?cat=cs.AI",
       max_depth=2,
       max_pages=20
   )
   # Returns: 20 research papers → Centrifuge DB
   ```

3. **Harvester Populates Database**
   - Extracts metadata (title, abstract, links)
   - Converts PDF abstracts → markdown
   - Marks as `processed_by_loom = False`

4. **Loom Processes Raw Content**
   ```python
   from semantic_loom import SemanticLoom
   
   loom = SemanticLoom()
   for url in centrifuge_db.get_unprocessed_urls():
       raw_content = centrifuge_db.get_raw_content(url)
       facts = loom.distill_web_content(raw_content['markdown'])
       loom.store_atomic_facts(facts, url)
   ```
   - Result: 20 papers → ~1000 atomic facts (30x compression)

5. **Synapse Consolidates**
   ```python
   from memory_synapse import MemorySynapse
   
   synapse = MemorySynapse()
   synapse.consolidate_during_idle()  # Background task
   # Merges similar facts, creates concepts
   ```

6. **Beacon Visualizes Trends**
   - New "AI Capabilities" cluster detected
   - Dashboard shows 15 new concepts
   - Escalation alerts if contradictions found

---

## 🛠️ Tool Breakdown

### Tool 1: `fetch_semantic_markdown(url, js_render, wait_for)`

**Purpose:** Convert single URL to LLM-ready markdown.

**When to use:**
- Fetching a single research paper
- Extracting blog post content
- Getting news article text
- Processing documentation pages

**Example:**

```python
from harvester_crawler import HarvesterCrawler

harvester = HarvesterCrawler()

result = harvester.fetch_semantic_markdown(
    url="https://arxiv.org/abs/2301.13688",
    js_render=False,  # No JS needed for static pages
    wait_for=None
)

print(result['metadata']['word_count'])  # 250 words
print(result['quality_score'])            # 92/100
print(result['markdown'][:500])           # Clean markdown preview
```

**Output Structure:**
```json
{
  "url": "https://...",
  "markdown": "# Title\n\nContent...",
  "html": "<html>...",
  "metadata": {
    "title": "Paper Title",
    "description": "Abstract...",
    "has_js": false,
    "content_type": "article",
    "word_count": 250,
    "engine": "crawl4ai"
  },
  "quality_score": 92,
  "engine_used": "crawl4ai",
  "status": "success"
}
```

**Engine Selection Logic:**
- ✅ `crawl4ai` (Primary): LLM-optimized, automatic pruning, JS support
- 🔄 `scrapling` (Fallback): 700x faster than BeautifulSoup
- 🎬 `playwright` (SPA): Full browser control for complex sites
- 📄 `beautifulsoup` (Static): Lightweight for static HTML

**Performance:**
- Static pages: 200-500ms
- Dynamic pages: 2-5s (includes JS rendering)
- Cached hits: <10ms

---

### Tool 2: `deep_crawl_domain(seed_url, max_depth, max_pages, parallel_workers)`

**Purpose:** Recursively crawl entire domain starting from seed URL.

**When to use:**
- Scout detects knowledge gap requiring comprehensive coverage
- Building domain knowledge base
- Competitive research on entire website
- Documentation site indexing

**Example:**

```python
result = harvester.deep_crawl_domain(
    seed_url="https://arxiv.org/list/cs.AI/recent",
    max_depth=2,
    max_pages=50,
    parallel_workers=4
)

# Returns:
# {
#   "domain": "arxiv.org",
#   "total_pages_crawled": 47,
#   "crawled_urls": ["https://...", ...],
#   "frontier": ["https://...", ...],  # Next level to crawl
#   "failed_urls": {"https://...": "Timeout"},
#   "content_summary": {
#     "avg_quality": 89,
#     "content_types": {"article": 45, "video": 2},
#     "total_words": 45000
#   },
#   "processing_time_s": 120
# }
```

**BFS Traversal Algorithm:**

```
Level 1 (seed):     1 URL (https://arxiv.org/list/cs.AI/recent)
                    ↓
Level 2:            8 URLs (direct links from seed)
                    ↓
Level 3:            40 URLs (links from Level 2)
                    ↓
Total:              49 URLs (capped at max_pages=50)
```

**Integration with Scout:**

```python
from adaptive_scout import AdaptiveScout
from harvester_crawler import HarvesterCrawler

scout = AdaptiveScout()
harvester = HarvesterCrawler()

# Scout identifies gap
query = "emergent AI capabilities in 2024"
complexity = scout.estimate_query_complexity(query)  # 8/10

if complexity >= 7:
    # Deep crawl needed
    crawl_result = harvester.deep_crawl_domain(
        seed_url="https://scholar.google.com/scholar?q=" + query,
        max_depth=3,
        max_pages=100  # Comprehensive
    )
    
    # Archive all to Centrifuge
    for url in crawl_result['crawled_urls']:
        harvester.archive_to_centrifuge(url)
```

**Performance:**
- 50 pages: ~120 seconds (parallel 4 workers)
- ~600KB HTML per page → compressed to 30KB markdown average

---

### Tool 3: `extract_structured_data(url, schema_hints)`

**Purpose:** Extract tables, forms, JSON-LD, microdata from page.

**When to use:**
- Loom needs structured facts (not just prose)
- Extracting research datasets
- Pulling comparison tables
- Getting financial/statistical data

**Example:**

```python
result = harvester.extract_structured_data(
    url="https://example.com/ai-benchmarks",
    schema_hints=["Dataset", "BenchmarkData"]
)

# Returns:
# {
#   "tables": [
#     {
#       "headers": ["Model", "Accuracy", "Speed"],
#       "rows": [
#         ["GPT-4", "95.2%", "2.1s"],
#         ["Claude", "94.8%", "1.9s"]
#       ]
#     }
#   ],
#   "forms": [...],
#   "json_ld": [{
#     "@type": "Dataset",
#     "@context": "https://schema.org",
#     "name": "AI Benchmark 2024",
#     "url": "https://..."
#   }],
#   "microdata": {...},
#   "extracted_structure": {
#     "table_count": 5,
#     "form_count": 2,
#     "json_ld_count": 3
#   },
#   "status": "success"
# }
```

**Loom Integration:**

```python
from semantic_loom import SemanticLoom

loom = SemanticLoom()

# Extract structured data
structure = harvester.extract_structured_data(url)

# Convert tables → atomic facts
for table in structure['tables']:
    facts = loom.extract_atomic_facts_from_table(table)
    # Fact: "Model=GPT-4, Accuracy=95.2%, Speed=2.1s"
```

**Output Formats:**
- Tables → CSV-like rows + headers
- Forms → JSON schema
- JSON-LD → Raw JSON
- Microdata → Flattened dict

---

### Tool 4: `bypass_dynamic_content(url, wait_selector, scroll_to_bottom, interaction_script)`

**Purpose:** Handle JavaScript-heavy sites, SPAs, infinite scroll.

**When to use:**
- Fetching from React/Vue/Angular apps
- Infinite scroll pages (Twitter, Medium)
- Behind interactive paywalls
- Video platform metadata

**Example:**

```python
result = harvester.bypass_dynamic_content(
    url="https://twitter.com/search?q=AI%20safety",
    wait_selector=".tweet",           # Wait for tweets to load
    scroll_to_bottom=True,             # Load all lazy content
    interaction_script=None            # No custom clicks needed
)

# Returns:
# {
#   "url": "https://...",
#   "html": "<html>... (fully rendered)",
#   "markdown": "# Search Results\n\nTweet 1...",
#   "js_interactions_applied": [
#     "Waited for: .tweet",
#     "Scrolled to bottom"
#   ],
#   "dynamic_content_detected": true,
#   "performance": {
#     "load_time_ms": 3200
#   },
#   "status": "success"
# }
```

**Complex SPA Example:**

```python
# YouTube-like interface requiring expansion clicks
result = harvester.bypass_dynamic_content(
    url="https://example.com/interactive-dashboard",
    wait_selector=".data-loaded",
    interaction_script="document.querySelectorAll('.expand').forEach(el => el.click())"
)
```

**Performance Profiles:**
- Static pages: 100-300ms
- Dynamic pages: 2-5s
- SPA with interactions: 5-15s
- Infinite scroll to bottom: 10-20s

---

### Tool 5: `archive_to_centrifuge(url, overwrite)`

**Purpose:** Store raw content to Centrifuge DB, marking ready for Loom pipeline.

**When to use:**
- After fetch/crawl/structure extraction
- Bulk import from other tools
- Persistent storage for offline processing
- Integration point between Harvester and Loom

**Example:**

```python
# Single URL
result = harvester.archive_to_centrifuge(
    url="https://arxiv.org/abs/2301.13688",
    overwrite=False  # Don't re-fetch if already cached
)

print(result['record_id'])        # 42
print(result['markdown_words'])   # 2500
print(result['ready_for_loom'])   # True

# Batch archive (from crawl results)
crawl_result = harvester.deep_crawl_domain("https://...")
for url in crawl_result['crawled_urls']:
    harvester.archive_to_centrifuge(url)
```

**Database Schema (raw_content table):**

```sql
CREATE TABLE raw_content (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    domain TEXT,
    raw_html TEXT,
    markdown_content TEXT,        -- For Loom input
    extracted_schema JSON,        -- Metadata
    content_type TEXT,            -- 'article', 'table', 'json', 'video'
    js_required BOOLEAN,
    timestamp DATETIME,
    processed_by_loom BOOLEAN,    -- Pipeline marker
    source_quality INTEGER,       -- 0-100 score
    fetch_method TEXT             -- 'crawl4ai', 'scrapling', etc.
);
```

**Pipeline Integration:**

```python
# Loom polls for unprocessed content
SELECT url, markdown_content 
FROM raw_content 
WHERE processed_by_loom = FALSE 
AND source_quality >= 70 
ORDER BY timestamp DESC 
LIMIT 50;

# After Loom processes:
UPDATE raw_content 
SET processed_by_loom = TRUE 
WHERE id = ?;
```

---

## 🔄 Engine Selection Strategy

### Crawl4AI (Primary) 
✅ **Best for:** General web content, LLM pipelines
- Automatic HTML pruning (removes nav, footer, ads)
- JavaScript rendering built-in
- Schema.org detection
- Optimized for markdown output

```python
harvester = HarvesterCrawler(use_crawl4ai=True)
```

### Scrapling (Fallback)
✅ **Best for:** Speed-critical, high-volume scraping
- 700x faster than BeautifulSoup (benchmarked)
- Built-in MCP server
- Undetectable (rotates UA, manages cookies)
- Lower memory footprint

```python
# Auto-fallback if Crawl4AI unavailable
harvester = HarvesterCrawler()  # Falls back to Scrapling
```

### Playwright (SPA/Complex)
✅ **Best for:** Single-page apps, dynamic content
- Full Chromium browser control
- Custom JavaScript execution
- Screenshot capability
- Session management

```python
# Force Playwright for complex SPA
result = harvester.bypass_dynamic_content(
    url="https://complex-spa.example.com",
    wait_selector=".content-loaded"
)
```

### BeautifulSoup (Emergency)
✅ **Best for:** Static HTML, minimal dependencies
- Zero external dependencies
- Lightweight processing
- HTML parsing only (no JS)

---

## 📊 Performance Optimization

### RAM Usage (32GB Available)

```
Parallel Workers Analysis:
├─ 1 worker:   ~500MB  (1 browser instance)
├─ 2 workers:  ~1GB    (2 browser instances)
├─ 4 workers:  ~2GB    (4 browser instances) ← RECOMMENDED
└─ 8 workers:  ~4GB    (8 browser instances)

Your Setup: 32GB RAM
├─ Harvester (parallel):    ~2GB
├─ Loom (semantic compress):  ~4GB (GPU-accelerated)
├─ System/OS:                 ~8GB
└─ Headroom:                  ~18GB ✅ Comfortable
```

### CPU/GPU Balance

```
Harvester: CPU/RAM-intensive
├─ HTML parsing: CPU 40%
├─ JS rendering: CPU 60%
└─ GPU: Idle ✅ (doesn't block Loom)

Loom: GPU-intensive
├─ Semantic compression: GPU 80%
├─ CPU: Light (20%)
└─ Can run parallel to Harvester ✅
```

### Caching Strategy

```python
# Check cache first (avoid re-fetching)
cached = harvester._check_cache(url)

# Archive hit = <10ms retrieval
result = harvester.archive_to_centrifuge(url, overwrite=False)

# First fetch = 500ms-5s, then cached forever
```

---

## 🚀 Deployment Pattern

### Single URL Pipeline

```python
from harvester_crawler import HarvesterCrawler
from semantic_loom import SemanticLoom

harvester = HarvesterCrawler()
loom = SemanticLoom()

# 1. Fetch
fetch = harvester.fetch_semantic_markdown("https://...")

# 2. Archive
archive = harvester.archive_to_centrifuge("https://...")

# 3. Process
facts = loom.distill_web_content(fetch['markdown'])

# 4. Store
loom.store_atomic_facts(facts, "https://...")

print(f"✅ {len(facts)} atomic facts extracted")
```

### Domain Crawl Pipeline

```python
# 1. Deep crawl
crawl = harvester.deep_crawl_domain(
    seed_url="https://example.com",
    max_pages=100
)

# 2. Batch archive
for url in crawl['crawled_urls']:
    harvester.archive_to_centrifuge(url)

# 3. Loom processes batch (async)
loom.batch_process_centrifuge_content(limit=50)

# 4. Beacon visualizes
# New concepts appear on dashboard in real-time
```

### Scout Integration (Knowledge Gap Closing)

```python
from adaptive_scout import AdaptiveScout

scout = AdaptiveScout()

# Scout finds gap
query = "latest AI safety research"
gap_severity = scout.estimate_query_complexity(query)

if gap_severity >= 7:
    # Harvester closes it
    crawl = harvester.deep_crawl_domain(
        seed_url=scout.find_best_source(query),
        max_pages=50
    )
    
    # Archive → Loom → Synapse → Beacon
    for url in crawl['crawled_urls']:
        harvester.archive_to_centrifuge(url)
    
    # Async background processing
    loom.batch_process_centrifuge_content()
```

---

## 📋 Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt

# Or selective install:
pip install crawl4ai scrapling playwright beautifulsoup4
```

### 2. Initialize Database

```python
from harvester_crawler import HarvesterCrawler

harvester = HarvesterCrawler()
# Creates raw_content table automatically
```

### 3. Test Harvesters

```bash
# Quick validation
python harvester_crawler.py

# Expected output:
# 🕸️ Harvester initialized with engine: crawl4ai
```

---

## ⚠️ Anti-Bot Handling

**Harvester Features:**
- User-Agent rotation (Scrapling)
- Random delays between requests
- Respects robots.txt
- Session/cookie management
- Proxy support (optional)

**Best Practices:**
- Add 1-2 second delays between requests
- Use rotating proxies for high-volume crawling
- Check site's ToS before crawling
- Implement rate limiting

```python
# Rate limiting example
import time

for url in urls:
    result = harvester.fetch_semantic_markdown(url)
    time.sleep(random.uniform(1, 2))  # Random 1-2s delay
```

---

## 🔗 Integration Checklist

- [ ] Install `requirements.txt` with Harvester dependencies
- [ ] Test `fetch_semantic_markdown()` on sample URL
- [ ] Verify `raw_content` table created in Centrifuge DB
- [ ] Test `deep_crawl_domain()` on known domain
- [ ] Verify content cached properly
- [ ] Connect Scout → Harvester trigger
- [ ] Connect Harvester → Loom pipeline
- [ ] Monitor performance (timing, memory, quality scores)
- [ ] Enable Beacon dashboard to visualize new content
- [ ] Test end-to-end: Scout gap → Harvester crawl → Loom facts → Beacon visualization

---

## 📞 Troubleshooting

**Issue:** "Crawl4AI not available"
→ **Solution:** Install `pip install crawl4ai` (or let it auto-fallback to Scrapling)

**Issue:** "Playwright timeout on SPA"
→ **Solution:** Use `wait_selector` parameter to wait for specific element:
```python
bypass_dynamic_content(url, wait_selector=".main-content")
```

**Issue:** High memory usage with 4 workers
→ **Solution:** Reduce to `parallel_workers=2` or add delays between requests

**Issue:** Anti-bot blocks (403 Forbidden)
→ **Solution:** Use Scrapling instead (undetectable), add delays, or use proxies

---

## 📊 Metrics to Monitor

```
harvester_result = fetch_semantic_markdown(url)

Metrics:
├─ processing_time_ms    (Should be <5000ms)
├─ quality_score         (Should be >70)
├─ word_count            (Should be >50)
├─ has_js                (True/False, indicates complexity)
└─ engine_used           (Which engine succeeded)

Dashboard Query:
SELECT 
  AVG(processing_time_ms) as avg_time,
  AVG(source_quality) as avg_quality,
  COUNT(*) as total_processed
FROM raw_content
WHERE timestamp > datetime('now', '-24 hours');
```

---

**Status:** ✅ Ready for production deployment
**Next Steps:** Install deps, test on known URLs, integrate with Scout workflow
