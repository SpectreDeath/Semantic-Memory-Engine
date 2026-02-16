# SME Extensions Catalog

**Version:** 1.0.0
**Date:** 2026-02-15

## 🧩 Extension Ecosystem

The Lawnmower Man Gateway supports a modular extension system located in the `extensions/` directory. Each extension is a self-contained plugin defined by a `manifest.json`.

### 📂 Governance & Security

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Epistemic Gatekeeper** | Visualizes trust scores (NTS) and enforces epistemic boundaries. | ✅ Active |
| **Governor** | Central control mechanism for system policies and resource usage. | 🟡 Beta |
| **Logic Auditor** | Verifies logical consistency of forensic findings. | ✅ Active |
| **Behavior Audit** | Audits agent behavior against defined protocols. | ✅ Active |
| **Forensic Vault** | Secure storage for sensitive evidentiary data. | ✅ Active |

### 🛡️ Tactical & Defense

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Tactical Intelligence Pack** | Specialized tools for analyzing tactical forensic evidence. | ✅ Active |
| **Adversarial Pattern Breaker** | Detects AI-smoothed text using Burstiness and Perplexity variance. | ✅ v1.0.0 |
| **Adversarial Tester** | Simulates adversarial attacks to test system robustness. | 🟡 Beta |
| **Immunizer** | Proactive system immunization against detected threat patterns. | 🟡 Beta |
| **Ghost Trap** | Identifies stealthy or obfuscated processes/signals. | 🟡 Beta |

### 🧠 Analysis & Audit

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Synthetic Source Auditor** | Detects machine-generated text patterns (SimHash/Burstiness). | ✅ Active |
| **Semantic Auditor** | Deep semantic analysis of corpus consistency. | ✅ Active |
| **Archival Diff** | Comparative analysis of historical vs. current data states. | ✅ Active |
| **Stetho Scan** | Deep system health and diagnostic scanning. | ✅ Active |
| **Mirror Test** | Self-reflective diagnostics for agent cognition. | 🟡 Beta |

### 🌐 Knowledge & Mapping

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Atlas** | Cartographic mapping of knowledge domains. | ✅ Active |
| **Nur** | Illumination of dark data/knowledge gaps. | 🟡 Beta |

### 🧪 Reference

| Extension | Description | Status |
| :--- | :--- | :--- |
| **Sample Echo** | Reference implementation of an Echo/TPM signing tool. | ✅ Reference |

## 🛠️ Installing Extensions

1. **Drop-in**: Place the extension folder into `D:\SME\extensions\`.
2. **Verify**: Run `python gateway/test_gateway.py` to confirm the registry loads the new plugin.
3. **Config**: Update `config/config.yaml` if the extension requires specific API keys or paths.

## 🧩 Developing Extensions

Create a new folder in `extensions/` with:

1. `manifest.json`: Metadata definition.
2. `plugin.py`: Python module with `on_startup()` hook.

See `extensions/ext_sample_echo/` for a boilerplate.
