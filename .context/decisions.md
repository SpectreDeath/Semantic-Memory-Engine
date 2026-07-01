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
## 2026-07-01 [nexus-vault, postgresql, metadata-ingestion, v3.0.1]
**Decision**: Create Nexus Vault Bridge to ingest validated SKILL.md metadata into PostgreSQL.
**Changes**:
- `src/utils/nexus_vault.py` - scans `.kilo/vault/*.metadata.json`, extracts 4 normalized semantic fields: triggers (`tags`), constraints (`category`/`type`/`inputs`/`outputs`), workflow (`workflow` list), version (`version` with `0.0.0` fallback).
- Dual-backend: PostgreSQL (`semantic.skill_patterns` schema, JSONB fields) when `SME_USE_POSTGRES` set; SQLite (`skill_patterns` table, TEXT fields) otherwise via `gateway.nexus_db`.
- Auto-calculates Epistemic Trust Score: base 0.5 + 0.1 per signal (source attribution, >=3 workflow steps, strict SemVer, non-empty triggers, non-empty constraints), clamped to [0.0, 1.0].
- Idempotent upsert via `UNIQUE(skill_name, version)` with `ON CONFLICT DO UPDATE`.
- Lightweight: reads only sidecar metadata; never parses full SKILL.md body, never clones repos.
**Verification**: `ruff check` clean, `py_compile` clean, unit test confirmed placeholder filtering and trust score delta on source presence.
**Status**: Complete

## 2026-07-01 [ci-fixes, lint, formatting, ghost-trap, v3.0.1]
**Decision**: Fix CI Code Quality failures from commit 066c892 and subsequent formatting drift.
**Changes**:
- `extensions/ext_ghost_trap/plugin.py`: sorted import block (`error_handling` before `plugin_base`), added trailing newline at EOF.
- `extensions/ext_ghost_trap/ghost_trap_client.py`: added trailing newline at EOF.
- Ran `ruff format` project-wide: 67 files reformatted, 350 left unchanged. Committed as separate chore commit cf0bf9c to avoid noise in feature commit.
- CI block: Node.js 20 deprecation warnings are runner-level notices, not code issues. Codecov upload failure is infra-related.
**Verification**: `ruff check` clean on `gateway/ src/ extensions/` (309 files). `ruff format --check` passes on CI-scoped directories.
**Status**: Complete

## 2026-07-01 [crawl-fetch, skillsmp, live-ingestion, v3.0.1]
**Decision**: Add live skill ingestion from SkillsMP.com to `scripts/extract_skill.py`.
**Implementation**:
- `crawl fetch` subcommand (~220 lines) with helpers: `_skillsmp_search()`, `_github_url_to_raw()`, `_stream_github_raw()`, `_is_plausible_skill_md()`.
- SkillsMP stream uses `requests.get(stream=True)` with 4 KB chunks; appends `/SKILL.md` to GitHub URLs.
- `_is_plausible_skill_md()` filters out 404s, empty stubs, malformed sources: requires min 50 chars and presence of YAML frontmatter (`---`) or `## purpose`/`## description` headings.
- GitHub URL conversion handles 3 patterns: `owner/repo`, `owner/repo/tree/branch`, `owner/repo/blob/branch/path`.
**Verification**: Live API returns real entries; raw fetch retrieved 2,552-char SKILL.md for python-debugpy.
**Status**: Complete

## 2026-07-01 [windows-env, clipboard, py3.13, v3.0.1]
**Environment Constraints**:
- Windows 32-bit: clipboard fallback chain `win32clipboard` -> `ctypes` -> actionable error.
- Python 3.13 required (3.14 causes pydantic V1 incompatibility). `requires-python = '>=3.13, <3.14'` in pyproject.toml.
- `pynvml` not installed: VRAM check falls back to `recommended_gold_standards=2` without actual GPU read.
- PowerShell 5.1: no `&&` chaining; use `;` or separate commands.
- CRLF line endings on Windows cause LF warnings in git.
**Status**: Active constraints
