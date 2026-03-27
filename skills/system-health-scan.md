---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Diagnostics
name: system-health-scan
Source: Semantic Memory Engine (SME)
Source_File: extensions/ext_stetho_scan/
---

## Purpose

Performs comprehensive system health and diagnostic scanning to assess SME infrastructure, detect issues, and provide optimization recommendations.

## Description

The Stetho Scan is a deep diagnostic tool that examines the SME system's health across multiple dimensions: database connectivity, API responsiveness, extension loading, memory usage, and processing queues. It provides actionable recommendations for maintenance and optimization.

## Workflow

1. **Component Enumeration**: List all SME components and extensions
2. **Connectivity Testing**: Verify database and API connections
3. **Performance Sampling**: Measure response times and resource usage
4. **Queue Analysis**: Check pending tasks and processing backlog
5. **Error Scanning**: Identify recent errors and warnings
6. **Health Scoring**: Calculate overall system health index
7. **Recommendation Generation**: Provide optimization suggestions

## Examples

### Example 1: Full System Diagnostic
**Input**: Request for comprehensive health check
**Output**: Health report with component status
**Use Case**: Routine maintenance

### Example 2: Issue Investigation
**Input**: Specific symptom or error
**Output**: Focused diagnostic on related components
**Use Case**: Troubleshooting

### Example 3: Pre-deployment Check
**Input**: System readiness verification request
**Output**: Readiness score with gap analysis
**Use Case**: Before major operations

## Implementation Notes

- **Checks**: Database, API, extensions, memory, queues, logs
- **Output**: JSON report with health scores
- **Extension**: Stetho Scan
- **Location**: `D:/SME/extensions/ext_stetho_scan/`

## See Also

- [Extensions Catalog](D:/SME/docs/EXTENSIONS_CATALOG.md)
- [Performance Optimization Guide](D:/SME/docs/PERFORMANCE_OPTIMIZATION_GUIDE.md)
