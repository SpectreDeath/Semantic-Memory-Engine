---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Advanced
Type: Tool
Category: AI Detection
name: synthetic-source-detection
Source: Semantic Memory Engine (SME)
Source_File: extensions/ext_synthetic_source_auditor/
---

## Purpose

Detects machine-generated text patterns using SimHash near-duplicate detection and burstiness analysis to identify synthetic content sources.

## Description

The Synthetic Source Auditor identifies text that exhibits characteristics of AI generation. It uses SimHash for near-duplicate detection against known AI-generated text databases, analyzes burstiness patterns for homogenized writing, and flags sources with high probability of being synthetic.

## Workflow

1. **SimHash Generation**: Create SimHash fingerprints of input text
2. **Database Comparison**: Check against known AI-generated signatures
3. **Burstiness Analysis**: Detect unnaturally uniform writing patterns
4. **Source Attribution**: Identify likely AI model or generation method
5. **Confidence Scoring**: Calculate synthetic probability score
6. **Reporting**: Generate detailed detection report

## Examples

### Example 1: Content Source Verification
**Input**: Article or document
**Output**: Synthetic probability with detection method breakdown
**Use Case**: Verifying content originality

### Example 2: Batch Source Screening
**Input**: Collection of documents
**Output**: Ranked list by synthetic probability
**Use Case**: Content moderation at scale

### Example 3: AI Model Identification
**Input**: Suspected AI-generated text
**Output**: Likely generation model or platform
**Use Case**: Attribution and provenance tracking

## Implementation Notes

- **Detection Methods**: SimHash, Burstiness, Perplexity variance
- **Database**: Known AI-generated text signatures
- **Extension**: Synthetic Source Auditor
- **Location**: `D:/SME/extensions/ext_synthetic_source_auditor/`

## See Also

- [Adversarial Pattern Detection](SKILL.adversarial-pattern-detection/)
- [Extensions Catalog](D:/SME/docs/EXTENSIONS_CATALOG.md)
