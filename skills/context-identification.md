---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Utilities
name: context-identification
Source: Semantic Memory Engine (SME)
Source_File: src/utils/context_sniffer.py
---

## Purpose

Identifies project context and manages persona assignments based on file extension detection and keyword scanning.

## Description

The Context Sniffer analyzes file content and metadata to determine project context. It uses file extension patterns, keyword scanning, and persona mapping to identify the appropriate context for analysis.

## Workflow

1. **File Analysis**: Examine file characteristics
2. **Extension Detection**: Identify file type
3. **Keyword Scanning**: Search for indicators
4. **Persona Mapping**: Assign appropriate persona
5. **Context Output**: Return context identification

## Examples

### Example 1: Project Type Detection
**Input**: Code file
**Output**: Project type (e.g., web, data)
**Use Case**: Context-aware analysis

### Example 2: Persona Assignment
**Input**: File or project
**Output**: Recommended persona
**Use Case**: Specialized processing

## Implementation Notes

- **Optimization**: 68 lines, <2MB memory
- **Location**: `D:/SME/src/utils/context_sniffer.py`