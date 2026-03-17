# Environment Variables Reference

## Required Variables

### SME_GATEWAY_SECRET
- **Required**: Yes
- **Default**: None
- **Description**: JWT signing secret for the gateway. Must be a secure 64-character hex string.
- **Example**: `8f2e7a3b9c1d4e6f8a2b5c9d3e7f1a6b4c8d2e5f9a7b3c6d1e8f4a9b2c5d7e3f`
- **Warning**: Do not commit this value. Use Docker secrets or vault in production.

### SME_ADMIN_PASSWORD
- **Required**: Yes
- **Default**: None
- **Description**: Admin password for the /login endpoint.
- **Example**: `SecureAdminPass2026!`
- **Warning**: Must be changed from default if previously used.

### SME_HSM_SECRET
- **Required**: Yes (for production)
- **Default**: None
- **Description**: Hardware Security Module signing seed for evidence integrity.
- **Example**: `HSM_Signing_Seed_2026_Secure`

## Optional Variables

### SME_CORS_ORIGINS
- **Required**: No
- **Default**: `http://localhost:80,http://localhost:5173`
- **Description**: Comma-separated list of allowed CORS origins.
- **Example**: `http://localhost:80,http://localhost:5173,https://example.com`

### SME_DATA_DIR
- **Required**: No
- **Default**: `/app/data` (container) or `./data` (local)
- **Description**: Data directory for SQLite databases and knowledge graphs.

### SME_EXTENSIONS_DIR
- **Required**: No
- **Default**: `./extensions`
- **Description**: Directory containing extension plugins.

### SME_USE_POSTGRES
- **Required**: No
- **Default**: `false`
- **Description**: Enable PostgreSQL backend instead of SQLite.
- **Values**: `true`, `false`, `1`, `0`, `yes`

### POSTGRES_CONNECTION_STRING
- **Required**: When SME_USE_POSTGRES=true
- **Default**: None
- **Description**: PostgreSQL connection string.
- **Example**: `postgresql://sme_user:sme_password@postgres:5432/sme_nexus`

## Database Variables

### POSTGRES_USER
- **Required**: When using docker-compose PostgreSQL
- **Default**: `sme_user`
- **Description**: PostgreSQL username.

### POSTGRES_PASSWORD
- **Required**: When using docker-compose PostgreSQL
- **Default**: `sme_password`
- **Description**: PostgreSQL password.

### POSTGRES_DB
- **Required**: When using docker-compose PostgreSQL
- **Default**: `sme_nexus`
- **Description**: PostgreSQL database name.

## AI Provider Variables

### SME_SIDECAR_URL
- **Required**: No
- **Default**: `http://sme-sidecar:8089`
- **Description**: URL of the AI sidecar service.

### SME_AI_PROVIDER
- **Required**: No
- **Default**: `langflow`
- **Description**: AI provider to use.
- **Values**: `ollama`, `langflow`, `mock`

### OLLAMA_BASE_URL
- **Required**: When using Ollama
- **Default**: `http://ollama:11434`
- **Description**: Ollama API endpoint.

### LANGFLOW_BASE_URL
- **Required**: When using Langflow
- **Default**: `http://langflow:7860`
- **Description**: Langflow API endpoint.

## Hardware Variables

### SME_VRAM_LIMIT_MB
- **Required**: No
- **Default**: `4096`
- **Description**: VRAM limit in MB for GPU operations.

### SME_OFFLOAD_THRESHOLD_MB
- **Required**: No
- **Default**: `3584`
- **Description**: VRAM threshold for model offloading.

## Runtime Variables

### PYTHONPATH
- **Required**: No
- **Default**: `/app` (container)
- **Description**: Python module search path.

### PYTHONUNBUFFERED
- **Required**: No
- **Default**: `1`
- **Description**: Disable Python output buffering for live logging.
