# Documentation Archive Index

> This directory contains obsolete or superseded documentation from the SME project.

## Archived Files

### Outdated Version Documentation

| File | Original Location | Archived | Reason |
|------|------------------|----------|--------|
| `RELEASE_STRATEGY.md` | docs/ | 2026-04-21 | Documents v2.0.0 release process; current version is v3.0.1 (sidecar removed, AI provider embedded) |
| `CONTROL_ROOM_OPERATOR.md` | docs/ | TBD | References sidecar + v2.0.0; needs v3.0.1 update or archival |
| `ADVANCED_QUICKSTART.md` | docs/ | TBD | References v2.0.0 Control Room; needs update for v3.0.1 native mode |
| `SCRAPEGRAPH_INTEGRATION_SUMMARY.md` | docs/ | TBD | References v2.3.4; should be updated to current version |
| `RELEASE_STRATEGY.md` | docs/ | 2026-04-21 | v2.0.0 release process obsolete |

### Migration & Legacy Planning

| File | Original Location | Archived | Reason |
|------|------------------|----------|--------|
| `LEGACY_MIGRATION.md` | docs/ | 2026-04-21 | Migration plan for `legacy/` directory; `legacy/` no longer exists in project root |
| `PHASE_3_PROGRESS.md` | docs/ | 2026-04-21 | Superseded by consolidated `progress.md` |
| `PHASE_4_COMPLETE.md` | docs/ | 2026-04-21 | Superseded by consolidated `progress.md` |

## Note on Specs

The `docs/specifications/` directory contains **active** specifications:
- `ghost_trap_spec.md` - Current (2026-02-21)
- `epistemic_gatekeeper_spec.md` - Current (2026-02-21)
- `archival_diff_spec.md` - Current (2026-02-21)

These are **NOT** archived; they represent active extension architecture.

## Cleanup Date

- **Initial archival:** 2026-04-21
- **Part of:** ROT (Redundant, Outdated, Trivial) cleanup
- **Related commit:** d4b244f

## Restoration

If any archived file needs to be restored for reference:
```bash
# Copy from archive back to docs/
cp docs/archive/FILENAME.md docs/FILENAME.md
```
Then update the file to current version standards as needed.
