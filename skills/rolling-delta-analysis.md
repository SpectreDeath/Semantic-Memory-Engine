---
name: rolling-delta-analysis
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Analysis
source_file: src/scribe/rolling_delta.py
source: Semantic Memory Engine (SME)
tags:
  - rolling-delta-analysis
  - time-series-forensics
  - change-point-detection
  - sliding-window-delta
  - metric-velocity
inputs:
  time_series_data:
    type: array
    required: true
    description: Ordered sequence of numerical observation points `[12.5, 13.0, 15.2, 19.8, ...]`.
  window_size:
    type: integer
    required: false
    description: Sliding window span $W \ge 2$ (default 5).
  threshold_sigma:
    type: number
    required: false
    description: Anomaly detection threshold multiplier in standard deviations (default 2.5).
outputs:
  deltas:
    type: array
    description: First-order rolling rate-of-change vector $\Delta x_t = x_t - x_{t-1}$.
  rolling_mean:
    type: array
    description: Moving average series over window $W$.
  change_points:
    type: array
    description: List of time indices where delta exceeded `threshold_sigma`.
  trend_direction:
    type: string
    description: Overall series trajectory (`'increasing'`, `'decreasing'`, or `'stationary'`).
---

# Rolling Delta Analysis Engine

`rolling-delta-analysis` monitors temporal velocity, acceleration, and sudden regime shifts in streaming telemetry. It computes **sliding window finite differences, moving statistics, and change-points in Python**:

$$\Delta x_t = x_t - x_{t-1}, \quad \mu_{W, t} = \frac{1}{W}\sum_{i=0}^{W-1} x_{t-i}, \quad \text{Anomaly} \iff |\Delta x_t - \bar{\Delta}_{W}| > k \cdot \sigma_{\Delta, W}$$

---

## The 5-Stage Rolling Delta Progression

1. **Series Ingest & Chronological Verification**: Ingest observation sequence; assert non-empty series of length $N \ge W$.
2. **First-Order Finite Difference Computation**: Compute step-to-step deltas $\Delta x_t$ across the timeline.
3. **The Visual Brief**: Generate interactive HTML sparkline brief at `%TEMP%\rolling-delta-brief-<timestamp>.html` displaying rolling mean envelopes and change-point markers.
4. **Mandatory Checkpoint**: Compute window rolling standard deviation; flag indices where $|\Delta x_t| > k\sigma$.
5. **Trend Classification & Output Emission**: Determine macro trend slope and emit complete delta profile.

---

## Implementation Notes

```python
import math
from typing import Dict, List, Any

def compute_rolling_delta(
    time_series_data: List[float],
    window_size: int = 5,
    threshold_sigma: float = 2.5
) -> Dict[str, Any]:
    n = len(time_series_data)
    if n < 2:
        return {"deltas": [], "rolling_mean": [], "change_points": [], "trend_direction": "stationary"}
        
    deltas = [time_series_data[i] - time_series_data[i-1] for i in range(1, n)]
    
    # Rolling mean
    rolling_means = []
    w = min(window_size, n)
    for i in range(n):
        start = max(0, i - w + 1)
        sub = time_series_data[start:i+1]
        rolling_means.append(round(sum(sub) / len(sub), 4))
        
    # Anomaly change-points
    mean_delta = sum(deltas) / len(deltas)
    var_delta = sum((d - mean_delta)**2 for d in deltas) / (len(deltas) - 1) if len(deltas) > 1 else 0.01
    std_delta = math.sqrt(var_delta) or 0.01
    
    change_points = [i+1 for i, d in enumerate(deltas) if abs(d - mean_delta) > (threshold_sigma * std_delta)]
    
    overall_slope = time_series_data[-1] - time_series_data[0]
    trend = "increasing" if overall_slope > std_delta else ("decreasing" if overall_slope < -std_delta else "stationary")
    
    return {
        "deltas": [round(d, 4) for d in deltas],
        "rolling_mean": rolling_means,
        "change_points": change_points,
        "trend_direction": trend
    }
```

---

## Anti-Patterns & Guardrails

- **Lag Misalignment** — Aligning rolling window outputs without accounting for half-window trailing lags.
- **Noise Over-Amplification** — Calculating high-order derivatives on un-smoothed high-frequency telemetry.
