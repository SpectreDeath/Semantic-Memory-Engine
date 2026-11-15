---
name: api-versioning
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Process
category: Core
source_file: gateway/routers/
source: Semantic Memory Engine (SME)
tags:
  - api-versioning
  - semantic-versioning
  - backward-compatibility
  - deprecation-lifecycle
  - schema-evolution
inputs:
  endpoint_path:
    type: string
    required: true
    description: API route path (e.g. `'/api/v1/analyze'`, `'/api/v2/analyze'`).
  client_version:
    type: string
    required: false
    description: Client requested semver string (e.g. `'1.2.0'`).
outputs:
  resolved_route:
    type: string
    description: Internal route handler mapped to the requested version.
  is_deprecated:
    type: boolean
    description: True if the requested API version is in the deprecation cycle.
  sunset_date:
    type: string
    description: ISO date when the deprecated version will be deactivated.
---

# API Versioning Engine

`api-versioning` manages backward-compatible API routing, semver negotiation, and deprecation lifecycles across SME gateway endpoints in Python:

$$\text{Route}(\text{Path}, v_{\text{client}}) = \arg\max_{v \in \mathcal{V}_{\text{supported}}, v \le v_{\text{client}}} \text{Handler}(v)$$

---

## The 5-Stage API Versioning Progression

1. **Request Route Ingestion & Header Parse**: Ingest route path and `X-API-Version` header.
2. **SemVer Range Matching**: Match client version against registered active and legacy route handlers.
3. **The Visual Brief**: Generate interactive HTML API lifecycle matrix at `%TEMP%\api-versioning-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that deprecated endpoints emit standard `Sunset` and `Deprecation` HTTP headers.
5. **Route Resolution & Output Emission**: Dispatch to active handler and emit routing metadata.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def resolve_api_version(
    endpoint_path: str,
    client_version: Optional[str] = "1.0.0"
) -> Dict[str, Any]:
    is_v1 = "/v1/" in endpoint_path or client_version.startswith("1.")
    return {
        "resolved_route": endpoint_path if not is_v1 else endpoint_path.replace("/v1/", "/v2/"),
        "is_deprecated": is_v1,
        "sunset_date": "2026-12-31" if is_v1 else None
    }
```

---

## Anti-Patterns & Guardrails

- **Abrupt Breaking Changes** — Deactivating API routes without a documented deprecation window.
- **Unpinned Client Calls** — Failing to default unversioned API requests to the oldest supported stable version.