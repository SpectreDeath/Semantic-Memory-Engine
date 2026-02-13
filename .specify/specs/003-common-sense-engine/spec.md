# Spec: OMCS Common Sense Engine Integration

## 1. Objective
Integrate the Open Mind Common Sense (OMCS) knowledge base via ConceptNet to provide "Digital Intuition" to the Semantic Memory Engine. This enables the agent to understand the intent and common-sense context of forensic entities (e.g., knowing that "CBRN" relates to toxins and "sensors" detect danger).

## 2. Environment Compliance
- **Runtime**: Python 3.13 (Sidecar).
- **Justification**: The ConceptNet lookup tool and the associated Langflow logic reside in the Sidecar to leverage the existing Langflow ecosystem and avoid polluting the Python 3.14 Main environment.

## 3. Hardware Guardrails (GTX 1660 Ti)
- **Constraint**: Preserve VRAM for the primary LLM.
- **Rule**: Do not use local embedding-based common sense models that require significant VRAM.
- **Implementation**: Use the ConceptNet Web API (`http://api.conceptnet.io/`) for lookups. Fallback to a local SQLite cache if offline capabilities are required in the future.

## 4. Functional Requirements
- **ConceptNet Lookup Tool**: A new tool in the Langflow agent that:
    - Takes an entity term as input.
    - Queries ConceptNet for `RelatedTo`, `UsedFor`, or `HasContext` relations.
    - Returns a summary of common-sense associations.
- **Logic Expansion Loop**:
    1. Agent identifies an "Entity" (e.g., "CBRN sensor").
    2. Agent invokes `ConceptNet Lookup` for "CBRN" and "sensor".
    3. ConceptNet returns associations: "toxins", "danger", "detection", "security".
    4. Agent broadens search parameters in the Main engine using these new terms.

## 5. Tool Integration
- **Platform**: Langflow (Python 3.13 Sidecar).
- **Component**: Custom Python Component or specialized LangChain tool.
- **Workflow**:
    1. Input: Entity string.
    2. Process: HTTP request to ConceptNet API.
    3. Output: JSON or string summary of associations.
