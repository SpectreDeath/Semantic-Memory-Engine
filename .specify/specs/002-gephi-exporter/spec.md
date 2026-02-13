# Spec: Gephi-Ready GEXF Exporter — Bipartite Deep-Stream

## 1. Objective

Develop a memory-efficient generator for producing `.gexf` (Graph Exchange XML Format) files from the `threat_leads` table in Supabase. This tool will enable detailed relationship mapping of threat actors in external forensic platforms like Gephi.

### 1.1 Bipartite Deep-Stream Extension

Extend the exporter with a **bipartite graph model** and **live streaming** capability:
- **Bipartite Logic**: Differentiate between **Target nodes** (primary threat actors) and **Footprint nodes** (secondary artifacts such as IPs, aliases, tool fingerprints).
- **Live Push**: Support real-time streaming to a running Gephi instance via the Graph Streaming plugin, in addition to `.gexf` file export.
- **VRAM-Aware Chunking**: Coordinate with the VRAM Watchdog to pause streaming when GPU memory approaches the CAUTION threshold.

## 2. Environment Compliance

- **Runtime**: Python 3.14 (Main Runtime).
- **Justification**: This process handles file system I/O and dashboard integration, which reside in the 3.14 environment. It avoids conflicts by querying Supabase via the standardized bridge logic.

## 3. Hardware Guardrails (GTX 1660 Ti)

- **Constraint**: The generator must be memory-efficient.
- **Implementation**: Use a streaming XML generation approach (e.g., `lxml.etree.xmlfile` or a manual string builder with buffered writes).
- **Rule**: Do not load the entire `threat_leads` dataset into RAM.
- **Chunked Stream** (NEW): If node count exceeds **5,000**, the tool must:
  1. Pause streaming after each 5,000-node chunk.
  2. Query the VRAM Watchdog for current usage.
  3. Proceed only if usage is below **5,800 MB** (CAUTION threshold).
  4. If above threshold, wait 10 seconds and re-check (up to 3 retries), then abort with an alert if still above.

## 4. Functional Requirements

### 4.1 Node Types (Bipartite Model)

| Type | Label | Color | Description |
|---|---|---|---|
| **Target** (Primary) | Threat actor name | 🔴 Red | One node per unique `threat_leads` entry |
| **Footprint** (Secondary) | Artifact value | 🔵 Blue | Derived from actor's IPs, aliases, tool fingerprints |

### 4.2 Edges

- **Target ↔ Footprint**: Every Target is connected to its own Footprint nodes.
- **Target ↔ Target**: Implicit link when two Targets share a common Footprint (co-occurrence edge, weight = number of shared footprints).

### 4.3 Node Attributes

Every node must include:
- `probability_score` (float) — from `threat_leads.confidence_score`
- `source_origin` (string) — from `threat_leads.source` or `threat_leads.incident_type`
- `confidence_score` (float)
- `first_seen` (timestamp)
- `incident_type` (string)
- `ai_verdict` (string)
- `node_class` (string) — `"target"` or `"footprint"`

### 4.4 AionUi Command Binding

- **Command**: `/stream-forensics`
- **Behaviour**: Triggers a **live push** to Gephi (via `gephistreamer` GephiREST) instead of only saving a `.gexf` file.
- **Fallback**: If Gephi is not reachable on `localhost:8080`, save to `.gexf` and notify the user.

## 5. UI Integration

- **Platform**: AionUi (via MCP tool) + Streamlit fallback.
- **Components**:
  - MCP tool `stream_forensics` — live Gephi push from AionUi chat.
  - MCP tool `gephi_export` — file-based `.gexf` export (existing).
  - MCP tool `gephi_list_exports` — list past exports (existing).
  - Streamlit: 'Download Gephi Export' button (unchanged).

## 6. Cross-References

| Dependency | Spec | Status |
|---|---|---|
| Supabase MCP Server | [001-supabase-mcp](../001-supabase-mcp/plan.md) | Implemented |
| VRAM Watchdog | [004-aionui-command-center](../004-aionui-command-center/spec.md) | Implemented |
| SME Constitution | [constitution.md](../../memory/constitution.md) | Active |
