# Spec: AionUi & Gephi Unified Command Center

## 1. Objective

Integrate AionUi as the primary graphical user interface for the Semantic Memory Engine (SME). AionUi will serve as the central control surface, unifying the **dual-Python agent architecture**, the **Supabase MCP connection** (Spec 001), and the **Gephi Forensic Visualizer** (Spec 002) into a single, local-first GUI that an operator can interact with from a chat interface. All components must remain within the hardware envelope of the **GTX 1660 Ti**.

## 2. Environment Compliance

| Component | Runtime | Justification |
|---|---|---|
| AionUi Desktop | Electron (host) | AionUi runs as a standalone Electron app. It orchestrates agents but does not consume Python resources itself. |
| Operator Agent | Python 3.14 (Main) | Sensors, pipeline, Gephi exporter, and UI tools live in the main runtime. Registered as the primary AionUi agent via ACP auto-detect. |
| Specialist Agent | Python 3.13 (Sidecar) | Langflow, Pydantic v1, and ConceptNet logic. Invoked through `src/ai/bridge.py`. Registered as a secondary AionUi agent. |

- **Rule**: AionUi must **never** bundle or install its own Python interpreter. It delegates all execution to the existing `.venv` and `.brain_venv` environments.

## 3. Hardware Guardrails (GTX 1660 Ti)

- **VRAM Budget**: 6 GB total. AionUi itself uses **0 MB VRAM** (pure CPU/Electron).
  - Reserved for LLM inference via Sidecar: **≤ 5.5 GB**.
  - Reserved for Gephi rendering (if co-running): **≤ 512 MB**.
- **Monitor Script**: A background watchdog process (`src/monitoring/vram_watchdog.py`) must poll `pynvml` every **10 seconds**. If total VRAM exceeds **5.8 GB** (96.7% of 6 GB), the watchdog:
  1. Sends a `CAUTION` toast to AionUi via stdout JSON.
  2. Logs the event to `logs/vram_alerts.log`.
  3. If sustained for **30 seconds**, issues a `SIGTERM` to the Sidecar worker to gracefully free VRAM.

## 4. Functional Requirements

### 4.1 AionUi Agent Integration (FR-01)

AionUi uses the **Agent Communication Protocol (ACP)** to auto-detect CLI tools on the system PATH. The SME project must expose two callable entry points:

| Agent Name | CLI Entry Point | Role |
|---|---|---|
| `sme-operator` | `python -m sme_cli` (3.14 venv) | Primary operator. Handles: pipeline runs, status, Gephi export, Supabase queries. |
| `sme-brain` | `.brain_venv/Scripts/python.exe src/ai/brain_worker.py` | Specialist. Handles: Langflow inference, ConceptNet expansion, forensic analysis flows. |

- AionUi's settings must declare both agents under the `"agents"` key in `aionui_settings.json`.
- The operator agent is set as `"default": true`.

### 4.2 Unified MCP Connection (FR-02)

The existing **Supabase MCP server** (Spec 001) must be mapped into AionUi's MCP configuration so that agents can query and write to the `threat_leads` table directly from the chat panel.

- **MCP Server ID**: `supabase-sme`
- **Transport**: `stdio` (the MCP server runs as a local subprocess).
- **Command**: `npx supabase-mcp-server`
- **Environment Variables**: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` sourced from `D:\SME\.env`.

### 4.3 Gephi Visualizer Bridge Tool (FR-03)

A custom AionUi **Tool** named `gephi_export` must be available in the chat interface. The tool:

1. Accepts a natural-language query from the user (e.g., *"Show me all threat actors linked to IP 192.168.x.x"*).
2. Translates the query into a Supabase filter on the `threat_leads` table.
3. Invokes `src/utils/gephi_bridge.py` with the appropriate `--mode` flag (`project | trust | knowledge | synthetic`).
4. Generates a `.gexf` file in `data/exports/`.
5. Returns the file path to the AionUi chat so the user can open it.

- **Fallback**: If Gephi is not running (no connection on `localhost:8080`), the tool must still generate the `.gexf` file and report success with a note: *"File saved. Open Gephi and load manually."*

### 4.4 VRAM Watchdog (FR-04)

- Script: `src/monitoring/vram_watchdog.py`
- **Runs as**: A background daemon launched by AionUi on startup.
- **Output format**: JSON lines to stdout (consumed by AionUi's process manager).

```json
{"level": "INFO", "vram_used_mb": 2048, "vram_total_mb": 6144, "pct": 33.3}
{"level": "CAUTION", "vram_used_mb": 5800, "vram_total_mb": 6144, "pct": 94.4, "action": "alert"}
{"level": "CRITICAL", "vram_used_mb": 5900, "vram_total_mb": 6144, "pct": 96.0, "action": "kill_sidecar"}
```

## 5. Cross-References

| Dependency | Spec | Status |
|---|---|---|
| Supabase MCP Server | [001-supabase-mcp](../001-supabase-mcp/plan.md) | Implemented |
| Gephi GEXF Exporter | [002-gephi-exporter](../002-gephi-exporter/spec.md) | Implemented |
| ConceptNet Cache | [003-offline-common-sense](../003-offline-common-sense/spec.md) | Implemented |
| SME Constitution | [constitution.md](../../memory/constitution.md) | Active |
