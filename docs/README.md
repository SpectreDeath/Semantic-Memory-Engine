# SME Documentation

> Semantic Memory Engine (SME) v3.0.1 - Complete Documentation Index

## Getting Started

- **[progress.md](progress.md)** - Current project status, completed utilities, and development roadmap (most recently updated)
- **[ADVANCED_QUICKSTART.md](ADVANCED_QUICKSTART.md)** - Comprehensive setup and deployment guide

## Architecture & Development

### System Architecture
- **[CONTROL_ROOM_OPERATOR.md](CONTROL_ROOM_OPERATOR.md)** - Operator control and management
- **[CONTAINER_INFRASTRUCTURE_ANALYSIS.md](CONTAINER_INFRASTRUCTURE_ANALYSIS.md)** - Docker and container deployment details
- **[DEPENDENCY_GRAPH.md](DEPENDENCY_GRAPH.md)** - Project dependency relationships
- **[EXTENSION_CONTRACT.md](EXTENSION_CONTRACT.md)** - Extension API specification

### Extensions & Modules
- **[EXTENSIONS_CATALOG.md](EXTENSIONS_CATALOG.md)** - Complete extension inventory
- **[SME_LOGIC_EXTENSIONS_TRAJECTORY.md](SME_LOGIC_EXTENSIONS_TRAJECTORY.md)** - Extension development trajectory
- **[TRAJECTORY_SUMMARY.md](TRAJECTORY_SUMMARY.md)** - Overall project development roadmap

### Specialized Capabilities
- **[CRAWLING_CAPABILITIES_EXPANSION.md](CRAWLING_CAPABILITIES_EXPANSION.md)** - Web crawling and data harvesting
- **[SCRAPEGRAPH_INTEGRATION_SUMMARY.md](SCRAPEGRAPH_INTEGRATION_SUMMARY.md)** - ScrapeGraphAI integration (v2.3.4 reference - needs v3.0.1 update)
- **[SCRAPEGRAPH_IMPROVEMENTS_SUMMARY.md](SCRAPEGRAPH_IMPROVEMENTS_SUMMARY.md)** - ScrapeGraphAI enhancements and fixes

## Operations & Maintenance

### Configuration
- **[ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)** - Environment configuration settings

### Monitoring & Diagnostics
- **[ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)** - Error handling patterns and troubleshooting
- **[OPERATION_POISONED_WELL_REPORT.md](OPERATION_POISONED_WELL_REPORT.md)** - Security incident report

### Performance & Optimization
- **[PERFORMANCE_OPTIMIZATION_GUIDE.md](PERFORMANCE_OPTIMIZATION_GUIDE.md)** - Performance tuning and optimization strategies

## Data & Storage

- **[FILE_MANIFEST.md](FILE_MANIFEST.md)** - Project file inventory
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
