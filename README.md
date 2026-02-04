# 🌿 Lawnmower Man: Forensic MCP Gateway (v1.2.0)

> **The Semantic Memory Engine (SME) Bridge for Agentic AI.**
> *Now featuring the Epistemic Gatekeeper & Trust Algorithms.*

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-1.2.0_Gatekeeper-green.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular_Plugin-blueviolet.svg)
![Hardware Optimized](https://img.shields.io/badge/Hardware-1660_Ti_6GB-green.svg)

---

## 🚀 Overview

Lawnmower Man is a production-grade **Model Context Protocol (MCP)** Gateway that exposes deep forensic capabilities to LLM agents (like LM Studio, Claude, or OpenAI). It anchors AI reasoning with:
- **Epistemic Trust**: Calculated Trust Scores (Entropy + Burstiness) for all data.
- **Hardware Security**: Simulated TPM enclave for evidence signing.
- **Semantic Memory**: 10GB+ ConceptNet knowledge graph for entity grounding.
- **Synthetic Detection**: Vaults "Grok-style" low-entropy text for counter-intelligence.

## 🛠️ Utility Suite

Our lightweight utility tools are optimized for the NVIDIA GeForce GTX 1660 Ti 6GB VRAM constraints:

### ✅ Data Guard Auditor (`auditor.py`)
- **Purpose**: Outlier detection using PyOD's Isolation Forest
- **Features**: CSV scanning, configurable contamination rates, CLI interface
- **Optimization**: 104 lines, minimal memory footprint
- **Usage**: `python auditor.py data.csv --contamination 0.15`

### ✅ Context Sniffer (`context_sniffer.py`)
- **Purpose**: Project context identification and persona management
- **Features**: File extension detection, keyword scanning, persona mapping
- **Optimization**: 68 lines, under 80-line requirement
- **Usage**: `python context_sniffer.py file.py`

### ✅ Gephi Streaming Bridge (`gephi_bridge.py`)
- **Purpose**: Visual project metadata streaming to Gephi
- **Features**: Node creation, visual mapping, directory-based edges
- **Optimization**: Efficient processing for large codebases
- **Usage**: `python gephi_bridge.py` (requires Gephi running)

---

## 🧱 Modular Architecture (v1.2.0)

The system is split into the **Core Gateway** and **Hot-Swappable Extensions**.

```mermaid
graph TD
    Client[AI Agent] <-->|MCP Protocol| Gateway[Lawnmower Gateway]
    
    subgraph Core [Core Services]
        Gateway <--> Nexus[Nexus DB]
        Gateway <--> TPM[Hardware Enclave]
        Gateway <--> Trust[Gatekeeper Logic]
    end
    
    subgraph Extensions [Extension Layer]
        Gateway -.->|Load| Plugin1[Forensic Echo]
        Gateway -.->|Load| Plugin2[Tactical Pack]
        Gateway -.->|Load| Plugin3[Epistemic Gatekeeper]
    end
```

### 📂 Project Structure

- **`gateway/`**: The core MCP server, `ToolRegistry`, and `SessionManager`.
- **`extensions/`**: Directory for drop-in plugins.
  - **`ext_sample_echo/`**: Reference TPM-signing verification tool.
  - **`ext_tactical_forensics/`**: Specialized IED/CBRN detection pack.
  - **`ext_epistemic_gatekeeper/`**: Folder auditor with Trust Score Heat Maps.
  - **`ext_synthetic_source_auditor/`**: Auto-vaulting for synthetic patterns.
- **`data/`**: Local storage for the 10GB knowledge graph (**Excluded from Git**).

---

## 🛠️ Usage

### 1. Run the Gateway (Production)
```bash
python -m gateway.mcp_server
```
*Exposes the MCP server on stdio for agent connection.*

### 2. Verify System Health
```bash
python gateway/test_gateway.py
```
*Checks core subsystems and verifies plugin loading.*

### 3. Docker Deployment
```bash
docker-compose up lawnmower-gateway
```

---

## 🧩 Creating Extensions

Lawnmower Man supports a standard v1.1.1+ boilerplate for new capabilities.

1. Create a folder in `extensions/` (e.g., `ext_my_tool`).
2. Add a `manifest.json`.
3. Implement `plugin.py` with standard hooks (`on_startup`, `on_ingestion`).

See **`extensions/ext_sample_echo/`** for a complete example.

---

## 🖥️ Hardware Constraints & Optimizations

### NVIDIA GeForce GTX 1660 Ti 6GB VRAM
Our utilities are specifically optimized for the 1660 Ti's 6GB VRAM limitations:

**Memory Management:**
- Lightweight Python libraries (avoid heavy ML frameworks)
- Efficient data processing (streaming vs. batch loading)
- Minimal memory footprint utilities
- CLI-based tools to reduce GUI overhead
- Smart caching and cleanup routines

**Performance Considerations:**
- Single-threaded design for stability
- Optimized for large codebases (1200+ files tested)
- Automatic cleanup of temporary data
- Minimal bandwidth usage for network operations

**Optimization Results:**
- Data Guard Auditor: 104 lines, <5MB memory usage
- Context Sniffer: 68 lines, <2MB memory usage  
- Gephi Bridge: 148 lines, efficient streaming for 1000+ files

## 📦 Requirements

- Python 3.10+ (3.14 compatible)
- `fastmcp`
- `pydantic`
- `faststylometry`
- `statistics` (Standard Lib)

---

_Powered by SimpleMem Architecture_
