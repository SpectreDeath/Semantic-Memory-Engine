import psycopg2
from psycopg2 import pool
import logging
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Any
from prometheus_client import Gauge, Counter

logger = logging.getLogger("LawnmowerMan.ArchivalDiff.Exporter")

# Phase 4: Prometheus Metrics
SME_ARCHIVAL_CHANGE_DETECTED = Gauge(
    "sme_archival_change_detected",
    "Indicates if data scrubbing was detected (1) or not (0)",
    ["url"]
)

SME_ARCHIVAL_SCRUB_EVENTS_TOTAL = Counter(
    "sme_archival_scrub_events_total",
    "Total number of detected archival scrubbing events",
    ["url"]
)

SME_ARCHIVAL_DELETED_PARAGRAPHS_TOTAL = Counter(
    "sme_archival_deleted_paragraphs_total",
    "Total number of paragraphs detected as scrubbed",
    ["url"]
)

class SmeExporter:
    """
    Transforms deleted content into SME bipartite nodes and commits to PostgreSQL.
    Also handles Prometheus metric updates.
    """
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.environ.get("DATABASE_URL", "postgresql://sme_user:sme_password@localhost:5432/sme_nexus")
        self.pool = None
        self._initialize_pool()
        self._initialize_schema()

    def _initialize_pool(self):
        try:
            self.pool = pool.SimpleConnectionPool(1, 10, dsn=self.db_url)
            logger.info("PostgreSQL connection pool initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")

    def _initialize_schema(self):
        """
        Creates the bipartite graph schema in Postgres.
        """
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                # SourceURLNode table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sme_source_url_nodes (
                        id SERIAL PRIMARY KEY,
                        url TEXT UNIQUE NOT NULL,
                        first_seen TIMESTAMPTZ DEFAULT NOW(),
                        last_checked TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                
                # ContentNode table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sme_content_nodes (
                        id SERIAL PRIMARY KEY,
                        content_hash TEXT UNIQUE NOT NULL,
                        content_text TEXT NOT NULL,
                        snapshot_timestamp TEXT NOT NULL,
                        snapshot_url TEXT NOT NULL,
                        detected_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                
                # Relationship table (SCRUBBED_FROM)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sme_relationships (
                        id SERIAL PRIMARY KEY,
                        content_node_id INT REFERENCES sme_content_nodes(id),
                        source_url_node_id INT REFERENCES sme_source_url_nodes(id),
                        relationship_type TEXT NOT NULL DEFAULT 'SCRUBBED_FROM',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                conn.commit()
                logger.info("SME Archival Schema initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            conn.rollback()
        finally:
            self._put_connection(conn)

    def _get_connection(self):
        if not self.pool:
            self._initialize_pool()
        try:
            return self.pool.getconn()
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            return None

    def _put_connection(self, conn):
        if self.pool and conn:
            self.pool.putconn(conn)

    def export_diff(self, diff_result: Dict[str, Any], metadata: Dict[str, Any]):
        """
        Processes diff result and commits to PostgreSQL.
        Updates Prometheus metrics.
        """
        target_url = metadata.get('url')
        deleted_content = diff_result.get('deleted_content', [])
        
        # Update metrics
        if deleted_content:
            SME_ARCHIVAL_CHANGE_DETECTED.labels(url=target_url).set(1)
            SME_ARCHIVAL_SCRUB_EVENTS_TOTAL.labels(url=target_url).inc()
            SME_ARCHIVAL_DELETED_PARAGRAPHS_TOTAL.labels(url=target_url).inc(len(deleted_content))
        else:
            SME_ARCHIVAL_CHANGE_DETECTED.labels(url=target_url).set(0)

        if not deleted_content:
            return
            
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                # 1. Ensure SourceURLNode exists
                cur.execute("""
                    INSERT INTO sme_source_url_nodes (url)
                    VALUES (%s)
                    ON CONFLICT (url) DO UPDATE SET last_checked = NOW()
                    RETURNING id;
                """, (target_url,))
                source_id = cur.fetchone()[0]
                
                # 2. Add ContentNodes and Relationships for each deleted paragraph
                for paragraph in deleted_content:
                    content_hash = hashlib.sha1(paragraph.encode()).hexdigest()
                    
                    # Insert ContentNode
                    cur.execute("""
                        INSERT INTO sme_content_nodes (content_hash, content_text, snapshot_timestamp, snapshot_url)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (content_hash) DO NOTHING
                        RETURNING id;
                    """, (
                        content_hash, 
                        paragraph, 
                        metadata['snapshot_old']['timestamp'], 
                        metadata['snapshot_old']['url']
                    ))
                    
                    result = cur.fetchone()
                    if result:
                        content_id = result[0]
                        
                        # Create SCRUBBED_FROM relationship
                        cur.execute("""
                            INSERT INTO sme_relationships (content_node_id, source_url_node_id, relationship_type)
                            VALUES (%s, %s, 'SCRUBBED_FROM');
                        """, (content_id, source_id))
                
                conn.commit()
                logger.info(f"Committed {len(deleted_content)} scrubbed nodes for {target_url}")
                
        except Exception as e:
            logger.error(f"Error exporting scrubbing data: {e}")
            conn.rollback()
        finally:
            self._put_connection(conn)
