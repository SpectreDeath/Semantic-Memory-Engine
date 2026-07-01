# SME Project Identity

## Purpose
Production-grade MCP Gateway for forensic AI capabilities (Lawnmower Man v3.0.1)

## Stack
- Python 3.13 (spacy incompatible with 3.14)
- FastAPI + Uvicorn
- PostgreSQL Nexus for production-grade storage
- SQLite for local development
- NVIDIA GeForce GTX 1660 Ti 6GB (hardware constraint)

## Architecture (v3.0.1)
```
Operator (8000) → AI Provider (embedded)
Frontend (5173)
```
Sidecar removed - AI provider runs directly in the operator.

## Conventions
- Extensions extend `BasePlugin` class
- Use logging module instead of print statements
- Run `ruff check` and `ruff format` before committing
- Target 75% test coverage (currently 30%)
- Phase testing: `pytest -m phase1|phase2|phase3`

## Test Status (2026-06-28)
- **Phase1**: 405 passed, 22 skipped
- **Phase2**: 189 passed, 21 skipped
- **Phase3**: 58 passed, 9 skipped
- **Total**: 652 passed, 52 skipped (30% coverage)

## Recent Work
- Fixed 28 pre-existing test failures (SkillsLoader fields, mocking paths)
- Skipped 10 unimplemented/v2.1.0 tests
- Added 21 tests for ext_stetho_scan (coverage: 0%→29%)
- Refactored ext_ghost_trap to BasePlugin + 37 tests (0%→15%)
- All changes pushed to GitHub (origin/main synced)
- Implemented skill extraction pipeline (src/utils/skill_extractor.py, scripts/extract_skill.py)
- Implemented Nexus Vault Bridge (src/utils/nexus_vault.py) for PostgreSQL/SQLite metadata ingestion
- Added live SkillsMP.com ingestion via crawl fetch with streaming GitHub raw content
- Added 2 gold-standard skills in skills/gold_standard/
- Ran project-wide ruff format (67 files reformatted)
- CI Code Quality job passes on gateway/ src/ extensions/ after formatting fixes

## Directory Structure
- `extensions/ext_*/plugin.py` - Plugin implementations
- `skills/` - Skill documentation (some in subdirectories)
- `data/logs/` - Runtime logs
- `.context/` - Agent session memory
- `.kilo/` - Agent configuration and skills