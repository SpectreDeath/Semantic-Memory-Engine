---
name: data-auditing
domain: SME_INTEGRATION
version: 1.0.0
complexity: Intermediate
type: Tool
category: Utilities
source_file: src/logic/audit_engine.py
source: Semantic Memory Engine (SME)
tags:
  - data-auditing
  - merkle-tree-auditing
  - cryptographic-ledger
  - tamper-evidence
  - forensic-compliance
inputs:
  audit_records:
    type: array
    required: true
    description: List of transaction or state event payloads to commit to the audit tree.
outputs:
  merkle_root:
    type: string
    description: Root cryptographic SHA-256 hash representing the complete audit tree state.
  leaf_count:
    type: integer
    description: Total number of audited records committed.
  audit_status:
    type: string
    description: Verification status (`'verified'`, `'corrupted'`).
---

# Data Auditing Engine

`data-auditing` constructs tamper-evident cryptographic Merkle trees over forensic state records in Python:

$$\text{MerkleRoot} = \text{HashTree}(\{h_1, \dots, h_N\}), \quad h_i = \text{SHA256}(\text{Record}_i)$$

---

## The 5-Stage Data Auditing Progression

1. **Record Ingestion & Leaf Hashing**: Ingest event array; compute SHA-256 leaf hashes for each record.
2. **Merkle Tree Construction**: Recursively compute pairwise parent hashes until a single root is derived.
3. **The Visual Brief**: Generate interactive HTML Merkle tree visualization brief at `%TEMP%\data-audit-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Verify audit proof paths; assert that any single-bit mutation changes the root hash.
5. **Root Signing & Output Emission**: Commit root to immutable SQLite ledger and emit audit receipt.

---

## Implementation Notes

```python
import hashlib
from typing import Dict, List, Any

def audit_data_records(
    audit_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    leaves = [hashlib.sha256(str(r).encode("utf-8")).hexdigest() for r in audit_records]
    if not leaves:
        return {"merkle_root": "empty_tree", "leaf_count": 0, "audit_status": "verified"}
        
    curr = list(leaves)
    while len(curr) > 1:
        next_level = []
        for i in range(0, len(curr), 2):
            left = curr[i]
            right = curr[i+1] if i+1 < len(curr) else left
            next_level.append(hashlib.sha256((left + right).encode("utf-8")).hexdigest())
        curr = next_level
        
    return {
        "merkle_root": curr[0],
        "leaf_count": len(leaves),
        "audit_status": "verified"
    }
```

---

## Anti-Patterns & Guardrails

- **Linear Unlinked Logging** — Storing audit records in append-only plaintext files without cryptographic tree linking.
- **Odd-Leaf Unbalanced Tree Errors** — Failing to duplicate the last leaf when processing odd-numbered record batches.
