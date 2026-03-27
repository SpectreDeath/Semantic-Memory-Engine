---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Utilities
name: log-analysis
Source: Semantic Memory Engine (SME)
Source_File: src/utils/log_utils.py
---

## Purpose

Provides log parsing, filtering, searching, and analysis capabilities for SME system logs.

## Description

The Log Analysis utility processes SME system logs for debugging, monitoring, and audit purposes. It supports filtering by level, searching patterns, aggregating statistics, and generating insights.

## Workflow

1. **Log Ingestion**: Load log files
2. **Filtering**: Apply log level filters
3. **Search**: Find specific patterns
4. **Analysis**: Extract statistics
5. **Reporting**: Generate log report

## Examples

### Example 1: Error Analysis
**Input**: Log files
**Output**: Error summary
**Use Case**: Debugging

### Example 2: Pattern Search
**Input**: Search pattern
**Output**: Matching entries
**Use Case**: Investigation

## Implementation Notes

- **Formats**: Structured and unstructured logs
- **Location**: `D:/SME/src/utils/log_utils.py`