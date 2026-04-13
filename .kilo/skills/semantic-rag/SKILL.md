---
name: semantic-rag
description: "Optimize semantic memory and RAG pipelines for the SME. Triggers: 'optimize RAG', 'semantic search', 'chunk strategy', 'retrieval tuning', 'vector similarity', 'embedding quality'. NOT for: new embedding models, when existing vector DB works fine."
---

# Semantic RAG Optimization

Optimize retrieval-augmented generation and semantic memory for the SME project.

## When to Use This Skill

Use this skill when:
- Improving semantic search accuracy
- Tuning chunk sizes for better retrieval
- Reducing noise in semantic matches
- Optimizing embedding similarity thresholds
- Debugging retrieval quality issues

Do NOT use this skill when:
- Need embeddings from scratch (use ML pipeline)
- Simple keyword search is sufficient
- Working with structured data only

## Input Format

```yaml
rag_request:
  action: string          # "analyze", "tune", "debug", "benchmark"
  query: string           # Test query to evaluate
  top_k: integer         # Number of results to evaluate (default: 5)
  similarity_threshold: float  # Cutoff threshold (default: 0.7)
```

## Key Techniques

### 1. Chunk Strategy Optimization

For SME's semantic memory:
- **Code**: 256-512 chars, overlap 50 chars
- **Docs**: 512-1024 chars, overlap 100 chars
- **Conversations**: Full messages as chunks

### 2. Similarity Threshold Tuning

```python
THRESHOLD_GUIDE = {
    "exact_match": 0.95,
    "high_similarity": 0.85,
    "relevant": 0.70,
    "_loose": 0.50,
}
```

### 3. Re-ranking Strategy

Apply cross-encoder re-ranking when initial recall is good but precision is low.

### 4. Query Expansion

Add semantic variations:
- Synonyms
- Abbreviations
- Related concepts

## Evaluation Metrics

- **Recall@K**: Fraction of relevant docs retrieved
- **MRR**: Mean reciprocal rank
- **NDCG**: Normalized discounted cumulative gain

## SME Integration Points

- `ext_semantic_auditor` - Semantic drift detection
- `ext_synthetic_source_auditor` - Feature vectors for embeddings
- Session memory via `memtext` skill

## Example Usage

```yaml
rag_request:
  action: analyze
  query: "how does authentication work"
  top_k: 10
```

Returns analysis of retrieval quality with specific improvements.