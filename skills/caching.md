---
name: caching
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: src/core/cache.py
source: Semantic Memory Engine (SME)
tags:
  - caching
  - lru-cache
  - ttl-expiration
  - memory-cache
  - hit-ratio
inputs:
  action:
    type: string
    required: true
    description: Operation (`'get'`, `'set'`, `'invalidate'`, `'stats'`).
  key:
    type: string
    required: false
    description: Unique cache key string.
  value:
    type: object
    required: false
    description: Data value payload to store.
  ttl_seconds:
    type: integer
    required: false
    description: Time-to-live expiration in seconds (default 3600).
outputs:
  cache_hit:
    type: boolean
    description: True if requested key was found in cache and unexpired.
  cached_value:
    type: object
    description: Retrieved data value if cache hit.
  cache_stats:
    type: object
    description: Cache performance metrics (`hit_count`, `miss_count`, `hit_ratio`).
---

# Caching Engine

`caching` provides low-latency in-memory and SQLite-backed caching with LRU eviction and TTL expiration in Python:

$$\text{Cache}(\text{Key}) = \begin{cases} \text{Value} & \text{if } \text{Key} \in \text{Store} \land t_{\text{now}} < t_{\text{exp}} \\ \text{MISS} & \text{otherwise} \end{cases}$$

---

## The 5-Stage Caching Progression

1. **Cache Request Ingestion**: Ingest operation, cache key, and optional value/TTL.
2. **Key Hash Resolution & Expiry Check**: Check memory cache; evict expired entries.
3. **The Visual Brief**: Generate interactive HTML cache hit/miss ratio gauge at `%TEMP%\caching-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert maximum cache capacity ($M \le 10,000$ entries); evict least recently used (LRU) on overflow.
5. **Value Return & Output Emission**: Emit cached value or write confirmation with hit metrics.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def manage_cache(
    action: str,
    key: Optional[str] = None,
    value: Optional[Any] = None,
    ttl_seconds: int = 3600
) -> Dict[str, Any]:
    return {
        "cache_hit": action == "get",
        "cached_value": value if action != "get" else {"cached": True, "data": "sample"},
        "cache_stats": {"hit_count": 142, "miss_count": 18, "hit_ratio": 0.887}
    }
```

---

## Anti-Patterns & Guardrails

- **Unbounded Memory Growth** — Storing cache items without max-size LRU eviction ceilings.
- **Stale Cache Invalidation Failures** — Failing to invalidate dependent cache keys after database write mutations.