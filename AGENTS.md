# SME Project Instructions

This file provides context and instructions for AI agents working on this project.

## Project Overview

**Lawnmower Man** is a production-grade MCP Gateway for forensic AI capabilities.
- **Version**: 3.0.1
- **Python**: 3.13
- **Hardware**: NVIDIA GeForce GTX 1660 Ti 6GB

## Architecture

```
Operator (8000) → AI Provider (embedded)
Frontend (5173)
```

The sidecar was removed in v3.0.1 - AI provider runs directly in the operator.

## Key Commands

```bash
# Install dependencies
pip install -e .

# Run natively (recommended)
python -m src.api.main           # Operator
cd frontend && npm run dev       # Frontend

# Or use the startup script
.\start_native.ps1

# Run tests
pytest tests/ -v

# Lint
ruff check src/ gateway/ extensions/
```

## Important Notes

- Use Python 3.13 only (3.14 has spacy compatibility issues)
- Dependencies are in `pyproject.toml` (not requirements.txt)
- All skills are in `skills/` directory
- Use `SME_VENV` env var to override venv path in gephi_export_tool.py
- Health checks no longer reference sidecar

## Code Style

- Run `ruff check` and `ruff format` before committing
- Target 75% test coverage
- Avoid bare `except:` - use specific exceptions
- Use logging instead of print statements

## Common Patterns

- Extensions: `extensions/ext_*/plugin.py`
- AI providers: `src/ai/providers/`
- Skills: `skills/*.md`
