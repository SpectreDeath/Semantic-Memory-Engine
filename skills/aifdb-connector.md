---
name: aifdb-connector
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Integration
source_file: src/query/aifdb_connector.py
source: Semantic Memory Engine (SME)
tags:
  - aifdb-connector
  - argumentation-database
  - aif-schemes
  - argument-interchange-format
  - debate-mining
inputs:
  argument_corpus_id:
    type: string
    required: true
    description: Unique identifier for the AIFdb debate or argument node set.
  action:
    type: string
    required: true
    description: Operation (`'fetch_nodeset'`, `'extract_schemes'`, `'export_json'`).
outputs:
  aif_graph:
    type: object
    description: Argument Interchange Format graph containing I-nodes (information), S-nodes (schemes), and inference edges.
  node_count:
    type: integer
    description: Count of argumentative proposition nodes retrieved.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# AIFdb Connector Engine

`aifdb-connector` interfaces with the global Argument Interchange Format Database (AIFdb), importing and serializing formal argument structures in Python:

$$\text{AIFGraph} = \langle \mathcal{I}, \mathcal{S}, \mathcal{E} \rangle, \quad \mathcal{I} = \text{Claims}, \quad \mathcal{S} = \text{InferenceSchemes}$$

---

## The 5-Stage AIFdb Connector Progression

1. **Request Intake & Corpus Resolution**: Ingest debate node-set ID and target format.
2. **AIF JSON/XML Fetch & Parsing**: Fetch formal argumentation nodeset from local repository or remote AIFdb API.
3. **The Visual Brief**: Generate interactive HTML argument debate graph brief at `%TEMP%\aifdb-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert graph well-formedness (edges strictly connect I-nodes through S-nodes).
5. **AIF Serialization & Output Emission**: Emit structured argument graph dictionary.

---

## Implementation Notes

```python
from typing import Dict, List, Any

def fetch_aifdb_nodeset(
    argument_corpus_id: str,
    action: str = "fetch_nodeset"
) -> Dict[str, Any]:
    mock_nodeset = {
        "nodes": [
            {"nodeID": "1", "text": "Premise A", "type": "I"},
            {"nodeID": "2", "text": "Inference Rule", "type": "RA"},
            {"nodeID": "3", "text": "Conclusion B", "type": "I"}
        ],
        "edges": [
            {"edgeID": "e1", "fromID": "1", "toID": "2"},
            {"edgeID": "e2", "fromID": "2", "toID": "3"}
        ]
    }
    return {
        "aif_graph": mock_nodeset,
        "node_count": len(mock_nodeset["nodes"]),
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Direct I-to-I Edge Injection** — Constructing AIF graphs with direct links between Information nodes without mediating Scheme (S) nodes.
- **Uncached Remote Queries** — Fetching static debate structures repeatedly without local SQLite caching.