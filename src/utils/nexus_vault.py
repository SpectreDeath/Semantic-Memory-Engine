"""Nexus Vault Bridge — ingest validated SKILL.md metadata into PostgreSQL.

Scans ``.kilo/vault/`` for ``*.metadata.json`` files, extracts normalized
semantic fields (triggers, constraints, workflow, version), and inserts
them as unified nodes into the existing Nexus schema with an automatically
calculated initial Epistemic Trust Score.

Usage:
    from src.utils.nexus_vault import ingest_vault_to_nexus

    result = ingest_vault_to_nexus()
    print(result)

Design goals:
    - Lightweight: reads only ``.metadata.json`` sidecar files, never full
      SKILL.md body, never clones repos.
    - Streaming: uses DB connection-pool only for the duration of a single
      transaction; no persistent background threads.
    - Dual-backend: targets PostgreSQL when ``SME_USE_POSTGRES`` is set,
      falls back to the SQLite ``gateway.nexus_db`` otherwise.
    - Idempotent: uses ``UNIQUE(skill_name, version)`` so re-runs are safe.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("nexus_vault")

# ---------------------------------------------------------------------------
# Constants / patterns
# ---------------------------------------------------------------------------
PLACEHOLDERS = {"n/a", "todo", "placeholder", "none", "xyz", ""}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_VAULT_DIR = "skills/gold_standard"  # Will be resolved to .kilo/vault

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in PLACEHOLDERS


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_skill_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract normalized semantic fields from a single metadata JSON payload.

    Mapping
    -------
    triggers   → ``tags`` list (placeholder-free, stripped)
    constraints → derived from ``category``, ``type``, ``inputs``, ``outputs``
    workflow   → ``workflow`` list (placeholder-free, kept as-is)
    version    → ``version`` string, defaulting to ``"0.0.0"``
    """
    # --- triggers ---
    raw_tags = metadata.get("tags", [])
    if isinstance(raw_tags, list):
        triggers = [
            _safe_str(t) for t in raw_tags if _safe_str(t) and not _is_placeholder(_safe_str(t))
        ]
    else:
        triggers = [_safe_str(raw_tags)] if not _is_placeholder(raw_tags) else []

    # --- constraints ---
    constraints: list[str] = []
    category = _safe_str(metadata.get("category", ""))
    skill_type = _safe_str(metadata.get("type", ""))

    if category and not _is_placeholder(category):
        constraints.append(f"category:{category}")
    if skill_type and not _is_placeholder(skill_type):
        constraints.append(f"type:{skill_type}")

    for field_name in ("inputs", "outputs"):
        raw_list = metadata.get(field_name, [])
        if isinstance(raw_list, list):
            for item in raw_list:
                sanitized = _safe_str(item)
                if sanitized and not _is_placeholder(sanitized):
                    constraints.append(f"{field_name}:{sanitized}")

    # --- workflow ---
    raw_workflow = metadata.get("workflow", [])
    if isinstance(raw_workflow, list):
        workflow = [
            _safe_str(s) for s in raw_workflow if _safe_str(s) and not _is_placeholder(_safe_str(s))
        ]
    else:
        workflow = (
            [_safe_str(raw_workflow)]
            if _safe_str(raw_workflow) and not _is_placeholder(_safe_str(raw_workflow))
            else []
        )

    # --- version ---
    version = _safe_str(metadata.get("version", "0.0.0"))
    if not version or not SEMVER_RE.match(version):
        version = "0.0.0"

    return {
        "triggers": triggers,
        "constraints": constraints,
        "workflow": workflow,
        "version": version,
    }


def _calculate_trust_score(
    metadata: dict[str, Any],
    extracted: dict[str, Any],
) -> float:
    """Calculate a lightweight initial Epistemic Trust Score for a skill pattern.

    Heuristic weights (mirrors ``gateway.epistemic_trust.TrustScore`` logic)
    are applied to auto-extracted provenance signals:

    - Base (unattributed): 0.5
    - +0.1: source attribution present (``source_file`` or ``source``)
    - +0.1: workflow completeness (≥3 steps)
    - +0.1: strict SemVer version string
    - +0.1: triggers (tags) non-empty
    - +0.1: constraints non-empty

    Result is clamped to ``[0.0, 1.0]``.
    """
    score = 0.5

    if not _is_placeholder(metadata.get("source_file")) or not _is_placeholder(
        metadata.get("source")
    ):
        score += 0.1

    if len(extracted.get("workflow", [])) >= 3:
        score += 0.1

    if SEMVER_RE.match(extracted.get("version", "")):
        score += 0.1

    if extracted.get("triggers"):
        score += 0.1

    if extracted.get("constraints"):
        score += 0.1

    return round(min(score, 1.0), 4)


# ---------------------------------------------------------------------------
# Backend detection / SQL generation
# ---------------------------------------------------------------------------


def _get_nexus() -> Any:
    """Resolve the active Nexus backend."""
    try:
        from src.database.postgres_nexus import get_nexus  # type: ignore

        return get_nexus()
    except Exception:
        pass

    try:
        from gateway.nexus_db import get_nexus  # type: ignore

        return get_nexus()
    except Exception:
        pass

    raise ImportError(
        "No Nexus backend available. "
        "Set SME_USE_POSTGRES=true with POSTGRES_CONNECTION_STRING, "
        "or ensure gateway/nexus_db is accessible."
    )


def _is_postgres(nexus: Any) -> bool:
    return nexus.__class__.__name__ == "PostgresNexus"


def _schema_init_sql(is_postgres: bool) -> str:
    """Return schema + table creation SQL for the detected backend."""
    if is_postgres:
        return """
            CREATE SCHEMA IF NOT EXISTS semantic;
            CREATE TABLE IF NOT EXISTS semantic.skill_patterns (
                id SERIAL PRIMARY KEY,
                skill_name VARCHAR(255) NOT NULL,
                version VARCHAR(50),
                triggers JSONB,
                constraints JSONB,
                workflow JSONB,
                trust_score DOUBLE PRECISION DEFAULT 0.0,
                source_attribution TEXT,
                vault_path TEXT,
                metadata JSONB,
                ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(skill_name, version)
            );
            CREATE INDEX IF NOT EXISTS idx_skill_patterns_name
                ON semantic.skill_patterns(skill_name);
            CREATE INDEX IF NOT EXISTS idx_skill_patterns_trust
                ON semantic.skill_patterns(trust_score DESC);
            CREATE INDEX IF NOT EXISTS idx_skill_patterns_ingested
                ON semantic.skill_patterns(ingested_at DESC);
        """
    # SQLite fallback
    return """
        CREATE TABLE IF NOT EXISTS skill_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            version TEXT,
            triggers TEXT,
            constraints TEXT,
            workflow TEXT,
            trust_score REAL DEFAULT 0.0,
            source_attribution TEXT,
            vault_path TEXT,
            metadata TEXT,
            ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(skill_name, version)
        );
        CREATE INDEX IF NOT EXISTS idx_skill_patterns_name
            ON skill_patterns(skill_name);
        CREATE INDEX IF NOT EXISTS idx_skill_patterns_trust
            ON skill_patterns(trust_score DESC);
    """


def _insert_sql(is_postgres: bool) -> str:
    """Return parameterized INSERT statement."""
    if is_postgres:
        return """
            INSERT INTO semantic.skill_patterns
                (skill_name, version, triggers, constraints, workflow,
                 trust_score, source_attribution, vault_path, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (skill_name, version) DO UPDATE SET
                triggers = excluded.triggers,
                constraints = excluded.constraints,
                workflow = excluded.workflow,
                trust_score = excluded.trust_score,
                source_attribution = excluded.source_attribution,
                vault_path = excluded.vault_path,
                metadata = excluded.metadata,
                ingested_at = NOW()
        """
    # SQLite (UPSERT)
    return """
        INSERT INTO skill_patterns
            (skill_name, version, triggers, constraints, workflow,
             trust_score, source_attribution, vault_path, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(skill_name, version) DO UPDATE SET
            triggers = excluded.triggers,
            constraints = excluded.constraints,
            workflow = excluded.workflow,
            trust_score = excluded.trust_score,
            source_attribution = excluded.source_attribution,
            vault_path = excluded.vault_path,
            metadata = excluded.metadata,
            ingested_at = CURRENT_TIMESTAMP
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ingest_vault_to_nexus(
    vault_dir: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Scan `.kilo/vault/` metadata files and ingest them into the Nexus.

    Parameters
    ----------
    vault_dir:
        Directory containing ``*.metadata.json`` files.
        Defaults to ``.kilo/vault`` relative to the repo root.
    limit:
        Optional cap on the number of files to process. Useful for
        smoke-testing without committing the full catalog.

    Returns
    -------
    dict[str, Any]
        Summary with ``processed``, ``inserted``, ``skipped``, and
        ``errors`` counts.
    """
    repo_root = Path(__file__).resolve().parents[2]
    effective_vault = Path(vault_dir) if vault_dir else repo_root / ".kilo" / "vault"

    if not effective_vault.exists():
        logger.warning("Vault directory not found: %s", effective_vault)
        return {
            "processed": 0,
            "inserted": 0,
            "skipped": 0,
            "errors": 0,
            "vault_dir": str(effective_vault),
            "error": "Vault directory not found",
        }

    meta_files = sorted(effective_vault.glob("*.metadata.json"))
    if limit is not None:
        meta_files = meta_files[:limit]

    logger.info("Found %d metadata files in %s", len(meta_files), effective_vault)

    nexus = _get_nexus()
    is_pg = _is_postgres(nexus)

    # Ensure schema/table exist
    nexus.execute(_schema_init_sql(is_pg))

    # Batched execution
    processed = 0
    inserted = 0
    skipped = 0
    errors = 0

    sql = _insert_sql(is_pg)

    for meta_path in meta_files:
        processed += 1
        try:
            raw = meta_path.read_text(encoding="utf-8")
            metadata = json.loads(raw)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping %s: parse error (%s)", meta_path.name, exc)
            skipped += 1
            continue

        skill_name = _safe_str(metadata.get("skill_name", meta_path.stem))
        if not skill_name or _is_placeholder(skill_name):
            logger.warning("Skipping %s: missing skill_name", meta_path.name)
            skipped += 1
            continue

        extracted = _extract_skill_fields(metadata)
        trust_score = _calculate_trust_score(metadata, extracted)

        source_attribution = _safe_str(metadata.get("source_file") or metadata.get("source"))
        if not source_attribution:
            source_attribution = None

        payload = {
            "skill_name": skill_name,
            "version": extracted["version"],
            "triggers": json.dumps(extracted["triggers"], ensure_ascii=False)
            if is_pg
            else json.dumps(extracted["triggers"]),
            "constraints": json.dumps(extracted["constraints"], ensure_ascii=False)
            if is_pg
            else json.dumps(extracted["constraints"]),
            "workflow": json.dumps(extracted["workflow"], ensure_ascii=False)
            if is_pg
            else json.dumps(extracted["workflow"]),
            "trust_score": trust_score,
            "source_attribution": source_attribution,
            "vault_path": str(meta_path),
            "metadata": json.dumps(metadata, ensure_ascii=False) if is_pg else json.dumps(metadata),
        }

        try:
            nexus.execute(sql, _params_for_backend(payload, is_pg))
            inserted += 1
            logger.debug(
                "Inserted %s v%s (trust=%.2f)", skill_name, extracted["version"], trust_score
            )
        except Exception:
            logger.exception("Insert failed for %s", meta_path.name)
            errors += 1

    summary = {
        "processed": processed,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "vault_dir": str(effective_vault),
        "backend": "postgresql" if is_pg else "sqlite",
    }

    logger.info(
        "Nexus vault ingest complete: %d processed, %d inserted, %d skipped, %d errors",
        processed,
        inserted,
        skipped,
        errors,
    )

    return summary


def _params_for_backend(payload: dict[str, Any], is_postgres: bool) -> tuple[Any, ...]:
    """Build ordered parameter tuple matching the backend's placeholder style."""
    # Common ordering aligned with _insert_sql()
    return (
        payload["skill_name"],
        payload["version"],
        payload["triggers"],
        payload["constraints"],
        payload["workflow"],
        payload["trust_score"],
        payload["source_attribution"],
        payload["vault_path"],
        payload["metadata"],
    )
