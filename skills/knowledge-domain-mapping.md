---
name: knowledge-domain-mapping
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Knowledge Management
source_file: extensions/ext_atlas/
source: Semantic Memory Engine (SME)
tags:
  - knowledge-domain-mapping
  - taxonomy-mapping
  - concept-hierarchies
  - domain-ontology
  - cross-domain-alignment
inputs:
  domain_concepts:
    type: array
    required: true
    description: List of concept dictionaries or taxonomy terms to map.
  target_ontology:
    type: string
    required: false
    description: Target canonical ontology schema (`'sme_master'`, `'acm_ccs'`, `'mesh'`, default `'sme_master'`).
outputs:
  mapped_domains:
    type: object
    description: Hierarchical domain trees with parent-child links and depth levels.
  unmapped_terms:
    type: array
    description: Concepts that could not be mapped to any canonical domain category.
  coverage_ratio:
    type: number
    description: Fraction of input terms successfully grounded in the domain ontology.
---

# Knowledge Domain Mapping Engine

`knowledge-domain-mapping` structures unstructured concepts into hierarchical domain taxonomies and semantic ontologies in Python:

$$\text{DomainTree}(\mathcal{C}) = \langle \mathcal{V}, \mathcal{E}, \text{root} \rangle, \quad \text{Coverage} = \frac{|\mathcal{C}_{\text{grounded}}|}{|\mathcal{C}|}$$

---

## The 5-Stage Knowledge Domain Mapping Progression

1. **Concept Ingestion & Hierarchy Init**: Ingest concept list; initialize root taxonomy node.
2. **Topological Classification**: Map concepts into domain branches (e.g. `Statistics`, `Forensics`, `Gateway`, `Security`).
3. **The Visual Brief**: Generate interactive HTML domain taxonomy tree at `%TEMP%\domain-mapping-brief-<timestamp>.html` with collapsible branch nodes.
4. **Mandatory Checkpoint**: Verify acyclicity in domain relations; prevent circular sub-domain dependencies.
5. **Tree Serialization & Output Emission**: Compile domain tree dictionary and emit complete `DomainHierarchyResult`.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def map_knowledge_domains(
    domain_concepts: List[str],
    target_ontology: str = "sme_master"
) -> Dict[str, Any]:
    DOMAINS = {
        "forensics": ["stylometry", "impostor", "adversarial", "rhetorical", "audit"],
        "gateway": ["mcp", "traffic_router", "session_bridge", "nexus"],
        "analytics": ["correlation", "clustering", "polars", "delta"]
    }
    
    mapped = {d: [] for d in DOMAINS}
    unmapped = []
    
    for term in domain_concepts:
        t_low = term.lower()
        found = False
        for d, keywords in DOMAINS.items():
            if any(k in t_low for k in keywords):
                mapped[d].append(term)
                found = True
                break
        if not found:
            unmapped.append(term)
            
    total = len(domain_concepts) or 1
    coverage = round((len(domain_concepts) - len(unmapped)) / total, 4)
    
    return {
        "mapped_domains": mapped,
        "unmapped_terms": unmapped,
        "coverage_ratio": coverage
    }
```

---

## Anti-Patterns & Guardrails

- **Flat Taxonomies** — Generating giant un-nested domain lists without parent-child hierarchical groupings.
- **Orphan Concept Neglect** — Dropping unmapped terms silently rather than capturing them in an explicit unmapped queue.
