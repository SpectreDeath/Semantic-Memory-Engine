# SME Logic, Extensions & Plugins — Analysis & Trajectory

This document summarizes the structure of the SME **logic layer**, **extensions**, and **plugin system**, plus concrete improvements and a trajectory to follow.

---

## 1. Current Structure

### 1.1 Logic layer (`src/logic/`)

| File | Purpose | Used by |
|------|---------|--------|
| `manifest_manager.py` | File hashing, lineage (stale check), `data/manifest.json` | `sme_cli` (`index`, `status`) |
| `reasoning_quantizer.py` | HDF5 “distillation” (entities/relationships groups) | `sme_cli` (`index`) |
| `audit_engine.py` | HDF5 drift analysis (claims vs knowledge core) | **Nothing** (unused) |

**Gaps**

- No `src/logic/__init__.py` — directory is not a proper package.
- **AuditEngine** is never imported; either wire it (API/CLI/extension) or document as future/optional.
- **ReasoningQuantizer.distill_assertions** is a stub: creates empty HDF5 groups, no real CSV→HDF5 parsing.
- Logic is **CLI-only**; no use from API, gateway, or extensions.

### 1.2 Extensions (`extensions/`)

- **Discovery**: `ExtensionManager` (gateway) scans `extensions/` for `manifest.json`, loads `entry_point` (default `plugin.py`).
- **Contract**: Module must define `register_extension(manifest, nexus_api)` returning the plugin instance. Instance should have:
  - `on_startup()` (optional, sync or async)
  - `on_ingestion(raw_data, metadata)` (optional)
  - `get_tools()` → list of callables (used by MCP).
- **Base**: `src/core/plugin_base.py` defines `BasePlugin` (ABC) with `on_startup`, `on_ingestion`, `get_tools` — but many extensions do **not** subclass it.

**Extension inventory (by contract)**

- **Use BasePlugin + `register_extension`**: e.g. intended for `ext_adversarial_breaker` (had `create_plugin` only → **fixed** to expose `register_extension`).
- **Custom class + `register_extension`**: `ext_archival_diff`, `ext_epistemic_gatekeeper`, `ext_sample_echo`, `ext_tactical_forensics` — no `BasePlugin`, optional `on_ingestion`.
- **Duplicate scout**: `ext_archival_diff` has two scouts — `ext_archival_diff/scout.py` (sync, requests) used by plugin, and `ext_archival_diff/ext_archival_diff/scout.py` (async, httpx) — redundant/divergent.

### 1.3 Gateway / Plugin loading

- **ExtensionManager** (`gateway/extension_manager.py`): `discover_and_load()` → `_load_module()` expects `register_extension(manifest, nexus_api)`.
- **get_status()**: Returns `List[Dict]` (one dict per extension with `id`, `name`, `version`, `tools_count`). Callers that expect a single dict with key `"loaded_extensions"` are wrong — e.g. **test_extension_matrix** (fixed in trajectory).
- **get_extension_tools()**: Aggregates tools from all extensions; each tool has `name`, `description`, `handler`, `plugin_id`. Many handlers are **async**; tests that call `handler("")` without `await` get a coroutine, not a string (test fixed to handle async).

---

## 2. Improvements Identified

### 2.1 Critical / Done in this pass

1. **ext_adversarial_breaker**
   - Expose `register_extension(manifest, nexus_api)` (manager only looks for this name). Keep `create_plugin` as internal or alias.
   - Remove dead duplicate block in `analyze_text` (second docstring + try/except after an unconditional return).
   - Fix relative import when loaded as standalone module: `ExtensionManager` loads plugin by file path, so `from .logic_anomaly_detector` fails with "no known parent package". Use try/except `ImportError` and add plugin dir to `sys.path` + `from logic_anomaly_detector import ...` as fallback.

2. **tests/test_extension_matrix.py**
   - **test_all_extensions_discovered**: `get_status()` returns a list; derive loaded IDs as `{s["id"] for s in loaded}` (or equivalent) instead of `loaded.get("loaded_extensions", [])`.
   - **test_extension_handler_returns_string**: Tool handlers are often async; use `inspect.iscoroutinefunction` and `asyncio.run(handler(...))` when calling (avoid deprecated `asyncio.iscoroutinefunction`).

3. **src/core/plugin_base.py**
   - Type hint: `List[callable]` → `List[Callable[..., Any]]` with `from typing import Callable` (and `Any`).

4. **src/logic**
   - Add `src/logic/__init__.py` (can re-export `ManifestManager`, `ReasoningQuantizer`, `AuditEngine` for a single import path).

### 2.2 Short-term trajectory

1. **Unify extension contract**
   - Either require all plugins to implement `BasePlugin`, or document two tiers: “full” (lifecycle + tools) vs “minimal” (tools only). Update ExtensionManager docstring and any contributor docs.

2. **Logic layer usage**
   - **AuditEngine**: Add a CLI command or API endpoint that calls `AuditEngine.analyze_drift(claims)`, or mark it “reserved for future use” and add a short comment in code.
   - **ReasoningQuantizer**: Either implement real CSV→HDF5 in `distill_assertions` or rename to make “stub” clear and add a TODO.

3. **ext_archival_diff scouts**
   - Choose one implementation (sync vs async) or a single facade; remove or clearly deprecate the other (e.g. `ext_archival_diff/ext_archival_diff/scout.py` if plugin uses top-level `scout.py`).

4. **ExtensionManager**
   - In `get_status()`, guard `instance.get_tools()` with `hasattr` (already done) and ensure no plugin is required to implement `on_ingestion` if not using BasePlugin.
   - **Relative imports**: Plugins are loaded via `spec_from_file_location(plugin_id, path)`, so they have no parent package and `from .sibling import X` fails. Options: (a) in each plugin, try relative import then fallback to adding plugin dir to `sys.path` and absolute import; (b) load extensions as packages (add `extensions` to `sys.path`, ensure each extension dir has `__init__.py`, use `importlib.import_module(f"{item}.plugin")`).

### 2.3 Medium-term trajectory

1. **Reduce coupling**
   - Extensions currently import `gateway.hardware_security`, `gateway.nexus_db` directly. Prefer a narrow “nexus” interface passed in by the gateway (e.g. from `plugin_base`) so extensions don’t depend on gateway internals.

2. **Ingestion pipeline**
   - If `on_ingestion` return value is used later, document it and have ExtensionManager aggregate results; otherwise keep current “fire-and-forget” and document.

3. **Logic package API**
   - In `src/logic/__init__.py`, export public classes and add a one-line docstring so `from src.logic import ManifestManager, ReasoningQuantizer, AuditEngine` is the standard import.

---

## 3. Trajectory Checklist

| Phase | Item | Status |
|-------|------|--------|
| **Immediate** | Add `register_extension` to ext_adversarial_breaker | ✅ |
| **Immediate** | Remove duplicate block in ext_adversarial_breaker `analyze_text` | ✅ |
| **Immediate** | Fix test_extension_matrix get_status + async handler handling | ✅ |
| **Immediate** | Add `src/logic/__init__.py` | ✅ |
| **Immediate** | Fix plugin_base typing `List[callable]` → `List[Callable[..., Any]]` | ✅ |
| **Short-term** | Document extension contract (BasePlugin vs minimal) | ✅ |
| **Short-term** | Wire or document AuditEngine; clarify ReasoningQuantizer stub | ✅ |
| **Short-term** | Add register_extension + relative-import fallback to all extensions | ✅ |
| **Short-term** | Consolidate ext_archival_diff scout(s) | ✅ |
| **Medium-term** | Narrow nexus API for extensions (reduce gateway coupling) | ✅ |
| **Medium-term** | Document on_ingestion return value usage (if any) | ✅ |

---

## 4. File Reference

- **Logic**: `src/logic/manifest_manager.py`, `reasoning_quantizer.py`, `audit_engine.py`
- **Plugin base**: `src/core/plugin_base.py`
- **Extension loading**: `gateway/extension_manager.py`
- **Extension tools / MCP**: `gateway/mcp_server.py`, `gateway/tool_registry.py`
- **CLI (logic usage)**: `sme_cli/main.py`
- **Extension test**: `tests/test_extension_matrix.py`
