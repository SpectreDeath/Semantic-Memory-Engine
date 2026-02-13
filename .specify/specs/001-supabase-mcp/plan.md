# Plan: Supabase MCP Integration

## 1. Architecture
The 3.13 Sidecar will use a dedicated module `src/ai/archiver.py` to interface with the Supabase MCP server.

## 2. Implementation Steps
1. **Dependency Injection**: Add `supabase` and `mcp` (if used as a library) to `.brain_venv`.
2. **Archiver Module**: Create `src/ai/archiver.py` (3.13 only).
3. **Bridge Update**: Ensure `bridge.py` can pass metadata required for archiving if not present in the flow context.
4. **Worker Update**: Update `brain_worker.py` to call the archiver post-execution of a forensic flow.

## 3. Verification
- Manual: Trigger a mock threat and check Supabase Dash for the entry in `threat_leads`.
- Automated: `pytest tests/verify_archiver.py`.

## 4. VRAM Management
- The archiver will run as a lightweight post-process to avoid competing with the LLM inference for VRAM.
