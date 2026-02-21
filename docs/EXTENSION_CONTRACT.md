# Extension Contract (Lawnmower Man v1.1.1)

Extensions are discovered by `ExtensionManager` and loaded from the `extensions/` directory. Each extension folder must contain a `manifest.json` and an entry-point module (default `plugin.py`).

## Required: `register_extension`

The entry-point module **must** define:

```python
def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Return the plugin instance. Required by ExtensionManager."""
    return YourPluginClass(manifest, nexus_api)
```

The manager calls this hook and stores the returned instance. Without it, the plugin is skipped.

## Plugin instance contract

The returned instance may follow one of two tiers.

### Minimal (tools only)

- **`get_tools()`** → `List[callable]`. Required. Returns the list of functions exposed as MCP tools. Each tool should have a docstring (used as description) and accept arguments appropriate for the agent (e.g. `(self, text: str)` or `(self)`).
- `on_startup()` — optional. Sync or async. Called once after load.
- `on_ingestion(raw_data, metadata)` — optional. Called when new data is ingested. Return value is **not currently used** by `ExtensionManager.notify_ingestion` (fire-and-forget). Future aggregation would require changes to the manager.

### Full (BasePlugin)

Implement `BasePlugin` from `src.core.plugin_base`: all of `on_startup`, `on_ingestion`, and `get_tools` are abstract. Use this when the extension participates in the full lifecycle and ingestion pipeline.

## Manifest

`manifest.json` should include at least:

- `plugin_id` — unique id (defaults to folder name).
- `name`, `version`, `description` — for status and tool metadata.
- `entry_point` — optional; default `"plugin.py"`.

## Loading note: relative imports

`ExtensionManager` loads each plugin via **file path** (`importlib.util.spec_from_file_location`), so the module has no parent package. Relative imports (`from .sibling import X`) will fail unless the plugin dir is on `sys.path` or the loader is changed to load extensions as packages.

**✅ Standard Pattern (Already Implemented):** All extensions should use this pattern for relative imports:

```python
try:
    from .sibling_module import SomeClass
except ImportError:
    import sys
    from pathlib import Path
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from sibling_module import SomeClass
```

This fallback mechanism is already implemented across all extensions and ensures compatibility when loaded via file path by the ExtensionManager.

## NexusAPI: Avoid Gateway Imports

Extensions receive `nexus_api` (implements `NexusAPI` from `src.core.nexus_interface`). Use it instead of importing from gateway:

- **DB access**: `nexus_api.nexus.execute(sql, params)` and `nexus_api.nexus.query(sql, params)`
- **HSM/TPM**: `nexus_api.get_hsm()` — returns the HardwareSecurity module for signing/verification

Do **not** import `gateway.hardware_security` or `gateway.nexus_db` in extensions. When `nexus_api` is `None` (e.g. tests), the ExtensionManager passes a `DefaultExtensionContext` that provides nexus and get_hsm.

Note: `gateway.gatekeeper_logic` (calculate_trust_score, etc.) is still imported by some extensions; moving it to `src.core` is a future refactor.

## Recent Improvements (Phase 1 Complete)

### ✅ ReasoningQuantizer Implementation
- **Status**: Fully implemented with actual CSV→HDF5 parsing
- **Features**: 
  - Auto-detection of CSV formats (ConceptNet, custom, auto)
  - Support for both ConceptNet-style and custom subject-predicate-object formats
  - High-performance HDF5 storage with structured datasets
  - Progress tracking and statistics reporting
  - Error handling and validation

### ✅ AuditEngine Integration
- **CLI**: Available via `sme drift --claims file.json` or `sme drift --inline '[{"subject":"A","predicate":"is","object":"B"}]'`
- **API**: Available via `POST /api/v1/drift/analyze` with JSON payload
- **Features**: Drift analysis comparing claims against knowledge core, anomaly detection, verification scoring

### ✅ Import Issue Resolution
- **Status**: All extensions already implement proper relative import fallbacks
- **Pattern**: Consistent try/except ImportError with sys.path manipulation
- **Compatibility**: Works with ExtensionManager's file-path loading mechanism

## Development Guidelines

### Creating New Extensions

1. **Create extension directory**: `extensions/ext_your_extension/`
2. **Add manifest.json**:
   ```json
   {
     "plugin_id": "ext_your_extension",
     "name": "Your Extension Name",
     "version": "1.0.0",
     "description": "Description of your extension",
     "entry_point": "plugin.py"
   }
   ```
3. **Implement plugin.py** with required `register_extension` function
4. **Use relative import pattern** for any sibling modules
5. **Follow BasePlugin contract** if you need full lifecycle support

### Testing Extensions

Use the extension matrix test to verify all extensions load correctly:
```bash
python -m pytest tests/test_extension_matrix.py -v
```

### Best Practices

- Use `NexusAPI` for all database and HSM operations
- Implement proper error handling and logging
- Use the relative import fallback pattern for all internal imports
- Follow the established tool naming conventions
- Document all tools with clear descriptions and parameter types

See `docs/SME_LOGIC_EXTENSIONS_TRAJECTORY.md` for the full trajectory and file references.
