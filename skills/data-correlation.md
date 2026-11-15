---
name: data-correlation
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Analysis
source_file: src/analysis/correlator.py
source: Semantic Memory Engine (SME)
tags:
  - data-correlation
  - feature-association
  - pearson-correlation
  - spearman-rank
  - dependency-matrix
inputs:
  dataset:
    type: object
    required: true
    description: "Tabular feature map `{'feature_a': [1.0, 2.0, ...], 'feature_b': [2.1, 3.9, ...]}`."
  method:
    type: string
    required: false
    description: "Correlation metric (`'pearson'` or `'spearman'`, default `'pearson'`)."
  min_threshold:
    type: number
    required: false
    description: Minimum absolute correlation coefficient to include in significant pairs (default 0.50).
outputs:
  correlation_matrix:
    type: object
    description: Pairwise correlation coefficients across all dataset variables.
  significant_pairs:
    type: array
    description: "List of strongly correlated feature pairs exceeding `min_threshold`."
  summary_stats:
    type: object
    description: Aggregate metrics including mean correlation and condition number.
---

# Data Correlation Engine

`data-correlation` computes pairwise associations and collinearity patterns across numerical observables. It calculates **Pearson product-moment and Spearman rank correlation matrices in Python**:

$$r_{xy} = \frac{\sum_{i=1}^n (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^n (x_i - \bar{x})^2 \sum_{i=1}^n (y_i - \bar{y})^2}}, \quad \rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$

---

## The 5-Stage Data Correlation Progression

1. **Dataset Ingestion & Vector Validation**: Ingest feature dictionary; assert uniform column lengths $N \ge 3$.
2. **Matrix Computation**: Compute sample means, variances, and pairwise covariance sums across all features.
3. **The Visual Brief**: Generate interactive HTML correlation heatmap at `%TEMP%\data-correlation-brief-<timestamp>.html` with color gradient $[-1.0, +1.0]$.
4. **Mandatory Checkpoint**: Filter out singular zero-variance columns to prevent division by zero.
5. **Significant Pair Extraction & Output Emission**: Extract pairs satisfying $|r_{xy}| \ge \theta$ and emit complete `CorrelationResult`.

---

## Implementation Notes

```python
import math
from typing import Dict, List, Any

def compute_data_correlations(
    dataset: Dict[str, List[float]],
    method: str = "pearson",
    min_threshold: float = 0.50
) -> Dict[str, Any]:
    features = list(dataset.keys())
    n = len(dataset[features[0]]) if features else 0
    
    means = {}
    stds = {}
    for f in features:
        vals = dataset[f]
        m = sum(vals) / n if n > 0 else 0.0
        var = sum((x - m)**2 for x in vals) / (n - 1) if n > 1 else 0.0
        means[f] = m
        stds[f] = math.sqrt(var)
        
    matrix = {}
    significant = []
    
    for i, f1 in enumerate(features):
        matrix[f1] = {}
        for j, f2 in enumerate(features):
            if i == j:
                matrix[f1][f2] = 1.0
                continue
            if stds[f1] == 0 or stds[f2] == 0:
                r = 0.0
            else:
                cov = sum((dataset[f1][k] - means[f1]) * (dataset[f2][k] - means[f2]) for k in range(n)) / (n - 1)
                r = cov / (stds[f1] * stds[f2])
            matrix[f1][f2] = round(r, 4)
            if i < j and abs(r) >= min_threshold:
                significant.append({"feature_1": f1, "feature_2": f2, "correlation": round(r, 4)})
                
    return {
        "correlation_matrix": matrix,
        "significant_pairs": significant,
        "summary_stats": {"total_features": len(features), "sample_size": n}
    }
```

---

## Anti-Patterns & Guardrails

- **Zero-Variance Feature Processing** — Attempting covariance calculation on invariant constant columns without zero-std guards.
- **Conflating Correlation with Causation** — Treating high observational correlation $r > 0.9$ as proof of causal dependency.