---
name: dark-data-discovery
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Knowledge Management
source_file: extensions/ext_nur/
source: Semantic Memory Engine (SME)
tags:
  - dark-data-discovery
  - unindexed-assets
  - orphan-records
  - forensic-scanning
  - shadow-data
inputs:
  scan_roots:
    type: array
    required: true
    description: List of storage directories, table names, or volume endpoints to scan.
  file_patterns:
    type: array
    required: false
    description: Glob patterns or file extension filters `['*.log', '*.sqlite', '*.wal']`.
outputs:
  unindexed_assets:
    type: array
    description: List of discovered unindexed files, orphaned tables, and hidden artifacts.
  total_volume_bytes:
    type: integer
    description: Total byte size of unindexed dark data detected.
  classification_breakdown:
    type: object
    description: File type and MIME category distribution of discovered dark assets.
---

# Dark Data Discovery Engine

`dark-data-discovery` scans disconnected storage volumes, database caches, and unindexed archives to uncover orphaned or obscured data assets in Python and SQLite:

$$\mathcal{D}_{\text{dark}} = \{f \in \text{StorageRoot} : f \notin \text{CatalogIndex} \land \text{Size}(f) > 0\}$$

---

## The 5-Stage Dark Data Discovery Progression

1. **Storage Endpoint Ingest & Scope Definition**: Ingest scan directory roots and file extension filters; verify filesystem read permissions.
2. **Recursive Traversal & Catalog Cross-Referencing**: Walk directory trees; cross-reference discovered files against the central metadata registry.
3. **The Visual Brief**: Generate interactive HTML disk allocation treemap brief at `%TEMP%\dark-data-brief-<timestamp>.html` highlighting unindexed assets.
4. **Mandatory Checkpoint**: Assert safety filters; exclude active lockfiles (`*.lock`, `*.wal`) to prevent race conditions.
5. **Asset Classification & Output Emission**: Classify discovered artifacts by MIME type and emit complete `DarkDataInventory`.

---

## Implementation Notes

```python
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

def discover_dark_data(
    scan_roots: List[str],
    file_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    unindexed = []
    total_bytes = 0
    categories = {}
    
    for root_str in scan_roots:
        root = Path(root_str)
        if not root.exists():
            continue
            
        for path in root.rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                size = path.stat().st_size
                ext = path.suffix or "unknown"
                unindexed.append({"path": str(path), "size_bytes": size, "extension": ext})
                total_bytes += size
                categories[ext] = categories.get(ext, 0) + 1
                
    return {
        "unindexed_assets": unindexed[:50],
        "total_volume_bytes": total_bytes,
        "classification_breakdown": categories
    }
```

---

## Anti-Patterns & Guardrails

- **Unbounded Deep Directory Traversals** — Scanning network-mounted or deeply recursive root paths without max-depth limits ($D > 10$).
- **Inadvertent Lock File Ingestion** — Reading active SQLite write-ahead logs (`*.wal`) concurrently while writer threads are active.
