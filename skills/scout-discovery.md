---
name: scout-discovery
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Query
source_file: src/query/scout.py
source: Semantic Memory Engine (SME)
tags:
  - scout-discovery
  - autonomous-exploration
  - exploratory-search
  - entity-expansion
  - graph-crawling
inputs:
  seed_entities:
    type: array
    required: true
    description: Initial starting entities or seed URLs for discovery exploration.
  max_depth:
    type: integer
    required: false
    description: Maximum hop distance from seed nodes $D \ge 1$ (default 2).
  relevance_threshold:
    type: number
    required: false
    description: Minimum semantic cosine similarity to continue traversing links (default 0.60).
outputs:
  discovered_nodes:
    type: array
    description: List of newly discovered entities and related concepts.
  traversal_graph:
    type: object
    description: Traversed graph topology including discovery sequence and hop distances.
  frontier_size:
    type: integer
    description: Count of unexplored boundary candidates remaining in the queue.
---

# Scout Discovery Engine

`scout-discovery` performs autonomous, guided exploration across local knowledge graphs and external information frontiers in Python:

$$\text{NextNode} = \arg\max_{v \in \text{Frontier}} \left( \text{Relevance}(v, \text{Goal}) \cdot e^{-\lambda \cdot \text{Depth}(v)} \right)$$

---

## The 5-Stage Scout Discovery Progression

1. **Seed Ingest & Priority Queue Setup**: Ingest seed entities; initialize best-first exploration priority queue.
2. **Hop Expansion & Link Evaluation**: Expand outgoing relationships; evaluate cosine relevance for candidate nodes.
3. **The Visual Brief**: Generate interactive HTML discovery expansion radar at `%TEMP%\scout-discovery-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Prune branches with relevance $< \theta$ or depth $> D_{\text{max}}$.
5. **Graph Synthesis & Output Emission**: Compile discovered node list and emit full `ScoutExplorationReport`.

---

## Implementation Notes

```python
import collections
from typing import Dict, List, Any, Optional

def run_scout_discovery(
    seed_entities: List[str],
    max_depth: int = 2,
    relevance_threshold: float = 0.60
) -> Dict[str, Any]:
    discovered = []
    frontier = collections.deque([(s, 0) for s in seed_entities])
    visited = set(seed_entities)
    
    while frontier:
        curr, depth = frontier.popleft()
        discovered.append({"entity": curr, "depth": depth, "relevance": 0.85 - (depth * 0.1)})
        
        if depth < max_depth:
            # Simulate neighbor expansion
            neighbors = [f"{curr}_sub_{i}" for i in range(2)]
            for nbr in neighbors:
                if nbr not in visited:
                    visited.add(nbr)
                    frontier.append((nbr, depth + 1))
                    
    return {
        "discovered_nodes": discovered,
        "traversal_graph": {"root": seed_entities, "total_visited": len(visited)},
        "frontier_size": len(frontier)
    }
```

---

## Anti-Patterns & Guardrails

- **Unconstrained Exponential Branching** — Expanding high-degree hub nodes without degree capping, overwhelming exploration memory.
- **Topical Drift** — Continuing exploration past several hops when relevance drops below the threshold.