"""
📊 Signature Comparisons v2.1.0 — Polars + Manhattan Distance

Purpose:
    High-performance signature comparison engine using Polars lazy evaluation.
    Loads reference corpus from laboratory.db and computes Manhattan Distance
    between a live signature and all stored references.

    Manhattan Distance is chosen over cosine similarity because:
        • It's computationally lighter (no square roots, no normalization)
        • Better suited for low-dimensional vectors (3 features)
        • Keeps math tractable on the GTX 1660 Ti / 6GB VRAM

Usage:
    from src.analysis.comparisons import SignatureCompare

    engine = SignatureCompare(db_path="data/storage/laboratory.db")

    live = {"alliteration_index": 0.42, "parallelism_score": 7, "superlative_count": 3}
    results = engine.compare_live_vs_corpus(live, source_filter="speech")
"""

from __future__ import annotations


import logging
import os
import sqlite3
from typing import Any

import polars as pl

# Configure logging
logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = os.getenv("SME_DB_PATH", "data/storage/laboratory.db")

# Signature feature columns used for distance computation
_FEATURE_COLS = ["alliteration_index", "parallelism_score", "superlative_count"]


class SignatureCompare:
    """
    Polars-backed signature comparison engine.

    Loads the reference corpus from laboratory.db lazily, applies predicate
    pushdown for source/date filtering, then computes Manhattan Distance
    between a "Live Signature" and every reference row.

    Design:
        read_database() → LazyFrame → filter → collect → distance calc
        All filtering happens before .collect() to minimize RAM usage.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """
        Initialize the comparison engine.

        Args:
            db_path: Path to the SQLite database.
                     Defaults to SME_DB_PATH env var or data/storage/laboratory.db.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_table()
        logger.info(f"SignatureCompare initialized — db={self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Return a new sqlite3 connection."""
        return sqlite3.connect(self.db_path)

    def _ensure_table(self) -> None:
        """Ensure the rhetorical_signatures table exists."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rhetorical_signatures (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    source      TEXT    NOT NULL,
                    alliteration_index  REAL NOT NULL,
                    parallelism_score   INTEGER NOT NULL,
                    superlative_count   INTEGER NOT NULL,
                    metadata    TEXT,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Corpus Loading (Polars Lazy)
    # ------------------------------------------------------------------

    def load_reference_corpus(
        self,
        source_filter: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pl.LazyFrame:
        """
        Load the reference corpus as a Polars LazyFrame with optional filters.

        Predicate pushdown: filters are applied BEFORE .collect() to
        keep memory usage minimal on constrained hardware.

        Args:
            source_filter: Substring match on the source column.
            start_date: ISO date string (inclusive lower bound).
            end_date: ISO date string (inclusive upper bound).

        Returns:
            pl.LazyFrame with filtered reference signatures.
        """
        conn = self._get_connection()
        try:
            df = pl.read_database(
                "SELECT * FROM rhetorical_signatures",
                connection=conn,
            )
        finally:
            conn.close()

        lf = df.lazy()

        # --- Predicate Pushdown ---
        if source_filter:
            lf = lf.filter(pl.col("source").str.contains(source_filter))
            logger.debug(f"Predicate pushdown: source contains '{source_filter}'")

        if start_date:
            lf = lf.filter(pl.col("created_at") >= start_date)
            logger.debug(f"Predicate pushdown: created_at >= {start_date}")

        if end_date:
            lf = lf.filter(pl.col("created_at") <= end_date)
            logger.debug(f"Predicate pushdown: created_at <= {end_date}")

        return lf

    # ------------------------------------------------------------------
    # Distance Computation
    # ------------------------------------------------------------------

    @staticmethod
    def manhattan_distance(
        live: dict[str, Any], reference: dict[str, Any]
    ) -> float:
        """
        Compute Manhattan Distance between two rhetorical signatures.

        Formula: |Δ_alliteration| + |Δ_parallelism| + |Δ_superlative|

        Lighter than Euclidean (no sqrt) or cosine similarity (no
        normalization) — suitable for a 3-feature vector on constrained
        hardware.

        Args:
            live: Live signature dict with feature columns.
            reference: Reference signature dict with feature columns.

        Returns:
            Manhattan distance (float). Lower = more similar.
        """
        distance = 0.0
        for col in _FEATURE_COLS:
            distance += abs(float(live[col]) - float(reference[col]))
        return distance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare_live_vs_corpus(
        self,
        live_signature: dict[str, Any],
        source_filter: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        top_n: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Compare a live signature against the reference corpus.

        Loads the corpus lazily, applies filters, collects, computes
        Manhattan Distance per row, and returns ranked results.

        Args:
            live_signature: Dict with alliteration_index, parallelism_score,
                            superlative_count.
            source_filter: Optional substring filter on source column.
            start_date: Optional ISO date lower bound.
            end_date: Optional ISO date upper bound.
            top_n: Maximum number of closest matches to return.

        Returns:
            List of dicts sorted by distance (ascending), each containing:
                - source, alliteration_index, parallelism_score,
                  superlative_count, created_at, manhattan_distance
        """
        lf = self.load_reference_corpus(
            source_filter=source_filter,
            start_date=start_date,
            end_date=end_date,
        )
        corpus_df = lf.collect()

        if len(corpus_df) == 0:
            logger.warning("Reference corpus is empty after filtering")
            return []

        logger.info(
            f"Comparing live signature against {len(corpus_df)} reference(s)"
        )

        # Compute Manhattan Distance for each row
        results = []
        for row in corpus_df.iter_rows(named=True):
            dist = self.manhattan_distance(live_signature, row)
            results.append({
                "source": row["source"],
                "alliteration_index": row["alliteration_index"],
                "parallelism_score": row["parallelism_score"],
                "superlative_count": row["superlative_count"],
                "created_at": row.get("created_at", ""),
                "manhattan_distance": round(dist, 6),
            })

        # Sort by distance ascending (closest first)
        results.sort(key=lambda r: r["manhattan_distance"])

        logger.info(
            f"Top match: source='{results[0]['source']}', "
            f"distance={results[0]['manhattan_distance']:.4f}"
        )

        return results[:top_n]
