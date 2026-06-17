# SME Extensions Catalog

**Version:** 2.0.0
**Date:** 2026-03-25

## 🧩 Extension Ecosystem

The Lawnmower Man Gateway supports a modular extension system located in the `extensions/` directory. Each extension is a self-contained plugin defined by a `manifest.json`.

### 📂 Governance & Security

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Epistemic Gatekeeper** | Visualizes trust scores (NTS) and enforces epistemic boundaries. | ✅ Active |
| **Governor** | Central control mechanism for system policies and resource usage. | ✅ Active |
| **Logic Auditor** | Verifies logical consistency of forensic findings. | ✅ Active |
| **Behavior Audit** | Audits agent behavior against defined protocols. | ✅ Active |
| **Forensic Vault** | Secure storage for sensitive evidentiary data. | ✅ Active |

### 🛡️ Tactical & Defense

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Tactical Intelligence Pack** | Specialized tools for analyzing tactical forensic evidence. | ✅ Active |
| **Adversarial Pattern Breaker** | Detects AI-smoothed text using Burstiness and Perplexity variance. | ✅ Active |
| **Adversarial Tester** | Simulates adversarial attacks to test system robustness. | ✅ Active |
| **Immunizer** | Proactive system immunization against detected threat patterns. | ✅ Active |
| **Ghost Trap** | Identifies stealthy or obfuscated processes/signals. | ✅ Active |

### 🧠 Analysis & Audit

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Synthetic Source Auditor** | Detects machine-generated text patterns (SimHash/Burstiness). | ✅ Active |
| **Semantic Auditor** | Deep semantic analysis of corpus consistency. | ✅ Active |
| **Archival Diff** | Comparative analysis of historical vs. current data states. | ✅ Active |
| **Stetho Scan** | Deep system health and diagnostic scanning. | ✅ Active |
| **Mirror Test** | Self-reflective diagnostics for agent cognition. | ✅ Active |

### 🌐 Knowledge & Mapping

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Atlas** | Cartographic mapping of knowledge domains. | ✅ Active |
| **Nur** | Illumination of dark data/knowledge gaps. | ✅ Active |

### 📡 Data & Ingestion

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Harvester** | One-click web ingestion converting URLs to semantic atomic facts. | ✅ Active |
| **Gathering** | Cloud storage integration (Drive, Dropbox, S3, OneDrive). | ✅ Active |
| **ScrapeGraph Harvester** | AI-powered scraping using ScrapeGraphAI graphs. | ✅ Active |
| **Query Engine** | Semantic search and query execution engine. | ✅ Active |

### 🔌 Gateway & Integration

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Gateway** | MCP server and tool registry. | ✅ Active |
| **AI Bridge** | LLM provider integration (Ollama, Langflow, Mock). | ✅ Active |
| **Analysis Core** | Unified analysis engine with multiple modes. | ✅ Active |
| **Data Storage** | Persistent data storage layer. | ✅ Active |
| **NLP Core** | NLP pipeline and text processing. | ✅ Active |
| **Scribe** | Adaptive learning and knowledge recording. | ✅ Active |
| **Validation** | Data validation and schema enforcement. | ✅ Active |
| **Logging** | Centralized logging system. | ✅ Active |
| **Monitoring** | System monitoring and metrics. | ✅ Active |
| **Core Utils** | Core utility functions and helpers. | ✅ Active |

### 🧪 Reference

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Sample Echo** | Reference implementation of an Echo/TPM signing tool. | ✅ Reference |

## 🛠️ Installing Extensions

1. **Drop-in**: Place the extension folder into `extensions/`.
2. **Verify**: Run `python gateway/test_gateway.py` to confirm the registry loads the new plugin.
3. **Config**: Update `config/config.yaml` if the extension requires specific API keys or paths.

## 🧩 Developing Extensions

Create a new folder in `extensions/` with:

1. `manifest.json`: Metadata definition.
2. `plugin.py`: Python module with `on_startup()` hook.

See `extensions/ext_sample_echo/` for a boilerplate.
