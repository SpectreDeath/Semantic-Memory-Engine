# SME Documentation

> Semantic Memory Engine (SME) v3.0.1 - Complete Documentation Index

## Getting Started

- **[progress.md](progress.md)** - Current project status, completed utilities, and development roadmap (most recently updated)

## Architecture & Development

### System Architecture
- **[EXTENSION_CONTRACT.md](EXTENSION_CONTRACT.md)** - Extension API specification

### Extensions & Modules
- **[TRAJECTORY_SUMMARY.md](archive/legacy/TRAJECTORY_SUMMARY.md)** - Historical extension development trajectory

### Specialized Capabilities
- **[CRAWLING_CAPABILITIES_EXPANSION.md](archive/legacy/CRAWLING_CAPABILITIES_EXPANSION.md)** - Historical crawling expansion analysis
- **[SCRAPEGRAPH_INTEGRATION_SUMMARY.md](archive/legacy/SCRAPEGRAPH_INTEGRATION_SUMMARY.md)** - Historical ScrapeGraphAI integration summary
- **[SCRAPEGRAPH_IMPROVEMENTS_SUMMARY.md](archive/legacy/SCRAPEGRAPH_IMPROVEMENTS_SUMMARY.md)** - Historical ScrapeGraphAI improvement notes

## Operations & Maintenance

### Configuration
- **[ENVIRONMENT_VARIABLES.md](archive/legacy/ENVIRONMENT_VARIABLES.md)** - Historical environment configuration settings

### Monitoring & Diagnostics
- **[ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)** - Error handling patterns and troubleshooting
- **[OPERATION_POISONED_WELL_REPORT.md](OPERATION_POISONED_WELL_REPORT.md)** - Security incident report

### Performance & Optimization
- **[PERFORMANCE_OPTIMIZATION_GUIDE.md](PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Performance tuning and optimization strategies

## Data & Storage

- **[MIGRATION_SQLITE_TO_POSTGRES.md](MIGRATION_SQLITE_TO_POSTGRES.md)** - Database migration guide

## Project Management

- **[PROJECT_REASSESSMENT.md](PROJECT_REASSESSMENT.md)** - Project review and planning

---

## Archive

Historical and obsolete documentation is stored in [`docs/archive/`](archive/).

- **[ARCHIVE_INDEX.md](archive/ARCHIVE_INDEX.md)** - Complete archive catalog

Notable archived documents include:
- `RELEASE_STRATEGY.md` (v2.0.0 release process - obsolete)
- `LEGACY_MIGRATION.md` (referencing removed legacy/ directory)
- `PHASE_3_PROGRESS.md` / `PHASE_4_COMPLETE.md` (superseded by current progress.md)

## Version Notes

**Current Version: v3.0.1**
- AI provider runs embedded in operator (sidecar removed in v3.0.1)
- Python 3.13 required
- Native mode recommended over Docker

Some documentation still contains references to v2.x or sidecar architecture and may require updating.
