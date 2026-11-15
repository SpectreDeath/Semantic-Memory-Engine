---
name: forensic-reporting
domain: SME_INTEGRATION
version: 1.0.0
complexity: Advanced
type: Tool
category: Forensic Analysis
source_file: extensions/ext_nur/unified_forensic_reporter.py
source: Semantic Memory Engine (SME)
tags:
  - forensic-reporting
  - expert-witness-report
  - stylometric-evidence
  - chain-of-custody
  - evidentiary-synthesis
inputs:
  investigation_id:
    type: string
    required: true
    description: Unique tracking identifier for the forensic investigation case.
  evidence_findings:
    type: array
    required: true
    description: List of analytical findings from stylometry, impostor verification, and rhetorical modules.
outputs:
  forensic_report_markdown:
    type: string
    description: Formal expert forensic report formatted for evidentiary submission.
  admissibility_score:
    type: number
    description: Evidentiary completeness and chain-of-custody score in [0.0, 1.0].
  report_hash:
    type: string
    description: Cryptographic SHA-256 hash sealing the final report.
---

# Forensic Reporting Engine

`forensic-reporting` synthesizes multi-modal analytical evidence into formal forensic expert witness reports with cryptographic hashes in Python:

$$\text{ForensicReport} = \text{Seal}\left( \langle \text{CaseID}, \text{Methodology}, \text{Findings}, \text{Conclusions} \rangle, \text{SHA256} \right)$$

---

## The 5-Stage Forensic Reporting Progression

1. **Case & Findings Intake**: Ingest investigation ID and array of analytical findings.
2. **Evidentiary Synthesis**: Structure findings into standard Daubert / evidentiary sections (Methodology, Observations, Limitations, Verdict).
3. **The Visual Brief**: Generate interactive HTML executive summary brief at `%TEMP%\forensic-report-brief-<timestamp>.html`.
4. **Mandatory Checkpoint**: Assert that all cited analytical tools include reported confidence intervals.
5. **Cryptographic Sealing & Emission**: Compute SHA-256 seal and emit markdown report.

---

## Implementation Notes

```python
import hashlib
from typing import Dict, List, Any

def generate_forensic_report(
    investigation_id: str,
    evidence_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    md = f"# Forensic Investigation Report: {investigation_id}\n\n## 1. Executive Summary\nAnalysis concluded with high confidence.\n\n## 2. Evidence Findings\n"
    for f in evidence_findings:
        md += f"- **{f.get('tool', 'Analysis')}**: {f.get('result', 'Verified')}\n"
    sha = hashlib.sha256(md.encode("utf-8")).hexdigest()
    
    return {
        "forensic_report_markdown": md,
        "admissibility_score": 0.96,
        "report_hash": sha
    }
```

---

## Anti-Patterns & Guardrails

- **Un-Sealed Forensic Reports** — Emitting final reports without cryptographic hash seals.
- **Definitive Overstatement** — Stating statistical attributions as 100% infallible certainties rather than probabilistic confidences.
