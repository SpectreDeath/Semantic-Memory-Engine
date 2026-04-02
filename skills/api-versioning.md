---
Domain: API Design
Version: 1.0.0
Complexity: intermediate
Type: architecture
Category: api
name: API Versioning
Source: SME v3.0.0
Source_File: gateway/routers/
---

# API Versioning Strategy

## Purpose
Manage API evolution and backward compatibility for the SME (Semantic Memory Engine) Gateway using semantic versioning and URL-based versioning.

## Description
SME v3.0.0 implements a versioned API strategy to ensure clients can reliably consume endpoints while allowing the system to evolve. All API routes are prefixed with `/api/v1/` to indicate the major version.

## Architecture

```
/api/v1/
├── analysis/          # Analysis endpoints
│   ├── graph          # Knowledge graph generation
│   └── report         # Intelligence reports
├── ingestion/         # Data ingestion
│   └── crawl          # Web crawling
├── connections/       # Service management
│   ├── status         # Health checks
│   └── ai-provider    # Provider switching
├── search/            # Semantic search
└── memory/            # Memory operations
```

## Workflow

### Version Naming Convention
- **Major** (`v1`, `v2`): Breaking changes, new URL prefix
- **Minor** (`v1.1`): New features, backward compatible
- **Patch** (`v1.0.1`): Bug fixes, no API changes

### Adding a New Endpoint
```python
# gateway/routers/analysis.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

@router.post("/graph")
async def generate_graph(request: GraphRequest) -> GraphResponse:
    """Generate knowledge graph from text."""
    # Implementation
    pass
```

### Deprecating an Endpoint
```python
from fastapi import APIRouter
import warnings

router = APIRouter(prefix="/api/v1", tags=["legacy"])

@router.post("/old-endpoint", deprecated=True)
async def old_endpoint():
    """Deprecated: Use /api/v1/new-endpoint instead."""
    warnings.warn("This endpoint is deprecated", DeprecationWarning)
    # Redirect or handle
    pass
```

## Examples

### Client Usage
```javascript
// Frontend API calls
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Version 1 endpoints
const response = await fetch(`${API_URL}/api/v1/analysis/graph`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'input data' })
});
```

### Version Migration
When releasing v2:
1. Create new router prefix `/api/v2/`
2. Keep v1 endpoints active with deprecation warnings
3. Update client to use v2 endpoints
4. Remove v1 after migration period (6 months recommended)

## Implementation Notes
- All routers use `APIRouter` from FastAPI
- Tags group endpoints by domain in OpenAPI docs
- Version in URL allows parallel deployment of multiple versions
- Breaking changes require new major version prefix

## Related Skills
- authentication.md - Securing versioned endpoints
- error-handling.md - Consistent error responses across versions
- config-management.md - Environment-specific API URLs