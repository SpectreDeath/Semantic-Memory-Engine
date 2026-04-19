---
name: vindex-workflow
description: >-
  Implements the "LLM as a Database" paradigm using Karpathy Loop methodology.
  Transforms RAG (vector DB) to "Physical Facts" via (Entity, Relation, Target) 
  triples, with KNN retrieval, trust scoring, and Gephi visualization.
metadata:
  category: ai/ml
  source:
    repository: 'https://github.com/spectre/SME'
    path: .kilo/skills/vindex-workflow
---

# V-Index Workflow

This skill implements the V-Index pipeline for transforming LLMs into queryable databases using the Karpathy Loop methodology (Observe → Theory → Implement → Evaluate).

## When to Use This Skill

- Building "Physical Facts" knowledge bases (triplets mapped to weight-space)
- Implementing graph-based knowledge retrieval without dense attention
- Forensic analysis with trust-scored knowledge nodes
- Real-time neural activation visualization in Gephi
- VS Code IDE integration for weight exploration

## What This Skill Does

### Phase 1: V-Index Ingestion Bridge
1. **Feature Probing** - Probe model weights for concept activations using transformer_lens
2. **Triplet Extraction** - Extract (Entity, Relation, Target) triples using spacy NER
3. **V-Index Overlay** - Patch LLM prompts with triples via `[V-INDEX]` actuator tokens

### Phase 2: Gephi Visualization
1. **Weight Export** - Export activations to GraphML/CSV/GEXF for Gephi
2. **Activation Streaming** - Stream real-time via WebSocket or HTTP to Gephi

### Phase 3: Graph Walk Navigator
1. **KNN Retrieval** - k-Nearest Neighbor search on local embeddings (0.38ms/query optimized)
2. **Trust Validation** - Filter by trust scores, block hallucination at threshold < 0.25

### Phase 4: VS Code IDE
1. **Weight Explorer** - Sidebar showing top activations for selected words
2. **Poseidon Test** - Right-click "Inject as Physical Fact" with Atlantis verification

## How to Use

### Extract Triplets from Text
```
Extract triplets from the following text:
```

### Inject Triplets into LLM Prompt
```
Use V-Index overlay to inject knowledge about:
```

### KNN Knowledge Retrieval
```
Search the knowledge base for:
```

### Check Trust / Block Hallucination
```
Validate these results for hallucination:
```

### Export to Gephi
```
Export activations to Gephi format:
```

### Run Poseidon Test
```
Inject this fact and verify with Poseidon:
```

## Example

**User**: "Extract triplets from: The Semantic Memory Engine was created by the research team."

**Output**:
```
(Entity, Relation, Target):
(The Semantic Memory Engine, created_by, the research team)
```

**User**: "Search knowledge base for 'SME creation'"

**Output**:
```
Retrieved 2 relevant triplets (sim: 0.926, 0.907)
Blocked: false, Action: proceed_with_trusted
```

## Implementation Modules

| Module | Path | Purpose |
|--------|------|---------|
| feature_prober.py | gateway/ | Model weight probing |
| triplet_harvester.py | gateway/ | Entity/Relation/Target extraction |
| vindex_overlay.py | gateway/ | Prompt patching |
| weight_exporter.py | gateway/ | GraphML/CSV export |
| activation_streamer.py | gateway/ | Gephi streaming |
| graph_walk.py | gateway/ | KNN retrieval |
| epistemic_trust.py | gateway/ | Trust/hallucination blocking |
| vscode_explorer.py | gateway/ | VS Code integration |

## Tuning Parameters

- `DEFAULT_TRUST_THRESHOLD`: 0.6 (accuracy-critical tasks)
- `HALLUCINATION_BLOCK_THRESHOLD`: 0.25 (block below this)
- `TRUST_WEIGHTS`: source_diversity (30%), source_type (25%), citation (20%), recency (15%), verification (10%)

## Karpathy Loop Iteration

1. **Observe**: Run `probe_concept_tool()` to see activations
2. **Theory**: Hypothesize V-index patch or Graph Walk modification
3. **Implement**: Modify triplet patterns or trust thresholds
4. **Evaluate**: Run forensic trace - did "Physical Edge" change?

## Related Use Cases

- Forensic authorship analysis
- Knowledge graph construction
- Hallucination prevention
- Neural network interpretability
- Real-time model monitoring
