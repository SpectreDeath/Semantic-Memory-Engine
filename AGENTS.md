# SME Project Instructions

This file provides context and instructions for AI agents working on this project.

## Project Overview

**Lawnmower Man** is a production-grade MCP Gateway for forensic AI capabilities.
- **Version**: 3.0.1 (Crucible Bridge Release)
- **Python**: 3.13 (Lazy fallback active for Python 3.14+)
- **Hardware**: NVIDIA GeForce GTX 1660 Ti 6GB

## Architecture

```
Operator (8000) ──► MimoControlBridge (6D Control Surface: D1-D6)
                      │
                      ▼
               Dynamic TrafficRouter (auto / local_only / em_cubed_workflow)
                      │
                      ├──► SessionBridge (SQLite WAL scratchpad persistence)
                      ├──► NexusDatabaseBridge (PRAGMA optimized multi-DB JOINs)
                      ├──► SemanticGraphBridge (WordNet & Graph Surface Execution)
                      ├──► SurfaceBridge (em-cubed Python AST & JSON Schema validation)
                      └──► EmCubedWorkflowBridge (Distributed DAG Task Pools)
                            │
                            ▼
              CandidatePoolStorage (SQLite WAL Candidate Pools F_ℓ)
                            │
                            ▼
              TextualGradientEngine (ANN Textual Backprop ∇text)
              MomentumBuffer & MultiStageValidationFilter
Frontend (5173) ──► WebSocket /ws/diagnostics (Live CPU/RAM/Routing Telemetry)
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
ruff check src/ gateway/ extensions/ tests/
```

## Important Notes

- Use Python 3.13 target (Python 3.14 guarded via lazy NLP loading)
- Dependencies are in `pyproject.toml` (not requirements.txt)
- Skills are in `skills/` directory (some organized in subdirectories like `skills/analysis/`)
- Extension tools wrapped with `_wrap_sandboxed_handler` and 3-failure circuit breakers
- Cryptographic Merkle tree hashing enabled in `AuditEngine` (`src/logic/audit_engine.py`)
- Agentic Neural Network ($\mathcal{ANN}$) backprop via `TextualGradientEngine` (`src/logic/textual_gradient.py`)

## Code Style

- Run `ruff check` and `ruff format` before committing
- Target 75% test coverage
- Avoid bare `except:` - use specific exceptions
- Use logging instead of print statements

## Common Patterns

- Component Bridges: `gateway/mcp_server.py` (`SessionBridge`, `NexusDatabaseBridge`, `SemanticGraphBridge`, `SurfaceBridge`)
- Traffic Routing: `gateway/traffic_router.py` (`TrafficRouter`)
- Distributed Workflows: `gateway/em_cubed_bridge.py` (`EmCubedWorkflowBridge`)
- Candidate Pools & Dynamic Routing: `gateway/candidate_pool.py` (`CandidatePoolStorage`)
- ANN Textual Backprop: `src/logic/textual_gradient.py` (`TextualGradientEngine`)
- ANN Momentum & Validation: `gateway/momentum_buffer.py` (`MomentumBuffer`, `MultiStageValidationFilter`)
- MIMO 6D Control Surface: `gateway/mimo_bridge.py` (`MimoControlBridge`, `Mimo6DConfig`)
- Extensions: `extensions/ext_*/plugin.py` (Managed via `ExtensionManager`)
- Cryptographic Audit: `src/logic/audit_engine.py` (`AuditEngine`)