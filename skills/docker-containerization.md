---
Domain: DevOps
Version: 1.0.0
Complexity: intermediate
Type: deployment
Category: infrastructure
name: Docker Containerization
Source: SME v3.0.0
Source_File: docker-compose.yaml
---

# Docker Containerization

## Purpose
Deploy and manage the SME (Semantic Memory Engine) stack using Docker containers with auto-healing and health checks.

## Description
SME v3.0.0 uses a multi-container architecture with Docker Compose for orchestration. The stack includes the Operator (core logic), Sidecar (AI bridge), Frontend (Control Room UI), and PostgreSQL Nexus (database).

## Architecture

```
┌─────────────────────────────────────────────┐
│              Docker Compose Stack            │
├─────────────────────────────────────────────┤
│  sme-operator    │ Port 8000  │ Core Logic  │
│  sme-sidecar     │ Port 8089  │ AI Bridge   │
│  sme-frontend    │ Port 5173  │ Control Room │
│  postgres-nexus  │ Port 5432  │ Database    │
└─────────────────────────────────────────────┘
```

## Workflow

### Quick Start
```bash
# Download the blueprint
curl -O https://raw.githubusercontent.com/SpectreDeath/Semantic-Memory-Engine/main/docker-compose.yaml

# Start the stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f sme-operator
```

### Building from Source
```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build sme-operator

# Rebuild without cache
docker-compose build --no-cache
```

### Environment Configuration
```bash
# Copy example environment
cp .env.example .env

# Edit with your secrets
# Required variables:
# - POSTGRES_PASSWORD
# - JWT_SECRET
# - API_KEYS
```

### Health Checks
Each container includes health checks:
- **Operator**: HTTP GET /health on port 8000
- **Sidecar**: HTTP GET /health on port 8089
- **Frontend**: HTTP GET / on port 5173
- **PostgreSQL**: pg_isready command

### Resource Limits
Containers are optimized for 16GB RAM systems:
```yaml
deploy:
  resources:
    limits:
      memory: 4G
    reservations:
      memory: 2G
```

## Examples

### Scaling Services
```bash
# Scale sidecar instances
docker-compose up -d --scale sme-sidecar=3
```

### Debugging
```bash
# Shell into operator container
docker-compose exec sme-operator /bin/bash

# View container resource usage
docker stats

# Inspect network
docker network inspect sme_default
```

### Data Persistence
```bash
# Backup PostgreSQL
docker-compose exec postgres-nexus pg_dump -U sme nexus > backup.sql

# Restore PostgreSQL
cat backup.sql | docker-compose exec -T postgres-nexus psql -U sme nexus
```

## Implementation Notes
- All containers use Python 3.13 base images
- Volume mounts for persistent data (data/, logs/)
- Auto-restart policy: unless-stopped
- Network isolation via Docker networks
- Graceful shutdown handling with signal traps

## Related Skills
- authentication.md - Secure container access
- config-management.md - Environment variables
- error-handling.md - Container error recovery