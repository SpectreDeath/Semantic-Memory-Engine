---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Advanced
Type: Tool
Category: Diagnostics
name: cognitive-mirror-test
Source: Semantic Memory Engine (SME)
Source_File: extensions/ext_mirror_test/
---

## Purpose

Performs self-reflective diagnostics for agent cognition, testing reasoning consistency, decision transparency, and cognitive blind spots.

## Description

The Mirror Test provides introspective analysis of AI agent reasoning. It tests whether agents can consistently explain their decisions, identifies cognitive biases and blind spots, and verifies reasoning chain validity through self-examination.

## Workflow

1. **Reasoning Extraction**: Extract decision rationale from agent
2. **Consistency Testing**: Verify reasoning across similar cases
3. **Transparency Analysis**: Assess explanation clarity and completeness
4. **Bias Detection**: Identify cognitive biases in reasoning
5. **Blind Spot Identification**: Find gaps in self-awareness
6. **Confidence Calibration**: Check prediction confidence accuracy
7. **Report Generation**: Cognitive health assessment

## Examples

### Example 1: Reasoning Consistency Check
**Input**: Agent decision history
**Output**: Consistency score across decisions
**Use Case**: Quality assurance

### Example 2: Explanation Quality Assessment
**Input**: Agent explanations for decisions
**Output**: Transparency score with improvements
**Use Case**: Trust verification

### Example 3: Bias Detection
**Input**: Decision patterns
**Output**: Identified cognitive biases
**Use Case**: Fairness audit

## Implementation Notes

- **Status**: Beta (🟡)
- **Tests**: Consistency, transparency, bias, confidence
- **Extension**: Mirror Test
- **Location**: `D:/SME/extensions/ext_mirror_test/`

## See Also

- [Logic Consistency Verification](SKILL.logic-consistency-verification/)
- [System Health Scan](SKILL.system-health-scan/)
- [Extensions Catalog](D:/SME/docs/EXTENSIONS_CATALOG.md)
