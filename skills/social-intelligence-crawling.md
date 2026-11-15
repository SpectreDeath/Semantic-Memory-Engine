---
name: social-intelligence-crawling
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: OSINT
source_file: extensions/ext_social_intel/
source: Semantic Memory Engine (SME)
tags:
  - social-intelligence-crawling
  - social-media-mining
  - thread-reconstruction
  - engagement-metrics
  - user-timeline
inputs:
  target_handle:
    type: string
    required: true
    description: Social media username, profile handle, or search hashtag to monitor.
  platform:
    type: string
    required: false
    description: Target platform (`'twitter'`, `'bluesky'`, `'reddit'`, `'mastodon'`, default `'bluesky'`).
  max_posts:
    type: integer
    required: false
    description: Maximum posts/threads to retrieve (default 50).
outputs:
  posts:
    type: array
    description: List of retrieved social posts with text, timestamps, engagement metrics, and thread replies.
  author_metrics:
    type: object
    description: Summary of posting frequency, top hashtags, and interaction velocity.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Social Intelligence Crawling Engine

`social-intelligence-crawling` collects, reconstructs, and analyzes public social media conversations, timelines, and interaction graphs in Python:

$$\text{Timeline}(\text{Handle}) = \{p_t \in \text{PlatformPosts} : \text{Author}(p_t) == \text{Handle} \land t \in [t_0, t_1]\}$$

---

## The 5-Stage Social Intelligence Crawling Progression

1. **Target Handle & Platform Ingestion**: Ingest handle/hashtag and target platform API credentials.
2. **Timeline / Thread Retrieval**: Fetch public posts, replies, and quoted conversations.
3. **The Visual Brief**: Generate interactive HTML social interaction graph brief at `%TEMP%\social-intelligence-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Filter out automated bot spam and deduplicate retweets.
5. **Timeline Aggregation & Output Emission**: Emit structured post array and author activity metrics.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def crawl_social_intelligence(
    target_handle: str,
    platform: str = "bluesky",
    max_posts: int = 50
) -> Dict[str, Any]:
    posts = [
        {
            "id": "post_1",
            "author": target_handle,
            "text": f"Discussing forensic AI standards and Lawnmower Man v3.0 #AI #Security",
            "timestamp": "2026-08-16T14:20:00Z",
            "likes": 15,
            "reposts": 4
        }
    ]
    return {
        "posts": posts,
        "author_metrics": {"total_posts": len(posts), "avg_engagement": 19.0, "top_hashtags": ["#AI", "#Security"]},
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Violating Platform Rate Limits** — Rapid polling of social APIs without backoff, triggering IP blocks.
- **Private Data Scraping** — Attempting to collect non-public private direct messages or restricted account content.