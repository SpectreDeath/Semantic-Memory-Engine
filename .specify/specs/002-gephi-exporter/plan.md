# Plan: Gephi-Ready GEXF Exporter — Bipartite Deep-Stream

## 1. Architecture

```
                     ┌──────────────────────────┐
   /stream-forensics │  gephi_export_tool.py    │  gephi_export
   ─────────────────►│  (FastMCP Server)        │◄──────────────
                     │                          │
                     │  stream_forensics()      │
                     │  ├─ query Supabase       │
                     │  ├─ build bipartite      │
                     │  ├─ check VRAM watchdog  │
                     │  └─ push to GephiREST    │
                     └──────────┬───────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                  ▼
    ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
    │ Supabase    │   │ Gephi        │   │ VRAM         │
    │ threat_leads│   │ :8080        │   │ Watchdog     │
    │ (MCP)       │   │ (streaming)  │   │ (pynvml)     │
    └─────────────┘   └──────────────┘   └──────────────┘
```

The tool resides in `src/tools/gephi_export_tool.py`. It wraps `src/utils/gephi_bridge.py` for legacy export modes and adds the new `stream_forensics` tool with bipartite logic and VRAM-aware chunking.

## 2. Technical Implementation

### 2.1 Bipartite Graph Construction

1. **Pass 1 — Target Nodes**: Page through `threat_leads` (1,000 rows/page). For each row create a **Target** node with attributes: `probability_score`, `source_origin`, `confidence_score`, `first_seen`, `incident_type`, `ai_verdict`, `node_class="target"`.
2. **Pass 2 — Footprint Extraction**: For each Target, extract secondary artifacts (aliases, IPs, fingerprints) and create deduplicated **Footprint** nodes with `node_class="footprint"`.
3. **Pass 3 — Edges**:
   - Target → Footprint (owns)
   - Target ↔ Target (co-occurrence when sharing ≥ 1 Footprint, edge weight = shared count).

### 2.2 Chunked Streaming with VRAM Guard

```python
CHUNK_SIZE = 5000  # nodes per chunk

for chunk in paginate_nodes(CHUNK_SIZE):
    if chunk_index > 0:
        vram = get_vram_usage()      # call pynvml
        if vram >= CAUTION_MB:       # 5800 MB
            wait_and_retry(retries=3, delay=10)
    stream_chunk_to_gephi(chunk)
```

### 2.3 Dual Output Modes

| Mode | Trigger | Output |
|---|---|---|
| File export | `gephi_export(mode=...)` | `.gexf` file in `data/exports/` |
| Live stream | `stream_forensics(query=...)` | Push to Gephi REST `localhost:8080` |

## 3. Files To Create/Modify

| Action | File | Description |
|---|---|---|
| MODIFY | `src/tools/gephi_export_tool.py` | Add `stream_forensics` tool, bipartite logic, VRAM guard |
| MODIFY | `config/aionui_settings.json` | Add `/stream-forensics` command binding |
| MODIFY | `.specify/specs/002-gephi-exporter/spec.md` | Updated with bipartite requirements |
| MODIFY | `.specify/specs/002-gephi-exporter/plan.md` | This revised plan |
| NEW | `config/sme_forensic_workspace.gephi` | Pre-configured Gephi workspace template |

## 4. Verification Plan

### Automated

- **Syntax check**: `python -c "import ast; ast.parse(open('src/tools/gephi_export_tool.py').read())"`
- **JSON config check**: `python -c "import json; json.load(open('config/aionui_settings.json'))"`

### Manual

1. Run `python src/tools/gephi_export_tool.py` — confirm MCP server starts without errors.
2. From AionUi chat: type `/stream-forensics` — confirm bipartite graph appears in Gephi (or `.gexf` file is saved if Gephi is offline).
3. Verify node attributes in Gephi: right-click any node → Data Laboratory → confirm `probability_score`, `source_origin`, `node_class` columns exist.
4. Test VRAM guard: with >5000 mock nodes, confirm the tool logs a VRAM check before continuing.

## 5. VRAM/RAM Impact

| Component | VRAM | RAM |
|---|---|---|
| `gephi_export_tool.py` (streaming) | 0 MB | ~50 MB baseline, ~100 MB peak during 5k chunk |
| Gephi (rendering bipartite) | ≤ 512 MB | ~800 MB |
| VRAM guard poll | 0 MB | 0 MB (inline pynvml call) |
