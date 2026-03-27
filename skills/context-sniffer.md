---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Utilities
name: context-sniffer
Source: Semantic Memory Engine (SME)
Source_File: src/utils/context_sniffer.py
---

## Purpose

Identifies project context and determines appropriate processing persona based on file analysis.

## Description

The Context Sniffer is a lightweight utility for determining project context from file analysis. It identifies the domain, type, and appropriate persona for processing files based on extension patterns and content keywords.

## Workflow

1. **File Input**: Receive file path or content
2. **Pattern Matching**: Analyze file characteristics
3. **Context Determination**: Identify project type
4. **Persona Selection**: Recommend processing approach

## Examples

### Example 1: Project Type Detection
**Input**: File path
**Output**: Project context
**Use Case**: Automated configuration

## Implementation Notes

- **Size**: 68 lines
- **Memory**: <2MB
- **Location**: `D:/SME/src/utils/context_sniffer.py`