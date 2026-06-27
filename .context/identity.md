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
- Target 75% test coverage (pytest.ini configured with phased markers)

## Directory Structure
- `extensions/ext_*/plugin.py` - Plugin implementations
- `skills/` - Skill documentation (some in subdirectories)
- `data/logs/` - Runtime logs
- `.context/` - Agent session memory
- `.kilo/` - Agent configuration and skills