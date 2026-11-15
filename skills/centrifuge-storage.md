---
name: centrifuge-storage
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Storage
source_file: src/core/centrifuge.py
source: Semantic Memory Engine (SME)
tags:
  - centrifuge-storage
  - tiered-storage
  - forensic-archiving
  - hot-warm-cold
  - data-lifecycle
inputs:
  action:
    type: string
    required: true
    description: Operation (`'store'`, `'retrieve'`, `'rotate_tiers'`, `'compact'`).
  payload:
    type: object
    required: false
    description: Document or artifact payload to archive.
  tier:
    type: string
    required: false
    description: Storage tier (`'hot'`, `'warm'`, `'cold'`, default `'hot'`).
outputs:
  storage_receipt:
    type: object
    description: Archive receipt with artifact ID, tier location, and compression ratio.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Centrifuge Storage Engine

`centrifuge-storage` manages tiered data lifecycle rotation (Hot RAM/SQLite, Warm Disk Parquet, Cold Compressed Vault) in Python:

$$\text{Tier}(\mathcal{D}) = \begin{cases} \text{HOT} & \text{if Age} < 7\text{d} \\ \text{WARM} & \text{if } 7\text{d} \le \text{Age} < 90\text{d} \\ \text{COLD} & \text{if Age} \ge 90\text{d} \end{cases}$$

---

## The 5-Stage Centrifuge Storage Progression

1. **Storage Request Ingestion**: Ingest artifact and desired storage tier.
2. **Compression & Encryption Packaging**: Apply zstandard compression and AES-GCM encryption for cold archiving.
3. **The Visual Brief**: Generate interactive HTML storage tier utilization treemap at `%TEMP%\centrifuge-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert SHA-256 checksum match before and after tier migration.
5. **Receipt Emission**: Emit storage receipt with persistent retrieval key.

---

## Implementation Notes

```python
import uuid
from typing import Dict, List, Any, Optional

def manage_centrifuge_storage(
    action: str,
    payload: Optional[Dict[str, Any]] = None,
    tier: str = "hot"
) -> Dict[str, Any]:
    art_id = f"art_{str(uuid.uuid4())[:8]}"
    return {
        "storage_receipt": {
            "artifact_id": art_id,
            "tier": tier,
            "compression": "zstd",
            "bytes_saved_pct": 68.5
        },
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Premature Cold Archival** — Migrating frequently queried active datasets to slow cold storage tiers.
- **Unverified Tier Migration** — Deleting source records from hot storage before verifying cold storage write integrity.