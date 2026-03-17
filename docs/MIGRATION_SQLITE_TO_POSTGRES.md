# SQLite to PostgreSQL Migration Guide

## Overview

SME v3.0.0 supports two database backends:
- **SQLite**: Default for local development
- **PostgreSQL**: Required for production multi-container deployments

## When to Use Each

| Use Case | Recommended Backend |
|----------|-------------------|
| Local development | SQLite |
| Single container deployment | SQLite |
| Multi-container production | PostgreSQL |
| Concurrent writes | PostgreSQL |
| High availability | PostgreSQL |

## SQLite Limitations

From `gateway/nexus_db.py`:
> The SQLite Nexus is intended as a local-dev / single-node store. The postgres service in docker-compose.yaml should be promoted to the primary store for multi-container writes; SQLite WAL mode does not scale well when multiple Docker containers share the same file over a volume.

## How to Enable PostgreSQL

### Step 1: Set Environment Variable

```bash
export SME_USE_POSTGRES=true
```

Or in docker-compose.yaml:

```yaml
sme-operator:
  environment:
    - SME_USE_POSTGRES=true
```

### Step 2: Configure Connection String

Set the PostgreSQL connection string:

```bash
export POSTGRES_CONNECTION_STRING=postgresql://user:password@host:5432/database
```

Or in docker-compose.yaml:

```yaml
environment:
  - POSTGRES_CONNECTION_STRING=postgresql://sme_user:sme_password@postgres:5432/sme_nexus
```

### Step 3: Ensure PostgreSQL is Running

The PostgreSQL service must be running and accessible. The docker-compose.yaml already includes a PostgreSQL 15 container:

```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_USER: sme_user
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: sme_nexus
```

## Schema Differences

### SQLite (ForensicNexus)

Uses SQLite with ATTACH for multiple databases:
- `forensic_nexus.db` (primary)
- `storage/laboratory.db` (attached as `lab`)
- `provenance.db` (attached as `prov`)
- `knowledge_core.sqlite` (attached as `core`)

### PostgreSQL (PostgresNexus)

Uses a single database with schemas:
- `lab.forensic_events` - Forensic event tracking
- `prov.source_provenance` - Source reliability tracking
- JSONB columns for flexible metadata

## Data Migration Steps

### Option 1: Fresh Start (Recommended for Development)

1. Start with PostgreSQL enabled
2. The schema is created automatically on first run
3. No migration needed

### Option 2: Export/Import (For Existing Data)

1. **Export from SQLite**:
   ```bash
   sqlite3 data/forensic_nexus.db ".backup forensic_nexus.db"
   ```

2. **Note**: Direct SQLite to PostgreSQL migration is not automatically supported. For production:
   - Consider using tools like `pgloader` for large datasets
   - Or implement custom migration scripts as needed

## Rollback

To revert to SQLite:
```bash
export SME_USE_POSTGRES=false
```

## Connection Pool Settings

PostgreSQL uses connection pooling (from `src/database/postgres_nexus.py`):
- Default min connections: 1
- Default max connections: 10

Adjust via:
```python
get_postgres_nexus(connection_string, min_connections=5, max_connections=20)
```

## Troubleshooting

### Connection Refused

Ensure PostgreSQL container is running:
```bash
docker-compose ps
docker-compose logs postgres
```

### Authentication Failed

Verify credentials match between:
- `POSTGRES_USER`
- `POSTGRES_PASSWORD` 
- `POSTGRES_CONNECTION_STRING`
