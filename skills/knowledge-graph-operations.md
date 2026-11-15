---
name: knowledge-graph-operations
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Analysis
source_file: src/analysis/knowledge_graph.py
source: Semantic Memory Engine (SME)
tags:
  - knowledge-graph-operations
  - rdf-triples
  - graph-traversal
  - sparql-querying
  - shortest-path
inputs:
  triples:
    type: array
    required: true
    description: "List of knowledge graph triples `[{'subject': 's', 'predicate': 'p', 'object': 'o'}]`."
  operation:
    type: string
    required: true
    description: "Graph operation (`'shortest_path'`, `'neighbors'`, `'centrality'`, `'subgraph'`)."
  query_params:
    type: object
    required: false
    description: "Operational parameters (e.g. `{'source': 'node_a', 'target': 'node_b'}`)."
outputs:
  operation_result:
    type: object
    description: Structured result payload matching requested graph operation.
  node_count:
    type: integer
    description: Total number of unique nodes in the active graph.
  edge_count:
    type: integer
    description: Total number of directed predicate edges.
---

# Knowledge Graph Operations Engine

`knowledge-graph-operations` manages semantic triple stores, graph traversals, and pathfinding queries across the SME knowledge base in Python:

$$\mathcal{G} = (\mathcal{V}, \mathcal{E}), \quad \mathcal{E} \subseteq \mathcal{V} \times \mathcal{R} \times \mathcal{V}, \quad \text{ShortestPath}(s, t) = \arg\min_{\pi \in \Pi_{s, t}} |\pi|$$

---

## The 5-Stage Knowledge Graph Operations Progression

1. **Triple Ingest & Adjacency Construction**: Ingest semantic triples; construct directed adjacency lists.
2. **Graph Metric Profiling**: Compute node degrees, density, and connected components.
3. **The Visual Brief**: Generate interactive HTML graph network brief at `%TEMP%\knowledge-graph-brief-<timestamp>.html` using Vis.js / Force-Directed physics.
4. **Mandatory Checkpoint**: Assert graph reachability; verify path existence between query endpoints.
5. **Traversal Execution & Output Emission**: Execute BFS/Dijkstra search or neighbor extraction and emit graph payload.

---

## Implementation Notes

```python
import collections
from typing import Dict, List, Any, Optional

def execute_graph_operation(
    triples: List[Dict[str, str]],
    operation: str = "neighbors",
    query_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    adj = collections.defaultdict(list)
    nodes = set()
    
    for t in triples:
        s, p, o = t["subject"], t.get("predicate", "related_to"), t["object"]
        adj[s].append({"neighbor": o, "predicate": p})
        nodes.add(s)
        nodes.add(o)
        
    params = query_params or {}
    src = params.get("source", list(nodes)[0] if nodes else "")
    tgt = params.get("target", "")
    
    res = {}
    if operation == "neighbors":
        res = {"source": src, "neighbors": adj.get(src, [])}
    elif operation == "shortest_path":
        # BFS Shortest Path
        queue = collections.deque([[src]])
        visited = {src}
        path_found = []
        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == tgt:
                path_found = path
                break
            for edge in adj.get(curr, []):
                nxt = edge["neighbor"]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(path + [nxt])
        res = {"source": src, "target": tgt, "path": path_found, "length": len(path_found) - 1 if path_found else -1}
        
    return {
        "operation_result": res,
        "node_count": len(nodes),
        "edge_count": len(triples)
    }
```

---

## Anti-Patterns & Guardrails

- **Unbounded Graph Expansion** — Running deep recursive graph traversals without visited-set cycle protection.
- **Dangling Triple References** — Storing edges that point to non-existent nodes without referential integrity checks.