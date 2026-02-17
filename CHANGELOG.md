
# Changelog

## [v2.3.0] - KDnuggets Python Libraries Integration - 2026-02-17

### Summary

Integrated the top Python libraries from KDnuggets' "12 Python Libraries You Need to Try in 2026" article to enhance SME's forensic AI capabilities.

### Added

- **Smolagents** (`smolagents>=1.0.0`): Hugging Face agent framework for building intelligent agents that write code and call tools
- **Pydantic-AI Agent Module** (`src/ai/pydantic_ai_agent.py`): Production-grade agentic framework with type-safe AI responses
- **Polars Forensics Module** (`src/analysis/polars_forensics.py`): High-performance data processing for forensic analysis
- **Smolagents Forensics Module** (`src/ai/smolagents_forensics.py`): Lightweight agent framework with custom SME tools

### Library Status (from KDnuggets Article)

| Library | Status | SME Integration |
| ------- | -------------------- | -------------------------------------------- |
| FastMCP | Already using | MCP server (`gateway/mcp_server.py`) |
| Polars | Already in requirements | Data processing module |
| MarkItDown | Already in requirements | Document conversion |
| Pydantic-AI | Already in requirements | New agent module |
| Smolagents | NEW | Agent framework module |

### Changes in v2.3.0

- **requirements.txt**: Added `smolagents>=1.0.0` under v2.3.0 section
- **v2.1.0 Section**: MarkItDown, Polars, Pydantic-AI already present
- **v2.2.0 Section**: llama-cpp-python, pynvml for hardware awareness

## [v1.2.0] - The Epistemic Gatekeeper - 2026-02-02

### v1.2.0 Overview

Transitioned the platform from a passive "Harvester" to an active "Epistemic Arbiter". This release introduces a unified Trust Scoring engine and strict guardrails against synthetic data pollution.

### Added in v1.2.0

- **Gatekeeper Logic**: New `TrustScorer` class measuring Entropy, Burstiness, and Vault Proximity.
- **Grok Vault**: A repository of known synthetic "pollutant" signatures for proximity matching.
- **Epistemic Gatekeeper Extension**: New `audit_folder_veracity` tool generating JSON Veracity Heatmaps.
- **Synthetic Source Auditor**: New `calculate_burstiness_metric` tool.

### Changed

- **MCP Server**: Injected "Synthetic Signal Guardrail" forcing a bold warning (`**[SYNTHETIC DATA WARNING]**`) if NTS < 50.
- **Nexus DB**: Enhanced with WAL mode for concurrency and "nexus_synthetic_baselines" table.
- **Trust Scoring**: Updated formula to heavily penalize "Entropy Deficits" and "Vault Matches".

### Security

- **Epistemic Humility**: System now actively flags potentially hallucinated or synthetic content.
