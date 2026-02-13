# Plan: Offline ConceptNet Caching System

## Proposed Changes

### AI Sidecar (Python 3.13)

#### [MODIFY] [conceptnet.py](file:///d:/SME/src/ai/tools/conceptnet.py)

- Refactor the tool to include SQLite connection management.
- Implement `init_db()` to set up tables and WAL mode.
- Implement `get_concept_with_cache(term)` as the primary entry point.
- Implement `_fetch_and_cache(term)` to handle API calls and storage.
- Implement a simple size-check and LRU purge mechanism.

---

## Verification Plan

### Automated Tests

- **Cache Logic Test**: `tests/test_conceptnet_cache.py`
  - Mock API.
  - Query term once (API called).
  - Query same term again (API not called, verify SQLite hit).
- **Size Limit Test**:
  - Inject dummy data until DB reaches 500MB.
  - Verify oldest records are purged.

### Manual Verification

1. Run `python src/ai/tools/conceptnet.py` (Sidecar).
2. Observe logs for "Cache Hit" vs "Cache Miss".
3. Check `data/conceptnet_cache.db` existence and size.
