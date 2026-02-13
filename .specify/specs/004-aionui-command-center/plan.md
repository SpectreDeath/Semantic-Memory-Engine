# Plan: AionUi & Gephi Unified Command Center

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   AionUi (Electron)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Chat Panel  │  │  MCP Client  │  │ Watchdog  │ │
│  │  (User I/O)  │  │  (stdio)     │  │ (JSON)    │ │
│  └───────┬──────┘  └──────┬───────┘  └─────┬─────┘ │
└──────────┼─────────────────┼───────────────┼────────┘
           │  ACP            │  MCP/stdio    │ stdout
    ┌──────┴──────┐   ┌──────┴──────┐  ┌─────┴──────┐
    │ sme-operator│   │  Supabase   │  │   VRAM     │
    │ (Py 3.14)   │   │  MCP Server │  │  Watchdog  │
    │  pipeline   │   │  (npx)      │  │ (pynvml)   │
    │  gephi_tool │   └─────────────┘  └────────────┘
    └──────┬──────┘
           │ subprocess (bridge.py)
    ┌──────┴──────┐
    │ sme-brain   │
    │ (Py 3.13)   │
    │  langflow   │
    │  conceptnet │
    └─────────────┘
```

## 2. Implementation Steps

### Phase 1 — AionUi Installation & Agent Registration

1. **Install AionUi** on the workstation (Windows build from [aionui.site/download](https://aionui.site/download/)).
2. **Create CLI shims** so AionUi's ACP can auto-detect the SME agents:
   - `sme-operator.bat` — wrapper that activates `.venv` and runs `python -m sme_cli`.
   - `sme-brain.bat` — wrapper that activates `.brain_venv` and runs `python src/ai/brain_worker.py`.
3. **Add shims to PATH** or place them in a project `bin/` directory that is appended to PATH in `aionui_settings.json`.
4. **Verify**: Open AionUi → Multi-Agent panel. Both agents should appear as detected.

### Phase 2 — MCP Server Configuration

1. **Map the Supabase MCP server** into `aionui_settings.json` under `"mcpServers"`:
   - Command: `npx supabase-mcp-server`
   - Env: source `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from `D:\SME\.env`.
2. **Test**: From the AionUi chat, ask the operator agent to *"list recent threat leads"*. The agent must use the MCP tool to query Supabase and return results.

### Phase 3 — Gephi Export Tool

1. **Create `src/tools/gephi_export_tool.py`**:
   - Parse user query → derive Supabase filter + mode.
   - Call `src/utils/gephi_bridge.py --mode <mode>`.
   - Return the output path (`data/exports/<timestamp>.gexf`).
2. **Register the tool** as an MCP tool so AionUi can invoke it from the chat.
   - Add a new `gephi-exporter` entry in `"mcpServers"` using a lightweight FastMCP wrapper.
3. **Test**: Ask *"Export trust graph to Gephi"* → expect a `.gexf` file to appear in `data/exports/`.

### Phase 4 — VRAM Watchdog

1. **Create `src/monitoring/vram_watchdog.py`**:
   - Poll `pynvml` every 10 seconds.
   - Emit JSON lines to stdout (consumed by AionUi's process manager).
   - Thresholds: CAUTION at 5.8 GB, CRITICAL at 5.9 GB (with SIGTERM to Sidecar).
2. **Register in `aionui_settings.json`** under a `"startup"` or `"background_processes"` key.
3. **Test**: Simulate high VRAM with a dummy allocation → verify CAUTION and CRITICAL logs appear.

### Phase 5 — Configuration Template

1. **Write `aionui_settings.json`** with all agents, MCP servers, and watchdog settings pre-configured for the SME environment.
2. **Place** in `D:\SME\config\aionui_settings.json` and symlink/copy to AionUi's config directory.

## 3. Files To Create/Modify

| Action | File | Description |
|---|---|---|
| **NEW** | `.specify/specs/004-aionui-command-center/spec.md` | This specification |
| **NEW** | `.specify/specs/004-aionui-command-center/plan.md` | This plan |
| **NEW** | `config/aionui_settings.json` | AionUi configuration template |
| **NEW** | `src/tools/gephi_export_tool.py` | Chat-invokable Gephi exporter MCP tool |
| **NEW** | `src/monitoring/vram_watchdog.py` | Background VRAM watchdog daemon |
| **NEW** | `bin/sme-operator.bat` | CLI shim for the Operator agent (3.14) |
| **NEW** | `bin/sme-brain.bat` | CLI shim for the Brain agent (3.13) |
| MODIFY | `src/utils/gephi_bridge.py` | Add `--output` argument for custom export path |
| MODIFY | `.specify/memory/constitution.md` | Add Section 4: GUI Layer rules |

## 4. Verification Plan

### Automated Tests

1. **VRAM Watchdog Unit Test**: `pytest tests/test_vram_watchdog.py`
   - Mock `pynvml` calls and assert correct JSON output at each threshold level.
2. **Gephi Export Tool Test**: `pytest tests/test_gephi_export_tool.py`
   - Mock Supabase data and verify `.gexf` file generation.

### Manual Verification

1. **Agent Detection**: Launch AionUi → navigate to Multi-Agent panel → confirm `sme-operator` and `sme-brain` appear.
2. **MCP Supabase Query**: Type in AionUi chat: *"Query the threat_leads table for the 5 most recent entries"* → confirm JSON response from Supabase.
3. **Gephi Export**: Type in AionUi chat: *"Export the trust graph to Gephi"* → confirm `.gexf` file is created in `data/exports/` and can be opened in Gephi.
4. **VRAM Monitor**: Check AionUi system tray or status bar for live VRAM readout. Verify no false-positive alerts under normal operation (~2 GB baseline).

## 5. VRAM / RAM Budget

| Component | VRAM | RAM |
|---|---|---|
| AionUi (Electron) | 0 MB | ~300 MB |
| sme-operator (3.14) | 0 MB | ~150 MB |
| sme-brain (3.13 + LLM) | ≤ 5.5 GB | ~500 MB |
| Gephi (if co-running) | ≤ 512 MB | ~800 MB |
| VRAM Watchdog | 0 MB | ~20 MB |
| **Total** | **≤ 6 GB** | **~1.8 GB** |
