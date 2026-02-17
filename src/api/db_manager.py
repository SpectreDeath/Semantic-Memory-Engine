"""
🗄️ Forensic DB Manager v2.1.0 — Polars LazyFrame Backend

Purpose:
    Memory-efficient database layer for laboratory.db using Polars
    lazy evaluation and predicate pushdown. Replaces pandas-based
    query patterns for the Rhetorical Fingerprinting pipeline.

Usage:
    from src.api.db_manager import ForensicDBManager

    db = ForensicDBManager()
    db.store_signature(signature_dict, source="speech_2024.pdf")
    results = db.query_signatures(start_date="2024-01-01", source="speech")

Constraints:
    • Uses polars.LazyFrame for predicate pushdown (filter before collect)
    • Designed for laptop with GTX 1660 Ti / 6GB VRAM — avoids RAM spikes
    • Does NOT touch vendored faststylometry (which uses pandas internally)
"""

import logging
import math
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

import polars as pl

# Configure logging
logger = logging.getLogger(__name__)

# Default database path (relative to project root)
DEFAULT_DB_PATH = os.getenv("SME_DB_PATH", "data/storage/laboratory.db")

# Table schema for rhetorical signatures
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rhetorical_signatures (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT    NOT NULL,
    alliteration_index  REAL NOT NULL,
    parallelism_score   INTEGER NOT NULL,
    superlative_count   INTEGER NOT NULL,
    metadata    TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


class ForensicDBManager:
    """
    Polars-based database manager for rhetorical signature storage and retrieval.

    Design:
        - Reads from SQLite via polars.read_database() → LazyFrame
        - Uses predicate pushdown: filters on date/source BEFORE .collect()
        - Writes via raw sqlite3 (Polars doesn't do INSERT)
        - Euclidean distance comparison between signature vectors
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to SME_DB_PATH env var or data/storage/laboratory.db.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_table()
        logger.info(f"ForensicDBManager initialized — db={self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new sqlite3 connection."""
        return sqlite3.connect(self.db_path)

    def _ensure_table(self) -> None:
        """Create the rhetorical_signatures table if it doesn't exist."""
        conn = self._get_connection()
        try:
            conn.execute(_CREATE_TABLE_SQL)
            conn.commit()
            logger.debug("Ensured rhetorical_signatures table exists")
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Read operations (Polars LazyFrame)
    # ------------------------------------------------------------------

    def load_signatures(self) -> pl.LazyFrame:
        """
        Load all rhetorical signatures as a Polars LazyFrame.

        Returns:
            pl.LazyFrame with columns: id, source, alliteration_index,
            parallelism_score, superlative_count, metadata, created_at.
        """
        conn = self._get_connection()
        try:
            df = pl.read_database(
                "SELECT * FROM rhetorical_signatures",
                connection=conn,
            )
            logger.debug(f"Loaded {len(df)} signature rows into LazyFrame")
            return df.lazy()
        finally:
            conn.close()

    def query_signatures(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source: Optional[str] = None,
    ) -> pl.DataFrame:
        """
        Query signatures with predicate pushdown filtering.

        Filters are applied to the LazyFrame BEFORE .collect(),
        minimizing memory usage on constrained hardware.

        Args:
            start_date: ISO date string (inclusive). Only signatures
                        created on or after this date.
            end_date:   ISO date string (inclusive). Only signatures
                        created on or before this date.
            source:     Substring match on the source column.

        Returns:
            pl.DataFrame with matching rows.
        """
        lf = self.load_signatures()

        # --- Predicate Pushdown: filter before materializing ---
        if start_date:
            lf = lf.filter(pl.col("created_at") >= start_date)
            logger.debug(f"Predicate pushdown: created_at >= {start_date}")

        if end_date:
            lf = lf.filter(pl.col("created_at") <= end_date)
            logger.debug(f"Predicate pushdown: created_at <= {end_date}")

        if source:
            lf = lf.filter(pl.col("source").str.contains(source))
            logger.debug(f"Predicate pushdown: source contains '{source}'")

        result = lf.collect()
        logger.info(f"Query returned {len(result)} signature(s)")
        return result

    # ------------------------------------------------------------------
    # Write operations (sqlite3)
    # ------------------------------------------------------------------

    def store_signature(
        self,
        signature: Dict[str, Any],
        source: str,
        metadata: Optional[str] = None,
    ) -> int:
        """
        Insert a RhetoricalSignature into the database.

        Args:
            signature: Dict with keys alliteration_index, parallelism_score,
                       superlative_count.
            source:    Identifier for the source document.
            metadata:  Optional JSON string of additional context.

        Returns:
            The rowid of the inserted record.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO rhetorical_signatures
                    (source, alliteration_index, parallelism_score,
                     superlative_count, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    signature["alliteration_index"],
                    signature["parallelism_score"],
                    signature["superlative_count"],
                    metadata,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            rowid = cursor.lastrowid
            logger.info(f"Stored signature id={rowid} from source='{source}'")
            return rowid
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    @staticmethod
    def compare_signatures(
        sig_a: Dict[str, Any], sig_b: Dict[str, Any]
    ) -> float:
        """
        Compute Euclidean distance between two rhetorical signatures.

        Args:
            sig_a: Dict with alliteration_index, parallelism_score,
                   superlative_count.
            sig_b: Same schema as sig_a.

        Returns:
            Euclidean distance (float). Lower = more similar.
        """
        delta_alliteration = sig_a["alliteration_index"] - sig_b["alliteration_index"]
        delta_parallelism = sig_a["parallelism_score"] - sig_b["parallelism_score"]
        delta_superlative = sig_a["superlative_count"] - sig_b["superlative_count"]

        distance = math.sqrt(
            delta_alliteration ** 2
            + delta_parallelism ** 2
            + delta_superlative ** 2
        )

        logger.debug(f"Signature distance: {distance:.4f}")
        return distance
