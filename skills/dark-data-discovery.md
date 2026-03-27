---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Advanced
Type: Tool
Category: Knowledge Management
name: dark-data-discovery
Source: Semantic Memory Engine (SME)
Source_File: extensions/ext_nur/
---

## Purpose

Illuminates dark data and knowledge gaps by identifying unaddressed questions, missing context, and unexplored areas within the knowledge graph.

## Description

The Nur (Light) extension discovers areas of uncertainty and knowledge gaps in the SME system. It identifies questions without answers, claims without evidence, and topics without sufficient coverage, providing a roadmap for knowledge acquisition.

## Workflow

1. **Question Mining**: Extract unanswered questions from the corpus
2. **Claim Extraction**: Identify unverified or unsupported claims
3. **Coverage Analysis**: Measure topic completeness
4. **Gap Prioritization**: Rank gaps by importance and feasibility
5. **Investigation Suggestions**: Recommend investigation paths
6. **Reporting**: Comprehensive gap analysis with recommendations

## Examples

### Example 1: Knowledge Completeness Audit
**Input**: Knowledge collection
**Output**: Areas lacking sufficient information
**Use Case**: Research gap analysis

### Example 2: Claim Verification
**Input**: Statements requiring verification
**Output**: Unsupported claims needing evidence
**Use Case**: Fact-checking workflow

### Example 3: Investigation Prioritization
**Input**: Research domain
**Output**: Prioritized list of areas to investigate
**Use Case**: Research planning

## Implementation Notes

- **Status**: Beta (🟡)
- **Methods**: Question detection, claim analysis, coverage metrics
- **Extension**: Nur
- **Location**: `D:/SME/extensions/ext_nur/`

## See Also

- [Atlas - Knowledge Mapping](SKILL.knowledge-domain-mapping/)
- [Extensions Catalog](D:/SME/docs/EXTENSIONS_CATALOG.md)
