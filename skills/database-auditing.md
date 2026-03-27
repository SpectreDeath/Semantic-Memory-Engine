---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Utilities
name: database-auditing
Source: Semantic Memory Engine (SME)
Source_File: src/utils/check_db.py
---

## Purpose

Performs database health checks, schema validation, and integrity verification for SME databases.

## Description

The Database Auditing utility checks database health, validates schemas, verifies data integrity, and identifies issues in SME database systems.

## Workflow

1. **Connection Test**: Verify database access
2. **Schema Validation**: Check structure
3. **Integrity Check**: Verify data consistency
4. **Health Metrics**: Gather health statistics
5. **Reporting**: Document findings

## Examples

### Example 1: Health Check
**Input**: Database reference
**Output**: Health status
**Use Case**: Routine monitoring

### Example 2: Schema Validation
**Input**: Database
**Output**: Schema issues found
**Use Case**: Migration verification

## Implementation Notes

- **Databases**: PostgreSQL, SQLite
- **Location**: `D:/SME/src/utils/check_db.py`