# SME Project Action Plan

## Current State

- **Branch**: `fix/python-version-enforcement`
- **Main branch**: 5 commits behind (needs sync)
- **Modified files**: 112 (70+ modified + 40 deleted + 12 untracked)
- **PRs merged**: #1 (V-Index), #2 (Python 3.13 enforcement)

---

## Phase 1: Sync & Cleanup (Priority: HIGH)

### 1.1 Sync with Main Branch
```bash
git checkout main
git pull origin main
git checkout fix/python-version-enforcement
git merge main
```

### 1.2 Analyze 112 Modified Files
Split into categories:
- **Extensions** (commit): New extensions (ext_api_key_manager, ext_webhook, etc.)
- **Frontend** (commit): New pages (APIKeyManager, AuditLog, Timeline)
- **Data files** (discard): .coverage, data/aether/*, data/chroma_db/*
- **docs/archive/** (discard): Already deleted files from previous work

### 1.3 Commit Meaningful Changes
```bash
# Option A: Single commit for all new extensions
git add extensions/ frontend/src/pages/ .vscode/
git commit -m "feat: Add new extensions and frontend pages"

# Option B: Separate commits if granular
```

---

## Phase 2: Python 3.13 Setup (Priority: HIGH)

### 2.1 Install Python 3.13
- Download: https://www.python.org/downloads/
- Install to: `C:\Users\spectre\AppData\Local\Programs\Python\Python313`

### 2.2 Create Virtual Environment
```bash
python3.13 -m venv .venv313
.venv313\Scripts\pip install -e .
.venv313\Scripts\pip install pytest pytest-cov
```

### 2.3 Verify spacy Imports
```bash
.venv313\Scripts\python -c "import spacy; print(spacy.__version__)"
```

---

## Phase 3: Test Suite Verification (Priority: HIGH)

### 3.1 Run Tests with Python 3.13
```bash
.venv313\Scripts\pytest tests/ -v --tb=short
```

### 3.2 Expected Results
- ~150 tests pass (core tests)
- ~3-5 failures (NLP edge cases - OK)
- Coverage target: 22%+ (already achieved)

### 3.3 Fix Critical Test Failures (if any)
- Focus on: test_events, test_aether, test_integration
- Skip: test_gephi_bridge (requires Gephi installed)

---

## Phase 4: Extension Tests (Priority: MEDIUM)

### 4.1 Run Extension Matrix Tests
```bash
pytest tests/test_extension_matrix.py -v
```

### 4.2 Add Missing Extension Tests
Already added:
- test_ext_api_key_manager.py ✓
- test_ext_scheduled_jobs.py ✓
- test_ext_webhook.py ✓

### 4.3 Fix Any Failing Extension Tests

---

## Phase 5: Future Enhancements (Priority: LOW)

### 5.1 FAISS Integration (>10k nodes)
- Research: https://github.com/facebookresearch/faiss
- Add to: gateway/graph_walk.py
- Use case: Scale KNN beyond current numpy implementation

### 5.2 Gephi Live Integration
- Requires: Gephi Desktop installed
- Test: gateway/activation_streamer.py WebSocket mode
- Use case: Real-time graph visualization

### 5.3 Complete Test Coverage
- Target: 75% (currently 22%)
- Strategy: Focus on untested gateway modules
- Tools: pytest-cov, coverage report

---

## Execution Order

| Step | Action | Status |
|------|--------|--------|
| 1 | Sync main → merge | TODO |
| 2 | Analyze modified files | TODO |
| 3 | Commit new extensions/pages | TODO |
| 4 | Discard data files | TODO |
| 5 | Install Python 3.13 | TODO |
| 6 | Create .venv313 | TODO |
| 7 | Run pytest on 3.13 | TODO |
| 8 | Verify spacy works | TODO |
| 9 | Run extension tests | TODO |
| 10 | [Future] FAISS | TODO |
| 11 | [Future] Gephi | TODO |
| 12 | [Future] Coverage | TODO |

---

## Notes

- Python 3.13 required due to spacy pydantic V1 incompatibility with 3.14
- Current working tree has 112 modified files from previous sessions
- PR #1 and #2 already merged to main
