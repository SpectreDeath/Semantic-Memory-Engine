# 🧠 Semantic Memory Engine (SME)

> **Solving the long-term memory problem for AI models through local, persistence-driven architecture.**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Hardware Profile: Local First](https://img.shields.io/badge/Hardware%20Profile-Local%20First-blueviolet)
![MCP Server](https://img.shields.io/badge/MCP%20Server-Integration-blue)

Welcome to the **Semantic Memory Engine** (formerly SimpleMem Laboratory). This project provides a robust, scalable framework for building persistent, semantic memory systems for AI agents, optimized for local execution.

## 📊 System Architecture

```mermaid
graph TD
    subgraph Layer0 [Layer 0: Ingestion]
        A[Harvester Spider] -->|Markdown| B[Raw Archive]
    end

    subgraph Layer1_2 [Layer 1 & 2: Core]
        B -->|Stream| C[Centrifuge DB]
        C -->|Context| D[Semantic Loom]
    end

    subgraph Layer3_6 [Layer 3 & 6: Intelligence]
        D -->|Atomic Facts| E[Synapse Memory]
        D -->|Stylometric Data| F[Scribe Forensic Engine]
    end

    subgraph Layer5_7 [Layer 5 & 7: Output]
        E -->|Semantic Search| G[Adaptive Scout]
        F -->|Authorship Score| H[Beacon Dashboard]
        G -->|Verified Context| I[LLM Response]
    end

    %% Hardware Optimization Notes
    classDef hardware fill:#f96,stroke:#333,stroke-width:2px;
    class D,E,G hardware;
```

## 📂 Directory Structure

- **`config/`**: Centralized configuration (`config.yaml`).
- **`src/`**: Core tool logic organized by layer.
  - `core/`: Foundation utilities, Centrifuge DB, and Loom distillation.
  - `harvester/`: Web search and content extraction.
  - `scribe/`: Forensic authorship engine.
  - `synapse/`: Memory consolidation.
  - `query/`: Semantic search and adaptive retrieval.
  - `monitoring/`: System health and diagnostics.
  - `orchestration/`: Pipeline management and automation.
  - `analysis/`: Rhetoric and trend analysis.
  - `visualization/`: Dashboards and feedback charts.
  - `networking/`: Connection probes and network analysis.
- **`data/`**: Unified storage for databases, logs, and lexicons.
- **`docs/`**: Comprehensive guides (previously in root).
- **`tests/`**: Verification and validation suites.
- **`legacy/`**: Archive of original flat-file structure (safe to remove after verification).

## 🚀 Getting Started

1. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Paths**:
   Edit `config/config.yaml` to adjust storage locations if necessary.

3. **Run a Tool**:
   Most tools are now importable as modules. To run a specific MCP server:

   ```bash
   python -m src.core.centrifuge
   ```

4. **Explore Documentation**:
   Check `docs/START_HERE.md` for a deep dive into the system capabilities.

## ✨ New Features: Semantic Memory

This upgrade includes **ChromaDB** integration for true semantic search.

- See `src/core/semantic_db.py` for the implementation.
- This allows the `Scout` and `Synapse` layers to associate facts by meaning rather than just keyword matches.

---

_Powered by SimpleMem Architecture_
