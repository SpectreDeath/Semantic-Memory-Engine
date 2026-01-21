# 🚀 Quick Start Guide - New Features

This guide shows you how to use the new features implemented in the SimpleMem Laboratory refactoring.

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# That's it! All 10 enhancements are included.
```

---

## 1️⃣ Using the New Package Exports

**Simple imports for common tools:**

```python
# Instead of importing from scattered modules...
from src.scribe.engine import ScribeEngine
from src.query.scout_integration import Scout
from src.query.engine import SemanticSearchEngine

# Now use this:
from src import ScribeEngine, Scout, SemanticSearchEngine, Config, ToolFactory

# Even simpler - use the factory
scribe = ToolFactory.create_scribe()
scout = ToolFactory.create_scout()
```

---

## 2️⃣ Using Centralized Configuration

**Before** (hardcoded paths):
```python
DB_PATH = "d:\\mcp_servers\\storage\\laboratory.db"
LOG_DIR = "d:\\mcp_servers\\data\\logs"
```

**After** (centralized):
```python
from src import Config

config = Config()

# Get configuration values with dot notation
db_path = config.get('storage.db_path')
log_dir = config.get('storage.log_dir')

# Type-safe getters
timeout = config.get_int('mcp.timeout', default=30)
threshold = config.get_float('analysis.similarity_threshold', default=0.6)

# Get as Path objects
db_path = config.get_path('storage.db_path')
```

---

## 3️⃣ Using the Tool Factory

**Cleaner dependency management:**

```python
from src.core.factory import ToolFactory

# Create tools (instances are cached)
scribe = ToolFactory.create_scribe()
scout = ToolFactory.create_scout()
search = ToolFactory.create_search_engine()
synapse = ToolFactory.create_synapse()
centrifuge = ToolFactory.create_centrifuge()
semantic_db = ToolFactory.create_semantic_db()
monitor = ToolFactory.create_monitor()

# Check what's loaded
loaded_tools = ToolFactory.list_instances()
print(loaded_tools)  # {'scribe': 'ScribeEngine', 'scout': 'Scout', ...}

# Health check
health = ToolFactory.health_check()
if health['scribe']:
    print("✅ Scribe is healthy")
```

---

## 4️⃣ Using Backward Compatible Imports

**Old code still works!**

```python
# These still work even though they're not recommended
from harvester_spider import HarvesterSpider
from scribe_authorship import ScribeEngine
from memory_synapse import MemoryConsolidator
from adaptive_scout import Scout

# These are actually imported from the new locations
# but via backward compatibility shims
```

---

## 5️⃣ Using the CLI Entry Point

**Discover and run tools from the command line:**

```bash
# List all available tools
python __main__.py list
# or
python -m src list

# Output:
# 🧪 SimpleMem Laboratory - Available Tools
#
# scribe          | Scribe Authorship Engine
#                 | Forensic authorship analysis and attribution
#
# scout           | Scout Adaptive Query System
#                 | Intelligent knowledge gap detection...
# [more tools...]

# Get info about a specific tool
python __main__.py info scribe
python __main__.py info scout

# Show help
python __main__.py help

# Show version
python __main__.py version
```

---

## 6️⃣ Running Integration Tests

**Verify the new architecture:**

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestImportStructure -v

# Run specific test
pytest tests/test_integration.py::TestConfiguration::test_config_singleton -v

# Expected output:
# tests/test_integration.py::TestImportStructure::test_backward_compat_imports PASSED
# tests/test_integration.py::TestImportStructure::test_new_imports PASSED
# tests/test_integration.py::TestConfiguration::test_config_singleton PASSED
# ... [more tests] ...
# ======================== 15 passed in 0.25s ========================
```

---

## 7️⃣ Creating a Simple Application

**Complete example using new features:**

```python
#!/usr/bin/env python
"""
Simple application using new SimpleMem features
"""

from src import Config, ToolFactory

def main():
    # 1. Load configuration
    config = Config()
    print(f"Database: {config.get('storage.db_path')}")
    print(f"Logs: {config.get('storage.log_dir')}")
    
    # 2. Create tools via factory
    scribe = ToolFactory.create_scribe()
    scout = ToolFactory.create_scout()
    search = ToolFactory.create_search_engine()
    
    # 3. Use the tools
    print(f"\n✅ Tools loaded: {ToolFactory.list_instances()}")
    
    # 4. Verify health
    health = ToolFactory.health_check()
    print(f"✅ System health: {health}")
    
    # 5. Use scribe for analysis
    text = "This is a sample document for analysis."
    fingerprint = scribe.extract_linguistic_fingerprint(text)
    print(f"\n✅ Linguistic fingerprint extracted")
    
    # 6. Use scout for knowledge gaps
    results = scout.detect_knowledge_gaps(text)
    print(f"✅ Knowledge gaps detected")

if __name__ == "__main__":
    main()
```

---

## 8️⃣ Configuration File Location

**Location**: `config/config.yaml`

```yaml
storage:
  base_dir: "D:/mcp_servers/data"
  db_path: "D:/mcp_servers/data/storage/laboratory.db"
  log_dir: "D:/mcp_servers/data/logs"
  lexicon_dir: "D:/mcp_servers/data/lexicons"

analysis:
  thresholds:
    high_alert_sentiment: 0.4
    similarity_threshold: 0.6
  lookback_days: 7

mcp:
  host: "localhost"
  port: 8000
```

**To modify**: Edit paths to match your system, then:

```python
# Reload configuration
from src.core.config import Config
config = Config()
config.reload()  # Reloads from file
```

---

## 9️⃣ Type Hints (For Contributors)

**Add type hints as you work:**

```python
from typing import List, Dict, Optional
from src import ScribeEngine, Config

def analyze_text(text: str) -> Dict[str, float]:
    """
    Analyze text and return metrics.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary with analysis results
    """
    scribe: ScribeEngine = ToolFactory.create_scribe()
    config: Config = Config()
    
    # Code here...
    return {}

# Run type checking
# mypy your_script.py
```

---

## 🔟 Monitoring Tools Health

**Check system status:**

```python
from src.core.factory import ToolFactory

# Check all tools
health = ToolFactory.health_check()

for tool, is_healthy in health.items():
    status = "✅" if is_healthy else "❌"
    print(f"{status} {tool}")

# Example output:
# ✅ scribe
# ✅ scout
# ✅ search
# ✅ synapse
# ✅ centrifuge
```

---

## 📚 Documentation Files

- **`docs/MIGRATION_CHECKLIST.md`** - Migration progress tracking
- **`docs/DEPENDENCY_GRAPH.md`** - Dependency relationships
- **`IMPLEMENTATION_SUMMARY.md`** - This implementation
- **`README.md`** - Updated for new structure
- **`REFACTORING_SUMMARY.md`** - Original refactoring notes

---

## 🎯 Common Patterns

### Pattern 1: Lazy Loading with Factory
```python
# Tools are only created when needed
scribe = ToolFactory.create_scribe()  # Created now
# ... much later ...
scout = ToolFactory.create_scout()    # Created now
```

### Pattern 2: Configuration-Driven Code
```python
config = Config()
batch_size = config.get_int('processing.batch_size', default=100)
retry_count = config.get_int('processing.max_retries', default=3)
```

### Pattern 3: Dependency Injection
```python
def process_document(scribe: ScribeEngine = None):
    if scribe is None:
        scribe = ToolFactory.create_scribe()
    # Use scribe...
```

---

## ⚠️ Migration from Old Code

**Old code:**
```python
from scribe_authorship import ScribeEngine
from adaptive_scout import Scout

scribe = ScribeEngine()
scout = Scout()
```

**Recommended new code:**
```python
from src import ToolFactory

scribe = ToolFactory.create_scribe()
scout = ToolFactory.create_scout()
```

**Why?**
- ✅ Centralized initialization
- ✅ Dependency management
- ✅ Easier testing and mocking
- ✅ Configuration consistency

---

## 🐛 Troubleshooting

### Problem: `Config not found`
```python
# Solution: Ensure config/config.yaml exists
# Or set config path before importing:
import os
os.chdir('/path/to/mcp_servers')
from src import Config
```

### Problem: Import errors
```python
# Solution: Run tests to verify structure
pytest tests/test_integration.py -v

# Or verify imports directly
python -c "from src import ScribeEngine, Scout; print('✅ OK')"
```

### Problem: Tools not initializing
```python
# Solution: Check factory health
from src.core.factory import ToolFactory
health = ToolFactory.health_check()
print(health)  # Shows which tools failed
```

---

## 📊 File Structure Quick Reference

```
d:\mcp_servers\
├── __main__.py                    # 🆕 CLI entry point
├── config/
│   └── config.yaml               # Configuration file
├── src/
│   ├── __init__.py               # 🆕 Enhanced exports
│   ├── core/
│   │   ├── config.py             # 🆕 Config singleton
│   │   ├── factory.py            # 🆕 Tool factory
│   │   ├── centrifuge.py
│   │   ├── semantic_db.py
│   │   └── ...
│   ├── scribe/
│   ├── query/
│   ├── synapse/
│   └── ...
├── data/
│   ├── storage/
│   ├── logs/
│   └── lexicons/
├── docs/
│   ├── MIGRATION_CHECKLIST.md    # 🆕 Migration tracking
│   ├── DEPENDENCY_GRAPH.md        # 🆕 Dependencies
│   └── ...
├── tests/
│   ├── test_integration.py        # 🆕 Integration tests
│   └── ...
├── requirements.txt               # ✅ Updated
└── README.md
```

---

## ✅ Verification Checklist

Run this to verify everything works:

```bash
# 1. Check Python version
python --version  # Should be 3.8+

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify imports
python -c "from src import ToolFactory, Config; print('✅ Imports OK')"

# 4. Run tests
pytest tests/test_integration.py -v

# 5. List tools
python __main__.py list

# 6. Check config
python -c "from src import Config; c = Config(); print('✅ Config OK')"
```

If all pass: ✅ **You're ready to go!**

---

**Happy coding! 🚀**

For more details, see the full documentation in `docs/` and `IMPLEMENTATION_SUMMARY.md`.
