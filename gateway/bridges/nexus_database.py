"""
Nexus Database Bridge - Provenance Registration & HSM Access
==============================================================
Handles SQLite Nexus database queries, provenance registration, and HSM access.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("lawnmower.bridges.nexus_database")


class NexusDatabaseBridge:
    """Handles SQLite Nexus database queries, provenance registration, and HSM access."""

    def __init__(self) -> None:
        self._nexus = None

    def get_hsm(self):
        """Return the HardwareSecurity module for evidence signing (NexusAPI)."""
        from gateway.hardware_security import get_hsm as _get_hsm

        return _get_hsm()

    @property
    def nexus(self):
        if self._nexus is None:
            from gateway.nexus_db import get_nexus as _get_nexus

            self._nexus = _get_nexus()
        return self._nexus

    def get_source_reliability(self, source_id: str) -> dict[str, Any]:
        """Query the Nexus core for source provenance reliability."""
        try:
            sql = (
                "SELECT reliability_tier, integrity_hash, is_tamper_evident "
                "FROM prov.source_provenance WHERE source_id = ?"
            )
            res = self.nexus.query(sql, (source_id,))
            if res:
                row = res[0]
                return {
                    "tier": row["reliability_tier"],
                    "hash": row["integrity_hash"],
                    "tamper_evident": bool(row["is_tamper_evident"]),
                }
            return {"tier": 1, "hash": "Unknown", "tamper_evident": False}
        except Exception as e:
            logger.exception(f"Nexus visibility error: {e}")
            return {"tier": 0, "hash": "Error", "tamper_evident": False}

    def register_provenance(
        self, source_id: str, path: str, hash_val: str, tier: int, method: str
    ) -> bool:
        """Manually register a source via the Nexus."""
        try:
            sql = """
                INSERT OR REPLACE INTO prov.source_provenance
                    (source_id, origin_path, integrity_hash, reliability_tier, acquisition_method)
                VALUES (?, ?, ?, ?, ?)
            """
            self.nexus.execute(sql, (source_id, path, hash_val, tier, method))
            return True
        except Exception as e:
            logger.exception(f"Nexus registration error: {e}")
            return False
