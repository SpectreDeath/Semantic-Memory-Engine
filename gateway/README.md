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
# Build and run the gateway container
cd d:\SME\gateway
docker-compose up -d
```

### Option 3: LM Studio Integration

1. Copy `gateway/mcp.json` to your LM Studio MCP configuration directory
2. Restart LM Studio
3. The Lawnmower Man tools will appear in your agent's tool list

---

## 🔧 Available Tools

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
│   SME ToolFactory         │
│   src/core/factory.py     │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   SME Forensic Toolkit    │
│   Scribe, Scout, Synapse  │
│   Sentiment, Entities...  │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   Knowledge Core          │
│   SQLite + ChromaDB       │
│   10GB+ ConceptNet        │
└───────────────────────────┘
```

---

## 📁 Project Structure

```
gateway/
├── __init__.py          # Package initialization
├── mcp_server.py        # Main MCP server with tool definitions
├── tool_registry.py     # Dynamic tool discovery
├── docker-compose.yml   # Container orchestration
├── Dockerfile           # Container image
├── mcp.json            # LM Studio configuration
└── README.md           # This file
```

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

1. Add the MCP handler in `mcp_server.py`:

```python
@mcp.tool()
def my_new_tool(param1: str) -> str:
    """Description for the LLM."""
    tool = registry.get_tool("my_new_tool")
    result = tool.process(param1)
    return json.dumps(result)
```

1. Test with: `python -m gateway.mcp_server`

---

## 📋 Sprint Status

- [x] Sprint 1: Foundation ✅
  - [x] Tool Registry
  - [x] MCP Server
  - [x] Docker Setup
  - [x] 8 Core Tools
  
- [ ] Sprint 2: Core Capabilities
- [ ] Sprint 3: Advanced Features  
- [ ] Sprint 4: Production Hardening

---

## 🔗 Related

- [SME Documentation](../docs/START_HERE.md)
- [Architecture Analysis](../docs/ARCHITECTURE_IMPROVEMENTS.md)
- [ToolFactory Reference](../src/core/factory.py)

---

### Powered by Project Lawnmower Man • Built on SME Forensic Toolkit
