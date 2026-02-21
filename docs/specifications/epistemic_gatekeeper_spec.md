# Epistemic Gatekeeper Extension Specification

## Overview

The Epistemic Gatekeeper provides trust scoring for data sources and content. It evaluates information quality using multiple signals including entropy analysis, burstiness detection, and vault proximity.

## Purpose

- Calculate trust scores for ingested content
- Detect synthetic or generated content
- Identify information quality signals
- Provide epistemic confidence metrics

## Trust Scoring Algorithm

### Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Entropy Score | 30% | Shannon entropy of content |
| Burstiness | 25% | Variability in content generation |
| Vault Proximity | 25% | Similarity to known synthetic patterns |
| Source Reliability | 20% | Historical reliability of source |

### Formula

```
TrustScore = (Entropy × 0.30) + (Burstiness × 0.25) + (Vault × 0.25) + (Source × 0.20)
```

## Signals

### Entropy Score
- Normal distribution expected for natural text
- Low entropy = suspicious uniformity (possible AI generation)
- High entropy = natural variability

### Burstiness
- Measures timing and volume patterns
- Consistent intervals suggest automation
- Variable patterns indicate human behavior

### Vault Proximity
- Compares against "Grok Vault" of synthetic signatures
- Cosine similarity to known patterns
- Flags content matching known synthetic sources

### Source Reliability
- Historical accuracy tracking
- Source reputation scoring
- Cross-reference validation

## API

### Tools Exposed

1. `calculate_trust_score(content: str)` - Get trust score for content
2. `audit_folder_veracity(folder: str)` - Audit all files in folder
3. `get_trust_metrics(content: str)` - Get detailed metrics

### Response Format

```json
{
  "trust_score": 75.5,
  "confidence": "high",
  "signals": {
    "entropy_score": 4.2,
    "burstiness": 0.65,
    "vault_proximity": 0.1,
    "source_reliability": 0.8
  },
  "recommendation": "approve",
  "flags": []
}
```

## Integration

### With Harvester
- Gatekeeper scores all ingested content
- Low scores trigger alerts
- Content flagged for review

### With Ghost Trap
- Ghost Trap events increase suspicion
- File system changes factor into trust
- Persistence mechanisms lower trust

### With NUR
- NUR anomalies correlate with trust
- Usage patterns inform scoring
- Combined analysis for accuracy
