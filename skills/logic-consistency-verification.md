---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Advanced
Type: Tool
Category: Analysis
name: logic-consistency-verification
Source: Semantic Memory Engine (SME)
Source_File: extensions/ext_logic_auditor/
---

## Purpose

Verifies logical consistency of forensic findings and detects contradictions, logical fallacies, and reasoning errors in analysis outputs.

## Description

The Logic Auditor examines forensic findings for internal consistency and logical soundness. It identifies contradictions between conclusions, detects common logical fallacies, and verifies that evidence properly supports stated conclusions.

## Workflow

1. **Finding Extraction**: Parse forensic findings into logical propositions
2. **Consistency Analysis**: Check for internal contradictions
3. **Fallacy Detection**: Identify logical fallacies (straw man, ad hominem, etc.)
4. **Evidence Mapping**: Verify evidence-to-conclusion relationships
5. **Confidence Scoring**: Assess overall reliability of findings
6. **Report Generation**: Document inconsistencies and recommendations

## Examples

### Example 1: Finding Consistency Check
**Input**: Set of forensic findings
**Output**: Consistency report with any contradictions flagged
**Use Case**: Validating analysis before reporting

### Example 2: Fallacy Detection
**Input**: Argument or conclusion text
**Output**: Identified fallacies with locations and explanations
**Use Case**: Critical analysis of arguments

### Example 3: Evidence Support Verification
**Input**: Conclusion with supporting evidence
**Output**: Support strength rating with gaps identified
**Use Case**: Verifying reasoning validity

## Implementation Notes

- **Analysis Type**: Propositional logic and informal fallacy detection
- **Integration**: Works with all SME forensic tools
- **Extension**: Logic Auditor
- **Location**: `D:/SME/extensions/ext_logic_auditor/`

## Capabilities

- Contradiction detection
- Logical fallacy identification
- Evidence-support mapping
- Confidence scoring

## See Also

- [Extensions Catalog](D:/SME/docs/EXTENSIONS_CATALOG.md)

---