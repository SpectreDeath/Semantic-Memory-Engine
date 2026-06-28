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
- Target 75% test coverage (currently 29%)
- Phase testing: `pytest -m phase1|phase2|phase3`

## Test Status (2026-06-28)
- **Phase1**: 363 passed, 22 skipped (core extensions)
- **Phase2**: 187 passed, 5 skipped (processing/NLP)
- **Phase3**: 68 passed, 13 skipped (integration)
- **Total**: 618 passed, 59 skipped

## Recent Work
- Fixed 28 pre-existing test failures (SkillsLoader fields, mocking paths)
- Skipped 10 unimplemented/v2.1.0 tests
- Added 21 tests for ext_stetho_scan (coverage: 0%→29%)
- All changes pushed to GitHub (origin/main synced)

## Directory Structure
- `extensions/ext_*/plugin.py` - Plugin implementations
- `skills/` - Skill documentation (some in subdirectories)
- `data/logs/` - Runtime logs
- `.context/` - Agent session memory
- `.kilo/` - Agent configuration and skills