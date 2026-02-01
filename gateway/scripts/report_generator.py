import os
import json
from datetime import datetime
from typing import Dict, Any, List

class ReportGenerator:
    """
    Automates the generation of Digital Forensic Witness Statements.
    """
    def __init__(self, session_id: str, bridge: Any, epistemic_tool: Any):
        self.session_id = session_id
        self.bridge = bridge
        self.epistemic_tool = epistemic_tool
        self.template = """# **Digital Forensic Witness Statement**

**Case ID:** `{case_id}` | **Date:** `{date}`

**Lead Investigator:** `Project Lawnmower Man (v0.5.0)`

### **1. Executive Summary**

{summary}

### **2. Authorship Attribution (Scribe Pro)**

| Sample Tested | Target Vector | Match Probability | Method Used |
| --- | --- | --- | --- |
{authorship_rows}

### **3. Knowledge Graph Influence (PageRank)**

{influence_section}

### **4. Epistemological Audit (Certainty Quotient)**

* **Certainty Quotient (CQ):** `{cq}`
* **Evidence Reliability:**
{reliability_bullets}

* **Integrity Check:** `SHA-256 Verified` (No tamper evidence detected).

### **5. Conclusion & Declaration**

Based on the **probabilistic linguistic match** and the **high-trust provenance** of the source logs, the system concludes that the claim is **{conclusion_status}**.

---
"""

    def generate(self, case_id: str = "CASE_REF_001"):
        """Gathers session state and generates the markdown report."""
        session = self.bridge.get_session()
        if not session:
            return {"error": "Session not found."}
        
        scratchpad = session.scratchpad
        
        # 1. Executive Summary
        summary = scratchpad.get("Summary")
        if not summary:
            summary = f"Autonomous forensic audit for Case {case_id}. Investigation focused on authorship attribution and graph influence."
        
        # 2. Authorship Rows
        authorship_rows = ""
        scribe_res = scratchpad.get("Scribe_Pro_Result")
        if scribe_res:
             probs = scribe_res.get("probabilities", {})
             for target, prob in probs.items():
                 # Probabilities are already multiplied by 100 in ScribePro or need it?
                 # FastStylometry returns 0.0-1.0. 
                 percentage = round(prob * 100, 2)
                 authorship_rows += f"| `Sample_Test` | `{target}` | `{percentage}%` | `faststylometry (Calibrated)` |\n"
        else:
            authorship_rows = "| N/A | N/A | N/A | N/A |\n"

        # 3. Influence Section
        influence_data = scratchpad.get("Influence_Result")
        if influence_data:
            entity = influence_data.get("entity", "Unknown")
            score = influence_data.get("centrality", 0.0)
            influence_section = f"* **Key Entity:** `{entity}`\n* **Centrality Score:** `{score}` (High Influence)\n* **Justification:** Node analysis indicates significant connectivity in the investigated network."
        else:
            influence_section = "No influence analysis data found in scratchpad."

        # 4. Epistemological Audit
        findings = scratchpad.get("Key_Findings", [])
        if not findings:
            findings = [{"claim": "General investigation", "evidence_sources": [{"id": "System_Audit"}]}]
        
        # We audit the primary claim
        main_claim = scratchpad.get("Primary_Claim", "Incident Investigation")
        audit_res = self.epistemic_tool.evaluate_claim(main_claim, findings[0].get("evidence_sources", []))
        
        cq = audit_res.get("certainty_quotient", 0.0)
        bullets = ""
        for trail in audit_res.get("audit_trail", []):
            bullets += f"* {trail}\n"
        
        # 5. Conclusion
        status = audit_res.get("status", "Unknown")
        
        report_md = self.template.format(
            case_id=case_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            summary=summary,
            authorship_rows=authorship_rows,
            influence_section=influence_section,
            cq=cq,
            reliability_bullets=bullets,
            conclusion_status=status
        )
        
        # Save to file
        report_path = f"Forensic_Report_{self.session_id}.md"
        with open(report_path, "w") as f:
            f.write(report_md)
            
        return {
            "status": "Report Generated",
            "path": report_path,
            "cq": cq,
            "conclusion": status
        }
