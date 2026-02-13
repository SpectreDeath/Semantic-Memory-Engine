# Spec: Supabase MCP Integration

## 1. Objective
Automate the persistence of captured threat leads from the Python 3.13 Sidecar (Brain) to the Supabase backend using the MCP (Model Context Protocol) server.

## 2. Rationale
The "Poisoned Well" simulation requires that all alerts are logged for forensic integrity. By integrating the archiving directly into the 3.13 Sidecar, we ensure that AI-generated insights are persisted immediately even if the main 3.14 UI is focused on other tasks.

## 3. Requirements
- The `.brain_venv` must be able to communicate with the Supabase MCP server.
- Captured leads must include: timestamp, username, incident_type, and AI_verdict.
- All leads must be stored in the `threat_leads` table as per the SME Constitution.

## 4. Constraints
- Must NOT cause memory overhead exceeding the 1660 Ti VRAM limits.
- Must handle network failures gracefully with local retries or logging.
