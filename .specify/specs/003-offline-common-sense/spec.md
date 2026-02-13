# Spec: Offline ConceptNet Caching System

## 1. Objective

Develop a local caching layer for the ConceptNet common-sense engine to ensure stability during API downtime, reduce network overhead, and support offline forensic analysis.

## 2. Environment Compliance

- **Runtime**: Python 3.13 (Sidecar).
- **Justification**: This system handles common-sense reasoning data, which is centralized in the AI Sidecar to maintain separation from the Python 3.14 Main environment.

## 3. Hardware Guardrails (GTX 1660 Ti)

- **Database Engine**: SQLite.
- **Concurrency**: Enable **Write-Ahead Logging (WAL)** mode for fast, non-blocking asynchronous reads.
- **Storage Limit**: The database size must not exceed **500MB**.
- **Rule**: Implement a purge mechanism (LRU - Least Recently Used) if the database exceeds the storage limit.

## 4. Functional Requirements

- **Cache Persistence**: Store ConceptNet relations (`RelatedTo`, `UsedFor`, `HasContext`, `IsA`) locally.
- **Forensic Weighting**: Store the `weight` attribute for each relation to allow the agent to prioritize high-confidence links.
- **Lookup Logic**:
  1. Check `conceptnet_cache.db`.
  2. If found, return cached results (Cache Hit).
  3. If not found, query ConceptNet Web API (Cache Miss).
  4. Store new results in SQLite with weights.

## 5. Schema Design

- **Table**: `concepts`
  - `id`: INTEGER PRIMARY KEY
  - `term`: TEXT (Indexed, unique)
  - `data`: JSON (Stored relations, weights, and metadata)
  - `last_accessed`: TIMESTAMP (For LRU purging)
