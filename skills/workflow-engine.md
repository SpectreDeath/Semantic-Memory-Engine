---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Advanced
Type: Tool
Category: Orchestration
name: workflow-engine
Source: Semantic Memory Engine (SME)
Source_File: src/orchestration/workflow_engine.py
---

## Purpose

Enables chaining SME skills/tools into executable workflows with state management, error handling, and parallel execution.

## Description

The Workflow Engine provides orchestration capabilities for SME. It allows defining multi-step workflows that execute in sequence or parallel, with dependency management, retry logic, and persistent execution tracking.

## Workflow

1. **Define**: Create workflow with steps and dependencies
2. **Register**: Register step handlers (skills/tools)
3. **Execute**: Run workflow with input data
4. **Track**: Monitor execution, handle errors, retries
5. **Complete**: Store results in database

## Examples

### Example 1: Research Workflow
**Input**: Topic: "AI ethics"
**Output**: Comprehensive report with sources
**Steps**: harvest_url → sentiment → stylometry → summarize

### Example 2: OSINT Investigation
**Input**: Username: "@target"
**Output**: Bot detection + profile analysis
**Steps**: osint_scan → bot_detection → trust_score

### Example 3: Parallel Analysis
**Input**: List of URLs
**Output**: Multi-source analysis results
**Steps**: Multiple harvest_url steps in parallel

## Implementation Notes

- **Location**: `D:/SME/src/orchestration/workflow_engine.py`
- **Database**: SQLite (storage.db_path)
- **API Endpoints**:
  - GET /workflows - List workflows
  - POST /workflows - Create workflow
  - POST /workflows/{id}/execute - Run workflow
  - GET /workflows/steps - List available steps
- **Step Registry**: Maps step names to actual handlers in `step_registry.py`