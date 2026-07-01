# SME Architecture Decisions

## 2026-06-28: Phase Testing Strategy Verified
**Decision**: Phase testing confirmed working
**Results**: All 652 tests pass across 3 phases
**Status**: Complete

## 2026-06-28: Ghost Trap Plugin Refactoring
**Decision**: Refactor `ext_ghost_trap/plugin.py` to extend `BasePlugin`
**Changes**:
- Added logging instead of print statements
- Added ErrorHandler integration
- Changed `get_tools()` to return list (from stetho_scan pattern)
- Added 37 tests covering plugin, detector, monitor, and client
**Coverage**: 0% → 15% for ext_ghost_trap
**Status**: Complete

## 2026-06-28: Ghost Trap Client Syntax Fix
**Decision**: Fix syntax error in `ghost_trap_client.py` line 169
**Fix**: Changed `event.get("path", event.get("target", ""))).lower()` to proper nesting
**Status**: Complete
## 2026-06-30 [extraction, skill-creation, v3.0.1, architecture]
- Built skill extraction terminal wrapper for SME v3.0.1. Core module at src/utils/skill_extractor.py provides SkillExtractor class with VRAM-aware few-shot injection (max 2 gold standards for GTX 1660 Ti 6GB). CLI script at scripts/extract_skill.py with commands: extract, batch, vault list/sync, gold list/add, doctor. Outputs SKILL.md + metadata.json to .kilo/vault/. Uses SME AI Provider factory (sentinel/langflow/mock). Error handling covers model timeouts, JSON parse failures, invalid JSON structure, missing required fields (skill_name, purpose, description, workflow). Gold standards in skills/gold_standard/ with manifest.json tracking use-when metadata. Entry point extract-skill registered in pyproject.toml.

## 2026-06-30 [production-hardening, extraction, v3.0.1]
**Decision**: Harden skill extraction pipeline from demonstration-grade to production-grade.
**Changes**:
- `extract_json_payload()` standalone function: brace-depth scanner replaces greedy `r"\{.*\}"` regex. Correctly handles nested JSON (`{"extraction": {"nested": {...}}}`) while rejecting bare prose braces like `{skill_name}`. Respects string boundaries and escape sequences.
- `resolve_extraction_response()` standalone function: unwraps nested `extraction` key, hoists `status`/`errors` from parent or inner level. Fixes layer-mismatch bug where nested `{"extraction": {"status": "failure"}}` was misread as success.
- `validate()` rewritten to collect ALL violations before returning. Added placeholder filtering (`N/A`, `TODO`, `placeholder`, `none`, `xyz`). Added strict SemVer `^\d+\.\d+\.\d+$`. Tags require lowercase kebab-case. Per-step workflow validation. Removed `break` on first invalid tag.
- `_apply_vram_cap()` in CLI: programmatically enforces VRAM safety threshold on `--max-gold`. Integrated into both `extract_cmd` and `batch_cmd` before context build. Logs original→enforced transition with `[WARN]` banner.
- Added `examples_text: str` to `ExtractedSkill` dataclass — resolves latent `AttributeError` in `_render_skill_md()`.
- Timestamp upgraded to `%Y-%m-%dT%H:%M:%S.%f%z` for microsecond-precision, sortable ISO 8601.
**Verification**: All unit tests pass (nested JSON, prose rejection, failure hoisting, placeholder filtering, 6-error collection, ruff clean, doctor green).
**Status**: Complete
