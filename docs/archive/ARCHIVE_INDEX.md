# Documentation Archive Index

> This directory contains obsolete or superseded documentation from the SME project.

## Archived Files

### Outdated Version Documentation

| File | Original Location | Archived | Reason |
|------|------------------|----------|--------|
| `RELEASE_STRATEGY.md` | docs/ | 2026-04-21 | Documents v2.0.0 release process; current version is v3.0.1 (sidecar removed, AI provider embedded) |
| `ADVANCED_QUICKSTART.md` | docs/ | 2026-06-17 | References removed legacy modules, `requirements.txt`, and v2-era Control Room workflow |
| `CONTROL_ROOM_OPERATOR.md` | docs/ | 2026-06-17 | v2.0.0 sidecar/container guide; current v3.0.1 runs native embedded provider |
| `ENVIRONMENT_VARIABLES.md` | docs/ | 2026-06-17 | References `SME_SIDECAR_URL` and container defaults obsolete in v3.0.1 |
| `CONTAINER_INFRASTRUCTURE_ANALYSIS.md` | docs/ | 2026-06-17 | Sidecar/container deployment analysis superseded by native operator mode |
| `EXTENSIONS_CATALOG.md` | docs/ | 2026-06-17 | v2.0.0 extension inventory; drift-prone and superseded by live `extensions/` tree |
| `SCRAPEGRAPH_INTEGRATION_SUMMARY.md` | docs/ | 2026-06-17 | v2.3.4 ScrapeGraphAI integration summary; kept for historical reference |
| `SCRAPEGRAPH_IMPROVEMENTS_SUMMARY.md` | docs/ | 2026-06-17 | Historical ScrapeGraphAI extension improvement notes |
| `CRAWLING_CAPABILITIES_EXPANSION.md` | docs/ | 2026-06-17 | Speculative crawling roadmap referencing removed `legacy/harvester_crawler.py` |
| `TRAJECTORY_SUMMARY.md` | docs/ | 2026-06-17 | Historical extension trajectory; superseded by current progress tracking |
| `RELEASE_STRATEGY.md` | docs/ | 2026-04-21 | v2.0.0 release process obsolete |

### Migration & Legacy Planning

| File | Original Location | Archived | Reason |
|------|------------------|----------|--------|
| `LEGACY_MIGRATION.md` | docs/ | 2026-04-21 | Migration plan for `legacy/` directory; `legacy/` no longer exists in project root |
| `PHASE_3_PROGRESS.md` | docs/ | 2026-04-21 | Superseded by consolidated `progress.md` |
| `PHASE_4_COMPLETE.md` | docs/ | 2026-04-21 | Superseded by consolidated `progress.md` |
| `DEPENDENCY_GRAPH.md` | docs/ | 2026-06-17 | Superseded by current project structure and dependency metadata |
| `FILE_MANIFEST.md` | docs/ | 2026-06-17 | Superseded by live filesystem and git status |
| `SME_LOGIC_EXTENSIONS_TRAJECTORY.md` | docs/ | 2026-06-17 | Superseded by current extension architecture and v3.0.1 native mode |

## Archived Scripts

| File | Original Location | Archived | Reason |
|------|------------------|----------|--------|
| `modernize_dataclasses.py` | scripts/ | 2026-06-17 | One-off migration utility no longer part of active workflow |
| `modernize_types.py` | scripts/ | 2026-06-17 | One-off migration utility no longer part of active workflow |
| `remove_pydantic_patches.py` | scripts/ | 2026-06-17 | One-off migration utility no longer part of active workflow |
| `test_scrapegraph_integration.py` | scripts/ | 2026-06-17 | Superseded by extension tests; moved with ScrapeGraph integration summary |
| `test_scrapegraph_simple.py` | scripts/ | 2026-06-17 | Superseded by extension tests; moved with ScrapeGraph integration summary |
| `vendor_faststylometry.py` | scripts/ | 2026-06-17 | One-off vendoring utility no longer part of active workflow |
| `vendor_faststylometry_local.py` | scripts/ | 2026-06-17 | One-off vendoring utility no longer part of active workflow |

## Note on Specs

The `docs/specifications/` directory contains **active** specifications:
- `ghost_trap_spec.md` - Current (2026-02-21)
- `epistemic_gatekeeper_spec.md` - Current (2026-02-21)
- `archival_diff_spec.md` - Current (2026-02-21)

These are **NOT** archived; they represent active extension architecture.

## Cleanup Date

- **Initial archival:** 2026-04-21
- **Additional cleanup:** 2026-06-17
- **Part of:** ROT (Redundant, Outdated, Trivial) cleanup
- **Related commit:** d4b244f

## Restoration

If any archived file needs to be restored for reference:
```bash
# Copy from archive back to docs/
cp docs/archive/FILENAME.md docs/FILENAME.md
```
Then update the file to current version standards as needed.
