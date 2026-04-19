# 🌿 Lawnmower Man Gateway

> **The Agent Interface Layer for the Semantic Memory Engine**

Project Lawnmower Man is the MCP (Model Context Protocol) gateway that exposes SME's forensic toolkit capabilities to LLM agents like those in LM Studio.

---

## 🚀 Quick Start

### Option 1: Direct Python

```bash
# From SME root directory
cd d:\SME
pip install fastmcp
python -m gateway.mcp_server
```

### Option 2: Docker

```bash
# Build and run the gateway container (from SME root)
cd d:\SME
docker-compose up gateway -d
```

### Option 3: LM Studio Integration

1. Copy `gateway/mcp.json` to your LM Studio MCP configuration directory
2. Restart LM Studio
3. The Lawnmower Man tools will appear in your agent's tool list

---

## 🔧 Available Tools

### Core Tools

| Tool | Category | Description |
|------|----------|-------------|
| `verify_system` | Diagnostics | Check CPU, RAM, database status |
| `semantic_search` | Query | Vector similarity search |
| `query_knowledge` | Query | Knowledge graph lookup |
| `save_memory` | Memory | Persist facts to storage |
| `get_memory_stats` | Diagnostics | Storage statistics |
| `analyze_authorship` | Forensics | Linguistic fingerprinting |
| `analyze_sentiment` | Analysis | Emotion detection |
| `list_available_tools` | Utility | Tool discovery |

### V-Index Pipeline (LLM as Database)

| Tool | Category | Description |
|------|----------|-------------|
| `extract_triplets_tool` | Extraction | Extract (Entity, Relation, Target) triples |
| `vindex_inject_tool` | Injection | Inject triplets via [V-INDEX] tokens |
| `probe_concept_tool` | Analysis | Probe model weights for concepts |
| `knn_search_tool` | Retrieval | k-Nearest Neighbor knowledge search |
| `trust_evaluate_tool` | Trust | Evaluate node trust score |
| `hallucination_block_tool` | Trust | Block hallucination via trust filtering |
| `export_activations_tool` | Export | Export to GraphML/CSV/GEXF |
| `stream_activations_tool` | Export | Stream to Gephi via WebSocket/HTTP |
| `poseidon_test_tool` | IDE | Inject fact & verify with Atlantis Test |

---

## 📁 Project Structure

```
gateway/
├── __init__.py              # Package initialization
├── mcp_server.py            # Main MCP server with tool definitions
├── tool_registry.py         # Dynamic tool discovery
├── docker-compose.yml       # Container orchestration
├── Dockerfile               # Container image
├── mcp.json                # LM Studio configuration
│
├── # V-Index Pipeline (LLM as Database)
├── feature_prober.py        # Model weight probing (transformer_lens)
├── triplet_harvester.py     # (Entity, Relation, Target) extraction
├── vindex_overlay.py        # Prompt patching with [V-INDEX]
├── graph_walk.py            # KNN retrieval (0.38ms/query optimized)
├── epistemic_trust.py       # Trust scoring & hallucination blocking
├── weight_exporter.py       # GraphML/CSV/GEXF export
├── activation_streamer.py   # Gephi WebSocket/HTTP streaming
└── vscode_explorer.py       # VS Code Weight Explorer integration
```

---

## 🏗️ Architecture

```
LLM Agent (LM Studio)
        │
        ▼ MCP Protocol
┌───────────────────────────┐
│   Lawnmower Man Gateway   │
│   gateway/mcp_server.py   │
└───────────────────────────┘
        │
        ▼ Direct Python API
┌───────────────────────────┐
│   V-Index Pipeline        │
│   graph_walk.py           │
│   epistemic_trust.py      │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   Knowledge Core          │
│   Graph Walk KNN          │
│   Trust Scoring           │
└───────────────────────────┘
        │
        ▼ Gephi Visualization
┌───────────────────────────┐
│   Gephi Streaming Plugin  │
│   Real-time Graph          │
└───────────────────────────┘
```

---

## ⚡ V-Index Pipeline (Karpathy Loop)

Implements "LLM as a Database" paradigm using Karpathy Loop methodology.

### Phase 1: V-Index Ingestion

```python
from gateway.triplet_harvester import extract_triplets_tool

# Extract (Entity, Relation, Target) triples
result = extract_triplets_tool("The SME was created by the research team.")
# Returns: [(The SME, created_by, the research team)]
```

### Phase 2: Graph Walk Retrieval

```python
from gateway.graph_walk import knn_search_tool

# k-Nearest Neighbor search (0.38ms/query)
results = knn_search_tool("semantic memory creation", k=5)
```

### Phase 3: Trust Validation

```python
from gateway.epistemic_trust import hallucination_block_tool

# Block hallucination at trust < 0.25
result = hallucination_block_tool(walk_results)
# Returns: {blocked: True/False, action: "proceed" | "force_backtrack"}
```

### Phase 4: Gephi Visualization

```python
from gateway.activation_streamer import GephiHTTPStreamer

# Stream to Gephi (HTTP REST API)
streamer = GephiHTTPStreamer()
streamer.stream_node(StreamNode(id="L1_N1", label="neuron", size=2.0))
```

---

## 🔧 Configuration

### Trust Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DEFAULT_TRUST_THRESHOLD` | 0.6 | Accuracy-critical tasks |
| `HALLUCINATION_BLOCK_THRESHOLD` | 0.25 | Block below this |

### Trust Weights

- source_diversity: 30%
- source_type: 25%
- citation: 20%
- recency: 15%
- verification: 10%

---

## 🔄 Development

### Adding a New Tool

1. Add the tool definition to `tool_registry.py`:

```python
"my_new_tool": ToolDefinition(
    name="my_new_tool",
    description="What it does",
    factory_method="create_my_tool",  # Must exist in ToolFactory
    category="analysis",
    parameters={"param1": "str"}
)
```

2. Add the MCP handler in `mcp_server.py`:

```python
@mcp.tool()
def my_new_tool(param1: str) -> str:
    """Description for the LLM."""
    tool = registry.get_tool("my_new_tool")
    result = tool.process(param1)
    return json.dumps(result)
```

3. Test with: `python -m gateway.mcp_server`

---

## 📋 Sprint Status

- [x] Sprint 1: Foundation ✅
  - [x] Tool Registry
  - [x] MCP Server
  - [x] Docker Setup
  - [x] 8 Core Tools

- [x] V-Index Pipeline ✅
  - [x] Triplet Extraction
  - [x] KNN Retrieval (optimized 0.38ms)
  - [x] Trust Scoring
  - [x] Gephi Streaming
  - [x] VS Code Integration

- [ ] Production Hardening

---

## 📖 Related Documentation

- [V-Index Workflow Skill](../.kilo/skills/vindex-workflow/SKILL.md)
- [Karpathy Loop Plan](../LLMs%20as%20Queryable%20Databases%20Karpthy%20plan.md)
- [SME Documentation](../docs/START_HERE.md)
- [Architecture Analysis](../docs/ARCHITECTURE_IMPROVEMENTS.md)
- [ToolFactory Reference](../src/core/factory.py)

---

### Powered by Project Lawnmower Man • Built on SME Forensic Toolkit