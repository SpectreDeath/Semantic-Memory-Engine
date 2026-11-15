---
name: data-management
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Core
source_file: src/core/data_manager.py
source: Semantic Memory Engine (SME)
tags:
  - data-management
  - dataset-lifecycle
  - schema-migrations
  - table-cleanup
  - storage-quotas
inputs:
  action:
    type: string
    required: true
    description: Operation (`'cleanup'`, `'migrate'`, `'quota_check'`, `'export'`).
  target_table:
    type: string
    required: false
    description: Table name or dataset identifier to manage.
outputs:
  management_summary:
    type: object
    description: Summary of records affected, bytes reclaimed, and migration status.
  status:
    type: string
    description: Operation status string (`'ok'` or `'error'`).
---

# Data Management Engine

`data-management` orchestrates dataset lifecycle operations, table pruning, schema migrations, and storage quota enforcement in Python and SQLite:

$$\text{ReclaimDiskSpace} = \text{Execute}(\text{DELETE FROM } T \text{ WHERE age} > \tau) \to \text{VACUUM}$$

---

## The 5-Stage Data Management Progression

1. **Request Intake & Scope Audit**: Ingest action and target dataset name.
2. **Quota & TTL Policy Evaluation**: Identify expired temporary tables and stale cache entries.
3. **The Visual Brief**: Generate interactive HTML storage quota breakdown brief at `%TEMP%\data-mgmt-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert database backup snapshot exists before executing schema migrations or truncations.
5. **Operation Execution & Output Emission**: Execute cleanup/migration and emit summary receipt.

---

## Implementation Notes

```python
from typing import Dict, List, Any, Optional

def execute_data_management(
    action: str,
    target_table: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "management_summary": {
            "action": action,
            "table": target_table or "all",
            "records_pruned": 150,
            "bytes_reclaimed_mb": 12.4
        },
        "status": "ok"
    }
```

---

## Anti-Patterns & Guardrails

- **Unbacked Schema Alterations** — Mutating database schemas without creating automatic timestamped recovery backups.
- **Unbounded Vacuum Locking** — Running heavy full-database `VACUUM` commands during peak transactional load.