# SME Architecture Decisions

## 2026-06-27: Plugin Refactoring Standardization
**Decision**: Refactor `ext_stetho_scan/plugin.py` to extend `BasePlugin` class
**Reason**: Consistent error handling and logging across all extensions
**Status**: Implemented

## 2026-06-27: Phased Testing Strategy
**Decision**: Add phase1/phase2/phase3 test markers to pytest.ini
**Reason**: Large test suite (710+ tests) was timing out; needed runtime controls
**Status**: Implemented - added to pytest.ini

## 2026-06-27: Generated Artifact Management
**Decision**: Add `reports/`, `data/logs/`, `skills/registry.json` to .gitignore
**Reason**: These are runtime-generated large files that shouldn't be version-controlled
**Status**: Implemented

## 2026-06-27: Skills Organization
**Decision**: Move `consolidation_analysis.py` to `skills/analysis/` subdirectory
**Reason**: Begin organizing skill documentation into category subdirectories
**Status**: Partial - only one file moved; 100+ skills remain flat

## 2026-06-27: Black Target Version
**Decision**: Update black target-version from py312 to py313 in pyproject.toml
**Reason**: Project requires Python 3.13; black config was outdated
**Status**: Fixed