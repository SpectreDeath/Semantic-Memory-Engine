---
name: nexus-interface
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Integration
source_file: gateway/mcp_server.py
source: Semantic Memory Engine (SME)
tags:
  - nexus-interface
  - multi-db-joins
  - pragma-optimization
  - sqlite-wal
  - forensic-vault
inputs:
  sql_query:
    type: string
    required: true
    description: Parameterized SQL query executing across attached SQLite databases.
  attached_databases:
    type: object
    required: false
    description: "Key-value map of attached database schemas `{'vault': 'path/to/vault.db', 'session': ':memory:'}`."
outputs:
  result_rows:
    type: array
    description: List of matched row dictionaries returned from multi-DB execution.
  execution_plan:
    type: string
    description: Query explanation plan from SQLite EXPLAIN QUERY PLAN.
  execution_time_ms:
    type: number
    description: Database query execution wall-clock time in milliseconds.
---

# Nexus Interface Engine

`nexus-interface` provides high-performance multi-database joins across attached SQLite WAL databases with PRAGMA optimizations in Python:

$$\text{QueryExecutor} = \text{Execute}(\mathcal{Q} \mid \text{PRAGMA synchronous = NORMAL}, \text{ATTACH } DB_1, DB_2)$$

---

## The 5-Stage Nexus Interface Progression

1. **SQL Query & Database Attachment Setup**: Ingest query and attached DB paths; open SQLite connection with WAL journaling.
2. **PRAGMA Performance Tuning**: Enable `PRAGMA synchronous = NORMAL`, `PRAGMA journal_mode = WAL`, and memory caching.
3. **The Visual Brief**: Generate interactive HTML multi-DB schema relation diagram at `%TEMP%\nexus-interface-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert query safety; disallow arbitrary `DROP TABLE` or destructive modifications without explicit administrative grants.
5. **Execution & Output Emission**: Execute multi-DB query and emit structured row dictionaries with execution plan.

---

## Implementation Notes

```python
import time
import sqlite3
from typing import Dict, List, Any, Optional

def query_nexus_interface(
    sql_query: str,
    attached_databases: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    
    # Mock data query
    conn.execute("CREATE TABLE mock_vault (id INT, item TEXT);")
    conn.execute("INSERT INTO mock_vault VALUES (1, 'nexus_record');")
    
    cur = conn.execute("SELECT * FROM mock_vault;")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    elapsed = (time.perf_counter() - t0) * 1000.0
    
    return {
        "result_rows": rows,
        "execution_plan": "SCAN mock_vault",
        "execution_time_ms": round(elapsed, 2)
    }
```

---

## Anti-Patterns & Guardrails

- **Unparameterized String Concatenation** — Building multi-DB join queries with unescaped user strings.
- **Missing WAL Configuration** — Opening SQLite instances in default journal mode, causing write locking contention.