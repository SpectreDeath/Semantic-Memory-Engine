# SME Forensic Gateway (Lawnmower Man) v3.0.1 — User Manual
> **Production-Grade MCP Forensic Gateway, Social Intelligence Crawler & Control Room UI**

---

## 📋 Table of Contents
1. [Overview & Architecture](#overview--architecture)
2. [Installation & Requirements](#installation--requirements)
3. [Service Startup & Primary Entry Points](#service-startup--primary-entry-points)
4. [Interactive Control Room UI Guide](#interactive-control-room-ui-guide)
5. [Social Intelligence & OSINT Crawler](#social-intelligence--osint-crawler)
6. [Forensic Intelligence Suite](#forensic-intelligence-suite)
7. [Hot-Swappable Extension Engine](#hot-swappable-extension-engine)
8. [FastAPI & FastMCP Tool API Reference](#fastapi--fastmcp-tool-api-reference)
9. [Hardware Optimization (GTX 1660 Ti 6GB VRAM)](#hardware-optimization-gtx-1660-ti-6gb-vram)
10. [Troubleshooting & Diagnostics](#troubleshooting--diagnostics)

---

## 🏛️ Overview & Architecture

**SME Forensic Gateway** (codename *Lawnmower Man*) provides a production-grade Model Context Protocol (MCP) gateway, AI operator bridge, and forensic investigation workbench.

It combines real-time social media intelligence, epistemic trust scoring, watermark/ghost account detection, and web harvesting with an interactive React/Vite Glassmorphism dashboard.

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      AI Agent / MCP Client (IDE)                       │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ MCP JSON-RPC
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                   SME Gateway Operator (Python 3.13)                   │
 ├───────────────────────────────────┬────────────────────────────────────┤
 │      Epistemic Gatekeeper         │      Social Intel Crawler          │
 ├───────────────────────────────────┼────────────────────────────────────┤
 │      Watermark & Ghost Traps      │      6D MIMO Traffic Router        │
 └─────────────────┬─────────────────┴──────────────────┬─────────────────┘
                   │ WebSocket (/ws/diagnostics)        │ REST / SQL
                   ▼                                    ▼
 ┌───────────────────────────────────┐    ┌───────────────────────────────┐
 │ Control Room Dashboard (Port 5173)│    │ PostgreSQL Nexus / SQLite DB  │
 └───────────────────────────────────┘    └───────────────────────────────┘
```

---

## ⚡ Installation & Requirements

### System Requirements
- **Python**: `3.13` (recommended)
- **Node.js**: `>=18.0` & `npm` (for Control Room UI)
- **Database**: SQLite WAL or PostgreSQL 15+
- **GPU (Optional)**: NVIDIA GTX 1660 Ti 6GB VRAM or higher

### Quick Setup
```bash
# Clone & install Python package in editable mode
git clone https://github.com/SpectreDeath/SME.git
cd SME
pip install -e .

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 🚀 Service Startup & Primary Entry Points

### 1. API Gateway / Operator (Backend)
```bash
python -m src.api.main
```
*Launches the FastAPI operator process and MCP gateway on port `8000`.*

### 2. Interactive Control Room UI (Frontend)
```bash
cd frontend
npm run dev
```
*Serves the web dashboard on `http://localhost:5173`.*

### 3. SME CLI Tool Suite
```bash
# Launch CLI main menu
sme

# Direct command execution
python -m sme_cli.main --help
```

---

## 🕹️ Interactive Control Room UI Guide

The Control Room UI (`http://localhost:5173`) features four primary panels:

### 1. Connections Manager
- **Dynamic AI Strategy**: Hot-swap between Langflow, Ollama, OpenAI, or Mock providers.
- **Hardware Telemetry**: Live meters for GPU VRAM, CPU utilization, and RAM allocation.

### 2. The Harvester Panel
- **Cloud Ingestion**: Ingest documents directly from Google Drive, Dropbox, OneDrive, and AWS S3.
- **Semantic Scraper**: Convert arbitrary web URLs into structured markdown facts with JS rendering.

### 3. Social Intelligence Crawler
- Track target handles across Twitter/X, Reddit, TikTok, and Telegram.
- Real-time sentiment metrics and automated bot classification.

### 4. Epistemic Trust Map
- Visualize knowledge graph confidence scores, source provenance, and synthetic data flags.

---

## 🕵️ Social Intelligence & OSINT Crawler

SME includes a multi-platform crawler capable of detecting automated disinfo campaigns:

```bash
# Run social intelligence audit from CLI
python -m src.utils.social_crawler --target "@suspect_handle" --depth 2
```

### Metrics Tracked
- **Epistemic Trust Score ($0.0 - 1.0$)**: Weighted evaluation of source domain authority, historical accuracy, and cross-reference validation.
- **Bot/Ghost Classification**: Stylometric analysis (`faststylometry`) flagging synthetic text patterns and bot automation artifacts.

---

## 🔬 Forensic Intelligence Suite

SME ships with specialized forensic tools:

### Data Guard Auditor (`src/utils/auditor.py`)
Uses PyOD Isolation Forest to detect tabular data anomalies:
```bash
python src/utils/auditor.py data/results/data.csv --contamination 0.15
```

### Context Sniffer (`src/utils/context_sniffer.py`)
Scans repositories for persona footprints, secret keys, and project contexts:
```bash
python src/utils/context_sniffer.py target_file.py
```

### Gephi Knowledge Graph Bridge (`src/utils/gephi_bridge.py`)
Exports network graphs for Gephi visualization:
```bash
python src/utils/gephi_bridge.py --mode trust
```

---

## 🧩 Hot-Swappable Extension Engine

Plugins are located in `extensions/` and dynamically loaded by the gateway at boot:

### Available Extensions
- `ext_sample_echo`: TPM cryptographic signature verification.
- `ext_tactical_forensics`: CBRN/IED tactical intelligence parser.
- `ext_epistemic_gatekeeper`: Trust Score heatmaps and directory auditing.
- `ext_synthetic_source_auditor`: Auto-vaulting synthetic content.

### Creating a New Extension
1. Create `extensions/ext_my_plugin/`.
2. Add `manifest.json`:
   ```json
   {
     "id": "ext_my_plugin",
     "name": "Custom Audit Plugin",
     "version": "1.0.0",
     "entry_point": "plugin.py"
   }
   ```
3. Implement `on_startup` and `on_ingestion` hooks in `plugin.py`.

---

## 📖 FastAPI & FastMCP Tool API Reference

### Health & Telemetry
- `GET /health`: Overall system health status.
- `WS /ws/diagnostics`: Live telemetry websocket feed.

### Harvester REST Endpoints
- `POST /api/v1/harvester/ingest`: Trigger URL or cloud file ingestion.
- `GET /api/v1/harvester/jobs/{job_id}`: Fetch status of background ingestion job.

### Exposed FastMCP Tools
- `ingest_url`: Scrape and atomize web page content.
- `audit_trust_score`: Calculate epistemic trust for a text payload.
- `detect_watermarks`: Scan text for invisible zero-width watermarks.

---

## 🖥️ Hardware Optimization (GTX 1660 Ti 6GB VRAM)

SME is explicitly optimized to execute within **6GB VRAM** limits:
- **Streaming Pipeline**: Micro-chunking payloads prevents memory spikes.
- **Model Offloading**: VRAM allocated only during active inference calls.
- **Process Isolation**: Prevents memory leaks across prolonged operator sessions.

---

## 🔧 Troubleshooting & Diagnostics

| Problem | Cause | Solution |
|---|---|---|
| `5173 Connection Refused` | Frontend dev server not running | Run `cd frontend && npm run dev` |
| `PostgreSQL Connection Failed` | DB service down or misconfigured | Fall back to SQLite WAL mode via `.env` setting |
| `Extension Load Warning` | Invalid `manifest.json` schema | Run `python -m gateway.test_gateway` to pinpoint error |
