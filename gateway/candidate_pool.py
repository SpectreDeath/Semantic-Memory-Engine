"""
CandidatePoolStorage - Persistent Candidate Team Pools (F_ℓ) & Dynamic Routing
=============================================================================
Manages layerwise candidate pools of validated agent team blocks in laboratory.db
and implements DynamicRoutingSelect(F_ℓ, ℓ, I_ℓ, I) for Agentic Neural Networks (ANN).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger("lawnmower.candidate_pool")


class CandidatePoolStorage:
    """
    SQLite WAL-backed storage for ANN candidate pools (F_ℓ) and dynamic team selection.
    """

    def __init__(self, db_path: str = "data/laboratory.db") -> None:
        self.db_path = Path(db_path)
        self._mem_conn: sqlite3.Connection | None = None
        if str(self.db_path) == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candidate_pools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    layer_index INTEGER NOT NULL,
                    block_id TEXT UNIQUE NOT NULL,
                    block_json TEXT NOT NULL,
                    loss_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_layer_idx ON candidate_pools (layer_index);"
            )
            conn.commit()

    def save_block(self, layer_index: int, block: dict[str, Any]) -> bool:
        """
        Insert or replace a validated candidate team block (f'_ℓ) into pool F_ℓ.
        """
        block_id = block.get("block_id") or f"block_l{layer_index}_default"
        loss_score = block.get("loss_score", 0.0)
        block_json = json.dumps(block)

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO candidate_pools (layer_index, block_id, block_json, loss_score)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(block_id) DO UPDATE SET
                        block_json = excluded.block_json,
                        loss_score = excluded.loss_score;
                    """,
                    (layer_index, block_id, block_json, loss_score),
                )
                conn.commit()
            logger.info(
                f"CandidatePoolStorage: Saved block '{block_id}' to layer {layer_index} pool (loss: {loss_score})"
            )
            return True
        except Exception as e:
            logger.exception(f"CandidatePoolStorage failed to save block '{block_id}': {e}")
            return False

    def get_pool(self, layer_index: int) -> list[dict[str, Any]]:
        """
        Retrieve candidate pool F_ℓ for layer ℓ.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT block_json FROM candidate_pools WHERE layer_index = ? ORDER BY loss_score ASC;",
                    (layer_index,),
                )
                rows = cursor.fetchall()
                return [json.loads(row["block_json"]) for row in rows]
        except Exception as e:
            logger.exception(f"CandidatePoolStorage failed to get pool for layer {layer_index}: {e}")
            return []

    def select_optimal_team(
        self, layer_index: int, task_context: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Implements f_ℓ = DynamicRoutingSelect(F_ℓ, ℓ, I_ℓ, I).
        Selects candidate block with minimal loss score from pool F_ℓ.
        """
        pool = self.get_pool(layer_index)
        if not pool:
            return None

        # Select block with lowest loss_score
        optimal_block = pool[0]
        logger.info(
            f"DynamicRoutingSelect: Selected optimal block '{optimal_block.get('block_id')}' for layer {layer_index}"
        )
        return optimal_block
