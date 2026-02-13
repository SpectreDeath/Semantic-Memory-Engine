# SME PROJECT CONSTITUTION

## 1. Environment Guardrails

- **Main Runtime**: Python 3.14 (Sensors, UI, Prefect).
- **AI Runtime**: Python 3.13 Sidecar (Langflow, Pydantic v1).
- **Rule**: Never import `langflow` or `pydantic` in the 3.14 environment. Always use `src/ai/bridge.py`.

## 2. Hardware constraints (GTX 1660 Ti)

- **VRAM Limit**: Max 6GB.
- **Rule**: AI flows must use quantized models (GGUF/AWQ) or lightweight 7B parameters to avoid OOM (Out of Memory) errors.
- **Rule**: Common sense reasoning via ConceptNet must be performed using the ConceptNet Web API or a local SQLite lookup to preserve 1660 Ti VRAM for the primary LLM.

## 3. Forensic Integrity

- **Persistence**: All "Poisoned Well" alerts must be logged to Supabase via the MCP server.
- **Rule**: No lead is considered "Captured" until it exists in the `threat_leads` table.

## 4. GUI Layer (AionUi)

- **Platform**: AionUi (Electron), communicates with agents via ACP (Agent Communication Protocol).
- **Rule**: AionUi must **never** bundle or install its own Python runtime. All execution is delegated to `.venv` (3.14) and `.brain_venv` (3.13) via CLI shims in `bin/`.
- **Rule**: The VRAM Watchdog (`src/monitoring/vram_watchdog.py`) must run as a background process whenever AionUi is active.
- **Rule**: All MCP tool servers registered in AionUi must use `stdio` transport (no network sockets) to minimise attack surface.

## 5. AI Interaction Protocol

- **Abstraction Enforcement**: All AI calls must pass through the `ProviderFactory`. Direct imports of `google.generativeai` or `anthropic` in logic files are prohibited.
- **Environment Control**: The active provider is managed solely via `SME_AI_PROVIDER`.
- **Mock First**: New forensic tools must be verified with the `MockProvider` before being promoted to live AI testing to save tokens and VRAM.
