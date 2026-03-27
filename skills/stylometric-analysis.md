---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Advanced
Type: Tool
Category: Forensic Analysis
name: stylometric-analysis
Source: Semantic Memory Engine (SME)
Source_File: src/scribe/stylo_wrapper.py
---

## Purpose

Analyzes writing style signatures to identify authorship, compare documents, and detect stylistic anomalies. Uses faststylometry for efficient writer profiling.

## Description

Stylometric Analysis extracts linguistic features from text to create authorship fingerprints. It analyzes vocabulary richness, sentence structure, function word usage, and punctuation patterns to build writer profiles that can be compared against reference corpora.

## Workflow

1. **Feature Extraction**: Compute linguistic features (word frequency, sentence length, etc.)
2. **Profile Generation**: Create writer fingerprint from features
3. **Reference Comparison**: Compare against known writer profiles (Miller Base)
4. **Manhattan Distance**: Calculate stylistic similarity score
5. **Anomaly Detection**: Identify unusual stylistic shifts
6. **Reporting**: Generate detailed stylometric report

## Examples

### Example 1: Authorship Attribution
**Input**: Anonymous document
**Output**: Matched author profile with confidence score
**Use Case**: Determining document provenance

### Example 2: Document Comparison
**Input**: Two documents to compare
**Output**: Similarity score with feature breakdown
**Use Case**: Verifying if documents share authorship

### Example 3: Style Anomaly Detection
**Input**: Document with suspected multiple authors
**Output**: Sections flagged for stylistic inconsistency
**Use Case**: Detecting ghostwriting or document tampering

## Implementation Notes

- **Libraries**: faststylometry for feature extraction
- **Distance Metric**: Manhattan distance for profile comparison
- **Reference Database**: Miller Base prints in laboratory.db
- **Node Limit**: 2,000 nodes for visualization (hardware constraint)

## See Also

- [SME v3.0.0 Operator Manual - Forensic Workflow](D:/SME/SME%20v3.0.0%20Operator%20Manual.md)
- [Performance Optimization Guide](D:/SME/docs/PERFORMANCE_OPTIMIZATION_GUIDE.md)

---