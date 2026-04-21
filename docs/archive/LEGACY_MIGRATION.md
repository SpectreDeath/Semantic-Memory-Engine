# Legacy Code Migration Plan

> Status: Pending Review | Last Updated: 2026-02-22

## Overview

This document outlines the migration plan for code in the `legacy/` directory. The goal is to either migrate useful code to the main codebase or mark dead code for removal.

## Legacy Directory Contents

```
legacy/
├── adaptive_scout.py           # Status: UNKNOWN - Needs review
├── data_processor.py           # Status: UNKNOWN - Needs review
├── gephi_bridge_simple.py     # Status: POSSIBLY USED - Check src/visualization/
├── harvester_crawler.py       # Status: REPLACED - See src/gathering/
├── HARVESTER_MANIFEST.json    # Status: REFERENCE - Keep for history
├── harvester_schema.py        # Status: REPLACED - See src/harvester/
├── harvester_spider.py        # Status: REPLACED - See src/gathering/
├── memory_synapse.py          # Status: UNKNOWN - Needs review
├── monitoring_diagnostics.py  # Status: UNKNOWN - Needs review
├── pipeline_orchestrator.py   # Status: REPLACED - See src/pipeline.py
├── REGISTRY_OLD.py           # Status: DEPRECATED - Remove
├── retrieval_query.py         # Status: UNKNOWN - Needs review
├── scribe_authorship.py       # Status: UNKNOWN - Needs review
├── semantic_loom.py          # Status: UNKNOWN - Needs review
├── test_fpdf.py              # Status: TEST - Move to tests/
├── TOOLBOX_MANIFEST.json     # Status: REFERENCE - Keep for history
├── verify_adaptive.py        # Status: TEST - Move to tests/
├── verify_pystyl.py          # Status: TEST - Move to tests/
├── verify_reporting.py        # Status: TEST - Move to tests/
├── Projects py/               # Status: DIRECTORY - Review contents
└── SME/                       # Status: DIRECTORY - Review contents
```

## Migration Categories

### Category 1: Move to Tests (Priority: High)

These files are test-related and should be moved to the `tests/` directory:

- [ ] `legacy/test_fpdf.py` → `tests/test_fpdf.py`
- [ ] `legacy/verify_adaptive.py` → `tests/test_adaptive.py`
- [ ] `legacy/verify_pystyl.py` → `tests/test_stylometry.py`
- [ ] `legacy/verify_reporting.py` → `tests/test_reporting.py`

### Category 2: Migrate to Source (Priority: Medium)

These files contain useful logic that should be migrated:

- [ ] `legacy/gephi_bridge_simple.py` → Merge into `src/visualization/` or `src/utils/gephi_bridge.py`
- [ ] `legacy/memory_synapse.py` → Review for potential migration to `src/synapse/`
- [ ] `legacy/semantic_loom.py` → Review for potential migration to `src/scribe/`

### Category 3: Replace with Current Code (Priority: Low)

These have been replaced by current implementations:

- [ ] `legacy/harvester_crawler.py` → Use `src/gathering/`
- [ ] `legacy/harvester_spider.py` → Use `src/gathering/`
- [ ] `legacy/harvester_schema.py` → Use `src/harvester/`
- [ ] `legacy/pipeline_orchestrator.py` → Use `src/pipeline.py`

### Category 4: Remove (Priority: High)

These files are deprecated and should be removed:

- [ ] `legacy/REGISTRY_OLD.py` - Duplicate of current registry
- [ ] `legacy/Projects py/` - Old project files, review and remove
- [ ] `legacy/SME/` - Old SME directory, review and remove

### Category 5: Unknown - Needs Review (Priority: Medium)

These files need manual review to determine their status:

- [ ] `legacy/adaptive_scout.py`
- [ ] `legacy/data_processor.py`
- [ ] `legacy/monitoring_diagnostics.py`
- [ ] `legacy/retrieval_query.py`
- [ ] `legacy/scribe_authorship.py`

## Action Items

### Immediate Actions (This Sprint)

1. **Move test files** - Relocate test files from `legacy/` to `tests/`
2. **Remove REGISTRY_OLD.py** - This is clearly deprecated
3. **Audit Projects py/** - Check contents and remove if obsolete

### Short-Term Actions (Next 2 Sprints)

4. **Review unknown files** - Go through Category 5 files
5. **Merge gephi_bridge** - Consolidate Gephi-related code

### Long-Term Actions (Backlog)

6. **Full legacy removal** - Once all migrations complete, remove entire `legacy/` directory

## Notes

- Always check for imports before removing any file
- Run tests after moving code to ensure nothing breaks
- Document any functionality that is lost during migration

## References

- See `docs/EXTENSION_CONTRACT.md` for current architecture
- See `src/pipeline.py` for current orchestration
- See `extension/` for VS Code extension details
</parameter>
<task_progress>- [x] Consolidate dependency management (pyproject.toml as source of truth)
- [x] Add ruff, bandit, mypy configuration to pyproject.toml
- [x] Add pre-commit configuration
- [ ] Fix SQL injection in forensic vault
- [ ] Refactor pipeline.py - extract late imports
- [x] Address legacy code - audit and plan
- [x] Create CI/CD workflow configuration