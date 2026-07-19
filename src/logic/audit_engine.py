"""
Audit Engine - Drift Analysis & Cryptographic Merkle Tree Audit Logging
=======================================================================
HDF5-based claim drift analysis combined with SHA-256 Merkle tree audit record
chaining for tamper-evident forensic audit trails.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import h5py

GENESIS_HASH = "0" * 64


@dataclass
class MerkleAuditRecord:
    """A cryptographic Merkle audit entry."""

    index: int
    event_type: str
    actor: str
    payload: dict[str, Any]
    timestamp: float
    prev_hash: str
    hash: str = field(init=False)

    def __post_init__(self):
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload_str = json.dumps(self.payload, sort_keys=True)
        raw = f"{self.index}|{self.timestamp}|{self.event_type}|{self.actor}|{payload_str}|{self.prev_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuditEngine:
    """
    Forensic Audit Engine for claim drift analysis and Merkle tree log verification.
    """

    def __init__(self, h5_path: str | None = None):
        if h5_path is None:
            self.h5_path = os.getenv("KNOWLEDGE_CORE_PATH", "data/knowledge_core.h5")
        else:
            self.h5_path = h5_path

        self.audit_records: list[MerkleAuditRecord] = []
        self._last_hash = GENESIS_HASH

    def analyze_drift(self, claims: list[dict]) -> dict:
        """
        Compares claims against the HDF5 core.
        Claim format: {"subject": "FastMCP", "predicate": "is", "object": "plumbing"}
        """
        results = {"drift_score": 0.0, "anomalies": [], "verified": []}

        try:
            with h5py.File(self.h5_path, "r") as f:
                if "relationships" in f:
                    rel_group = f["relationships"]

                    for claim in claims:
                        subj, obj = claim.get("subject"), claim.get("object")
                        if subj in rel_group and obj in rel_group[subj]:
                            results["verified"].append(claim)
                        else:
                            results["anomalies"].append(claim)
                else:
                    results["anomalies"] = claims
        except FileNotFoundError:
            results["anomalies"] = claims
        except Exception:
            results["anomalies"] = claims

        total = len(claims)
        if total > 0:
            results["drift_score"] = len(results["anomalies"]) / total

        return results

    def log_event(
        self, event_type: str, actor: str = "system", payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Log a forensic event into the Merkle audit chain.
        """
        payload_data = payload or {}
        timestamp = time.time()
        index = len(self.audit_records)

        record = MerkleAuditRecord(
            index=index,
            event_type=event_type,
            actor=actor,
            payload=payload_data,
            timestamp=timestamp,
            prev_hash=self._last_hash,
        )

        self.audit_records.append(record)
        self._last_hash = record.hash

        return {
            "index": record.index,
            "event_type": record.event_type,
            "actor": record.actor,
            "timestamp": record.timestamp,
            "hash": record.hash,
            "prev_hash": record.prev_hash,
        }

    def verify_integrity(self) -> dict[str, Any]:
        """
        Verify the full Merkle audit chain integrity to detect tampering.
        """
        if not self.audit_records:
            return {
                "valid": True,
                "total_events": 0,
                "merkle_root": GENESIS_HASH,
                "corrupted_index": None,
            }

        expected_prev = GENESIS_HASH

        for idx, record in enumerate(self.audit_records):
            if record.prev_hash != expected_prev:
                return {
                    "valid": False,
                    "reason": f"Broken chain link at index {idx}",
                    "corrupted_index": idx,
                    "merkle_root": self._last_hash,
                }

            recomputed_hash = record._compute_hash()
            if recomputed_hash != record.hash:
                return {
                    "valid": False,
                    "reason": f"Tampered record payload at index {idx}",
                    "corrupted_index": idx,
                    "merkle_root": self._last_hash,
                }

            expected_prev = record.hash

        return {
            "valid": True,
            "total_events": len(self.audit_records),
            "merkle_root": self._last_hash,
            "corrupted_index": None,
        }

    def compute_merkle_root(self) -> str:
        """
        Compute current Merkle tree root hash for distributed node consensus.
        """
        if not self.audit_records:
            return GENESIS_HASH
        return self._last_hash

    def verify_remote_merkle_root(self, remote_merkle_root: str) -> dict[str, Any]:
        """
        Verify consensus between local Merkle root and a remote node's Merkle root.
        """
        local_root = self.compute_merkle_root()
        consensus = local_root == remote_merkle_root

        return {
            "consensus": consensus,
            "local_merkle_root": local_root,
            "remote_merkle_root": remote_merkle_root,
            "total_events": len(self.audit_records),
        }

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Return the current audit trail as a list of dictionaries."""
        return [
            {
                "index": r.index,
                "event_type": r.event_type,
                "actor": r.actor,
                "payload": r.payload,
                "timestamp": r.timestamp,
                "hash": r.hash,
                "prev_hash": r.prev_hash,
            }
            for r in self.audit_records
        ]
