
# Changelog

## [v2.3.3] - Project Cleanup & Gap Resolution - 2026-02-21

### Summary

Addressed identified project gaps and cleaned up git working directory. This release includes production-ready infrastructure components and enhanced documentation.

### Added

- **PostgreSQL Nexus** (`src/database/postgres_nexus.py`):
  - Production-grade database layer for multi-container deployments
  - Thread-safe connection pooling with psycopg2
  - Factory function for SQLite/PostgreSQL switching via `SME_USE_POSTGRES` env var
  - Full schema initialization with indexes

- **Governor Client** (`src/monitoring/governor_client.py`):
  - Real-time system resource monitoring
  - CPU, RAM, Disk I/O tracking via psutil
  - GPU monitoring via pynvml (NVIDIA)
  - Threshold checking for automated alerts
  - Snapshot history for trend analysis

- **GhostTrap Client** (`extensions/ext_ghost_trap/ghost_trap_client.py`):
  - Integration module for persistence event detection
  - Query recent events and alerts
  - Check specific paths for flagging
  - Persistence mechanism detection

- **API Documentation**:
  - Added Swagger/OpenAPI endpoints to FastAPI
  - Available at `/api/docs` and `/api/redoc`
  - OpenAPI schema at `/api/openapi.json`

- **Extension Specifications**:
  - `docs/specifications/ghost_trap_spec.md` - Ghost Trap architecture
  - `docs/specifications/epistemic_gatekeeper_spec.md` - Trust scoring algorithm

### Changed

- **.gitignore**: Added entries for build artifacts, IDE folders, and data files
- **Extensions**: Updated all 18 extensions with BasePlugin architecture

### Dependencies

- Added `psycopg2-binary>=2.9.0` for PostgreSQL support

---

## [v2.3.2] - Social Intelligence Crawler & Maintenance - 2026-02-20

### Summary

Added Social Media Intelligence Crawler extension for advanced social media monitoring and disinformation detection. Performed comprehensive project cleanup, documentation updates, and system maintenance.

### Added

- **Social Intelligence Crawler Extension** (`extensions/ext_social_intel/`):
  - Multi-platform social media monitoring (Twitter/X, Reddit, Facebook, YouTube, TikTok)
  - Advanced analytics including sentiment analysis, bot detection, and coordination detection
  - Content moderation with NSFW detection, spam prevention, and hate speech detection
  - Comprehensive API integration with rate limiting and OAuth authentication
  - Real-time disinformation campaign tracking and influencer activity monitoring

### New Files

- **`extensions/ext_social_intel/`** - Complete social media intelligence extension
  - `plugin.py` - Main plugin class with 6 core tools
  - `api_manager.py` - Multi-platform API integration
  - `sentiment_analyzer.py` - Multi-language sentiment analysis
  - `campaign_detector.py` - Bot and coordination pattern detection
  - `content_moderator.py` - Content filtering and moderation
  - `manifest.json` - Extension configuration
  - `README.md` - Comprehensive documentation

### Documentation Updates

- **cSpell Configuration**: Added technical terms configuration to README files
- **Project Documentation**: Updated various documentation files in `docs/` directory
- **Extension Documentation**: Added comprehensive documentation for new extension

### Maintenance & Cleanup

- **Temporary Files**: Removed `test_errors.txt` and `test_output.txt`
- **Code Quality**: Verified all staged changes are ready for release
- **Git Status**: Cleaned up untracked files and prepared for release

### Infrastructure

- **Database**: Added forensic_nexus.db and provenance.db to project structure
- **Storage**: Organized data storage directory structure
- **Extensions**: Added new extension to the extension ecosystem

---

## [v2.3.1] - Security Hardening & Infrastructure Audit - 2026-02-18

### Summary

Full 26-point security and infrastructure audit of the SME container stack. Addressed
critical networking bugs, security vulnerabilities, thread-safety issues, Windows-path
portability problems, and production-readiness gaps across the backend, gateway, and
frontend layers.

### Critical Fixes

- **`src/ai/sidecar.py`** — Fixed `uvicorn.run()` binding `127.0.0.1` → `0.0.0.0`;
  the sidecar was completely unreachable from other containers on the Docker network.
  Also replaced hardcoded mock entity extraction with a real HTTP call to the operator's
  `link_entities` tool, with a word-tokenizer noun-phrase fallback.
- **`gateway/mcp_server.py`** — Removed `asyncio.run()` at module import time (crashes
  when an event loop is already running); replaced with try/except RuntimeError that
  falls back to `loop.create_task()` or `loop.run_until_complete()`. Removed hardcoded
  mock data ("Administrative Account", "Perimeter Breach") from `entity_extractor` tool.

### Security Fixes

- **`gateway/auth.py`** — Replaced deprecated `datetime.utcnow()` with
  `datetime.now(timezone.utc)`. `SECRET_KEY` now logs a CRITICAL warning if not set
  via env var; insecure hardcoded fallback removed. Added thread-safe singleton lock.
- **`gateway/hardware_security.py`** — HSM seed now loaded from `SME_HSM_SECRET` env
  var with CRITICAL log if missing; hardcoded seed removed. Thread-safe singleton lock.
- **`gateway/rate_limiter.py`** — Added `threading.Lock()` for thread-safe token-bucket
  operations. Thread-safe singleton creation.
- **`src/api/main.py`** — CORS wildcard (`allow_origins=["*"]`) replaced with
  `SME_CORS_ORIGINS` env var (comma-separated list), defaulting to
  `localhost:80,localhost:5173`. Fixed simulated WebSocket latency metric with real
  `psutil.disk_io_counters()` measurement.

### Infrastructure & Portability

- **`gateway/nexus_db.py`** — Fixed hardcoded Windows path `d:/SME/data` (broke in
  Docker Linux containers). Now resolves: explicit arg → `SME_DATA_DIR` env var →
  `Path(__file__).parent.parent / "data"`. Thread-safe singleton lock added. TODO
  comment added for future Postgres migration.
- **`docker-compose.yaml`** — Complete rewrite:
  - Added `autoheal` service (willfarrell/autoheal) for healthcheck-triggered restarts.
  - `depends_on` upgraded to `condition: service_healthy` for sidecar and postgres.
  - Added `healthcheck` to postgres (`pg_isready`).
  - Named networks added: `frontend-net`, `backend-net`, `monitoring-net`.
  - All secrets injected as env vars (`SME_GATEWAY_SECRET`, `SME_ADMIN_PASSWORD`,
    `SME_HSM_SECRET`, `SME_CORS_ORIGINS`, `SME_DATA_DIR`, `SME_VRAM_LIMIT_MB`,
    `SME_OPERATOR_URL`).
  - Frontend port changed 5173 → 80 (nginx production build).
  - Removed `CHOKIDAR_USEPOLLING` (dev-server-only flag; irrelevant to nginx).
  - Added clarifying comment: `memory: 4G` caps system RAM, not VRAM.
- **`pyproject.toml`** — Version bumped 2.1.0 → 2.3.0. Added missing deps:
  `smolagents`, `llama-cpp-python`, `pynvml`, `fastmcp`, `PyJWT`, `fastapi`,
  `uvicorn`, `httpx`. Fixed package discovery to use `[tool.setuptools.packages.find]`
  with proper `include` globs.

### Frontend — Production Build

- **`Dockerfile.frontend`** — Rewrote as two-stage build: `node:20-alpine` builder
  (`npm ci --frozen-lockfile` + `npm run build`) → `nginx:alpine` production image.
- **`frontend/nginx.conf`** *(new)* — SPA routing (`try_files`), `/api/` and `/ws/`
  reverse-proxy to sme-operator, WebSocket Upgrade headers, gzip compression,
  1-year cache for hashed assets, no-cache for `index.html`.
- **`frontend/vite.config.js`** — Added `server.host: true`, `server.port: 5173`,
  and dev-proxy for `/api` and `/ws` routes.
- **`frontend/package.json`** — Added `react-router-dom ^7.0.0` and `zustand ^5.0.0`.
  `npm install` run; `lodash-es` prototype-pollution vuln patched via `npm audit fix`.

### New Files

- **`.env.example`** — Documents all required secrets with generation commands.
- **`tests/test_extension_matrix.py`** — Parametrized pytest suite covering all 18
  extension plugins: discovery, tool schema validation, handler callability.

### Known Acceptable Vulnerabilities (frontend, `npm audit`)

| Package | Advisory | Why acceptable |
| --- | --- | --- |
| `ajv < 8.18.0` | ReDoS with `$data` option ([GHSA-2g4f-44pwh-qvx6](https://github.com/advisories/GHSA-2g4f-44pwh-qvx6)) | Dev-only (eslint toolchain); not present in the nginx production image. No upstream fix available. |
| `got < 11.8.5` via `react-force-graph` | UNIX socket redirect ([GHSA-pfrx-2qq88-qq97](https://github.com/advisories/GHSA-pfrx-2qq88-qq97)) | Runs in browser context only; browsers cannot open UNIX sockets, so the redirect path is not reachable. Fix requires a breaking downgrade of `react-force-graph`. |

### Known Limitations / Future Work

- `validate_access()` in `gateway/mcp_server.py` is defined but not called by tool
  handlers — enforcing it would require per-tool auth wiring (tracked separately).
- Postgres as primary store (replacing SQLite Nexus) — documented as TODO in
  `gateway/nexus_db.py`.

---

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
