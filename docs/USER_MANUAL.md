# 📘 SME Forensic Gateway (Lawnmower Man) — Official User & Operator Manual

Welcome to the **SME Forensic Gateway** User & Operator Manual. This document provides a complete guide to operating, configuring, expanding, and developing against SME v3.0.1+.

---

## 📑 Table of Contents
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Quickstart & Native Launch](#2-quickstart--native-launch)
3. [The Interactive Control Room UI](#3-the-interactive-control-room-ui)
4. [Harvester & Cloud Ingestion Engine](#4-harvester--cloud-ingestion-engine)
5. [Social Intelligence & OSINT Crawlers](#5-social-intelligence--osint-crawlers)
6. [Model Context Protocol (MCP) & FastMCP Server](#6-model-context-protocol-mcp--fastmcp-server)
7. [Database Tier (SQLite WAL & PostgreSQL Nexus)](#7-database-tier-sqlite-wal--postgresql-nexus)
8. [Merkle Audit Engine & Cryptographic Provenance](#8-merkle-audit-engine--cryptographic-provenance)
9. [Command Line Tool Suite (SME CLI)](#9-command-line-tool-suite-sme-cli)
10. [Troubleshooting & Diagnostics](#10-troubleshooting--diagnostics)

---

## 1. System Overview & Architecture

The **Semantic Memory Engine (SME)** is a production-grade MCP Gateway enabling AI Agents (Claude, GPT-4o, Ollama, LangChain, Smolagents, Pydantic-AI) to perform deep forensic analysis, semantic memory ingestion, claim drift detection, and social media OSINT.

```mermaid
graph TD
    Client[AI Agent / MCP Client] <-->|FastMCP JSON-RPC / SSE| Gateway[SME API Gateway - FastAPI Port 8000]
    Gateway <--> UI[Control Room Dashboard - Port 5173]
    Gateway <--> Provider[Unified AI Provider - Local VRAM / Langflow]
    Gateway <--> Database[ForensicNexus - SQLite WAL / PostgreSQL]
    Gateway <--> Audit[Merkle Audit Engine - ED25519 Signatures]
```

### Key Hardware Optimization
- **Single-GPU Optimization**: SME runs efficiently on NVIDIA GTX 1660 Ti (6GB VRAM) or equivalent hardware via `pynvml` telemetry and dynamic model quantization swapping.

---

## 2. Quickstart & Native Launch

### System Requirements
- **Python**: `3.13.x` (Python 3.14 is blocked due to `spacy` C-extensions).
- **Node.js**: `v18.0.0` or higher.
- **Git & C++ Build Tools** (for local native modules).

### Native Launch (30 Seconds)

```bash
# 1. Clone & install workspace in editable mode
cd D:\GitHub\projects\SME
pip install -e .

# 2. Launch the API Gateway / Operator
python -m src.api.main

# 3. Launch the Control Room Frontend (Terminal 2)
cd frontend
npm run dev
```

Visit **[http://localhost:5173](http://localhost:5173)** to access the Control Room.

---

## 3. The Interactive Control Room UI

The Control Room dashboard is built with React 19, Vite, and modern Glassmorphism aesthetics.

### Key Sections:
- **Connections Manager**: Dynamic AI strategy switching (Ollama, Langflow, Mock) with live hardware telemetry (VRAM, CPU, RAM).
- **Live Ingestion Feed**: Real-time streaming log of processed atomic facts, entity markers, and router events.
- **Interactive Knowledge Graph**: 2D force-directed node visualizer ([GraphVisualizer.jsx](file:///D:/GitHub/projects/SME/frontend/src/components/GraphVisualizer.jsx)) for inspecting memory nodes and Merkle audit chains.
- **The Harvester Panel**: Web page scraper converting URLs to atomic semantic facts.
- **API Key Manager**: Create, rotate, and revoke security bearer tokens.
- **Tool Lab**: Test MCP tools interactively from the browser.

---

## 4. Harvester & Cloud Ingestion Engine

SME includes a multi-provider cloud fetcher ([cloud_fetcher.py](file:///D:/GitHub/projects/SME/src/gathering/cloud_fetcher.py)) supporting automatic URL provider detection:

### Supported Storage Links
- **Google Drive**: Shared file and folder links.
- **Dropbox**: Shared public links.
- **OneDrive**: Sharepoint & OneDrive file links.
- **Amazon S3**: Presigned GET URLs.

```python
from src.gathering.cloud_fetcher import CloudFetcher, fetch_sync

# Async Usage
fetcher = CloudFetcher()
result = await fetcher.fetch("https://drive.google.com/file/d/...")
print(result["content"])

# Sync Usage
result = fetch_sync("https://dropbox.com/s/...")
```

---

## 5. Social Intelligence & OSINT Crawlers

The `ext_social_intel` plugin monitors disinformation patterns across major social media networks:

- **Supported Platforms**: Twitter/X, Reddit, Facebook, YouTube, TikTok, Bluesky (AT Protocol), Telegram.
- **Coordinated Botnet Detection**: Pattern recognition analyzing posting intervals, text similarity, and account creation velocities.
- **Sentiment Analysis**: Multi-lingual sentiment scoring and bias indicator detection.

---

## 6. Model Context Protocol (MCP) & FastMCP Server

SME exposes 45+ dynamic extension tools via FastMCP.

### Standard Endpoints:
- `POST /mcp`: JSON-RPC protocol endpoint.
- `GET /sse`: Server-Sent Events stream for long-running forensic tasks.
- `GET /docs`: Interactive Swagger API documentation.

### Connecting Claude Desktop or Cursor:
Add to your `mcpServers` configuration:

```json
{
  "mcpServers": {
    "sme-gateway": {
      "command": "python",
      "args": ["-m", "gateway.mcp_server"]
    }
  }
}
```

---

## 7. Database Tier (SQLite WAL & PostgreSQL Nexus)

SME offers a dual-engine database layer:

### Switching Engines
Set the environment variable:

```bash
# Enable PostgreSQL Nexus
export SME_USE_POSTGRES=true
export POSTGRES_CONNECTION_STRING=postgresql://sme:password@localhost:5432/smedb
```

### PostgreSQL Nexus Capabilities:
- Connection pooling with automatic reconnection retries.
- Production multi-container concurrency support.
- JSONB indexing for forensic event metadata.

---

## 8. Merkle Audit Engine & Cryptographic Provenance

The `AuditEngine` ([audit_engine.py](file:///D:/GitHub/projects/SME/src/logic/audit_engine.py)) maintains a tamper-evident SHA-256 Merkle chain for all forensic operations.

### ED25519 Cryptographic Signatures

```python
from src.logic.audit_engine import AuditEngine

engine = AuditEngine()
engine.log_event("EVIDENCE_INGESTED", actor="agent_alpha", payload={"url": "https://example.com"})

# Generate keypair & sign Merkle root
private_key, public_key = engine.generate_keypair()
signature = engine.sign_merkle_root(private_key)

# Verify signature
assert engine.verify_merkle_signature(public_key, signature) is True
```

---

## 9. Command Line Tool Suite (SME CLI)

SME provides a full-featured CLI accessible via `sme` or `python -m sme_cli.main`.

```bash
# Check system health & VRAM telemetry
sme status

# Run web harvester on target URL
sme harvest https://example.com --output markdown

# Run anomaly audit scanner
sme audit data/sample.csv

# Inspect Merkle audit chain integrity
sme verify-audit
```

---

## 10. Troubleshooting & Diagnostics

- **VRAM Contention**: If VRAM warnings occur, switch AI provider to `Mock` or `Ollama 4-bit` in the Connections Manager.
- **Port Conflicts**: If port 8000 is occupied, run `uvicorn src.api.main:app --port 8001`.
- **Database Locks**: If SQLite locks occur under heavy concurrency, ensure WAL mode is enabled or switch to PostgreSQL (`SME_USE_POSTGRES=true`).
