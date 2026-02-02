
# Changelog

## [v1.2.0] - The Epistemic Gatekeeper - 2026-02-02

### Summary
Transitioned the platform from a passive "Harvester" to an active "Epistemic Arbiter". This release introduces a unified Trust Scoring engine and strict guardrails against synthetic data pollution.

### Added
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
