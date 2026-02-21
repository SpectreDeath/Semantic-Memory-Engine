"""
PostgreSQL Nexus - Production-grade database layer for multi-container deployment.

This module provides a PostgreSQL-backed alternative to the SQLite Nexus.
PostgreSQL is required for production deployments where multiple Docker
containers need to write to the database concurrently.

Usage:
    # Switch from SQLite to PostgreSQL by setting environment variable:
    export SME_USE_POSTGRES=true
    export POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:5432/db

Or configure in docker-compose.yaml environment section.
"""

import os
import threading
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("lawnmower.nexus.postgres")

# Connection string from environment
POSTGRES_CONNECTION_STRING = os.environ.get(
    "POSTGRES_CONNECTION_STRING",
    os.environ.get("DATABASE_URL", "")
)


class PostgresNexus:
    """
    PostgreSQL-backed forensic database layer.
    
    Provides the same interface as ForensicNexus but with PostgreSQL
    for production multi-container deployments.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        self.connection_string = connection_string or POSTGRES_CONNECTION_STRING
        
        if not self.connection_string:
            raise ValueError(
                "PostgreSQL connection string not provided. "
                "Set POSTGRES_CONNECTION_STRING or DATABASE_URL environment variable."
            )
        
        # Initialize connection pool
        self.pool = pool.ThreadedConnectionPool(
            min_connections,
            max_connections,
            self.connection_string
        )
        logger.info("PostgreSQL Nexus: Connection pool initialized")
        
        # Initialize schema
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        schema_sql = """
            -- Lab forensic events table
            CREATE TABLE IF NOT EXISTS lab.forensic_events (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                tool_name VARCHAR(255) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                target TEXT,
                confidence FLOAT,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Source provenance table
            CREATE TABLE IF NOT EXISTS prov.source_provenance (
                id SERIAL PRIMARY KEY,
                source_id VARCHAR(255) UNIQUE NOT NULL,
                reliability_tier VARCHAR(50),
                acquisition_method VARCHAR(100),
                first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_forensic_events_timestamp 
                ON lab.forensic_events(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_forensic_events_tool 
                ON lab.forensic_events(tool_name);
            CREATE INDEX IF NOT EXISTS idx_source_provenance_id 
                ON prov.source_provenance(source_id);
            
            -- Enable JSONB indexing
            CREATE INDEX IF NOT EXISTS idx_forensic_events_metadata 
                ON lab.forensic_events USING GIN(metadata);
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                conn.commit()
            logger.info("PostgreSQL Nexus: Schema initialized")
        except Exception as e:
            logger.error(f"PostgreSQL Nexus: Schema init failed: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Run a query and return results as dicts."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"PostgreSQL Query Error: {e}\nSQL: {sql}")
            return []

    def execute(self, sql: str, params: tuple = ()):
        """Execute a write operation."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                conn.commit()
        except Exception as e:
            logger.error(f"PostgreSQL Execution Error: {e}\nSQL: {sql}")
            raise

    def get_unified_forensic_feed(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Cross-DB JOIN: Link forensic events to their source reliability.
        """
        sql = """
            SELECT
                e.timestamp,
                e.tool_name,
                e.event_type,
                e.target,
                e.confidence,
                p.reliability_tier,
                p.acquisition_method
            FROM lab.forensic_events e
            LEFT JOIN prov.source_provenance p ON e.target = p.source_id
            ORDER BY e.timestamp DESC
            LIMIT %s
        """
        return self.query(sql, (limit,))

    def get_status(self) -> Dict[str, Any]:
        """Return the status of the PostgreSQL connection."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version() as version")
                    version = cur.fetchone()
                    
                    cur.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            n_live_tup as row_count
                        FROM pg_stat_user_tables
                        ORDER BY n_live_tup DESC
                        LIMIT 10
                    """)
                    tables = cur.fetchall()
                    
                    return {
                        "backend": "PostgreSQL",
                        "version": version[0] if version else "unknown",
                        "tables": [dict(t) for t in tables]
                    }
        except Exception as e:
            return {"backend": "PostgreSQL", "error": str(e)}


# ---------------------------------------------------------------------------
# Thread-safe global singleton
# ---------------------------------------------------------------------------
_nexus: Optional[PostgresNexus] = None
_nexus_lock = threading.Lock()


def get_postgres_nexus(
    connection_string: Optional[str] = None,
    min_connections: int = 1,
    max_connections: int = 10
) -> PostgresNexus:
    """
    Get the PostgreSQL Nexus singleton.
    
    Args:
        connection_string: PostgreSQL connection string
        min_connections: Minimum pool connections
        max_connections: Maximum pool connections
    
    Returns:
        PostgresNexus instance
    """
    global _nexus
    with _nexus_lock:
        if _nexus is None:
            _nexus = PostgresNexus(
                connection_string,
                min_connections,
                max_connections
            )
    return _nexus


def is_postgres_enabled() -> bool:
    """Check if PostgreSQL mode is enabled."""
    return os.environ.get("SME_USE_POSTGRES", "").lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Unified Nexus Factory
# ---------------------------------------------------------------------------
def get_nexus(use_postgres: Optional[bool] = None) -> Any:
    """
    Factory function to get the appropriate Nexus instance.
    
    Args:
        use_postgres: Override automatic detection
    
    Returns:
        ForensicNexus (SQLite) or PostgresNexus (PostgreSQL)
    """
    if use_postgres is None:
        use_postgres = is_postgres_enabled()
    
    if use_postgres:
        return get_postgres_nexus()
    
    # Fall back to SQLite
    from gateway.nexus_db import get_nexus as get_sqlite_nexus
    return get_sqlite_nexus()
