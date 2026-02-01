import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("lawnmower.planner")

class ForensicPlanner:
    """
    Orchestrates multi-step forensic investigations autonomously.
    """
    def __init__(self, mcp_tools: Dict[str, Any], session_manager: Any):
        self.tools = mcp_tools
        self.session_manager = session_manager

    def run_investigation(self, text: str, case_id: str, session_id: str) -> Dict[str, Any]:
        """
        Executes a standard investigative battery:
        1. Scribe Pro (Authorship)
        2. Influence (Centrality)
        3. Epistemic (Audit)
        4. Witness Statement (Reporting)
        """
        results = {"case_id": case_id, "steps": []}
        session = self.session_manager.get_session(session_id)
        
        # Step 1: Authorship Attribution
        logger.info(f"[{case_id}] Step 1: Scribe Pro Analysis")
        scribe_req = {"text": text, "comparison_id": "Suspect_Alpha_Vector"}
        scribe_res = json.loads(self.tools["analyze_authorship_pro"](scribe_req, session_id=session_id))
        
        session.update_scratchpad("Scribe_Pro_Result", scribe_res)
        results["steps"].append({"name": "Authorship", "result": scribe_res})
        
        # Step 2: Entity Influence (if entities found)
        # We'll extract entity from deep_analyze or similar if possible, 
        # or just use a baseline for the automated flow
        logger.info(f"[{case_id}] Step 2: Influence Analysis")
        # For the autonomous flow, we use a default hub entity related to the audit if not specified
        influence_req = {"entity_name": "Administrative_Token_42"}
        influence_res = json.loads(self.tools["get_influence_score"](influence_req, session_id=session_id))
        
        session.update_scratchpad("Influence_Result", influence_res)
        results["steps"].append({"name": "Influence", "result": influence_res})
        
        # Step 3: Epistemic Audit
        logger.info(f"[{case_id}] Step 3: Epistemic Audit")
        primary_claim = f"Authorship match for Case {case_id} indicates {scribe_res.get('status')} match."
        session.update_scratchpad("Primary_Claim", primary_claim)
        
        audit_req = {
            "claim": primary_claim,
            "evidence_sources": [{"id": "Evidence_Secure_Log"}] # Standard high-trust anchor
        }
        # In a real flow, we'd dynamically assign evidence sources
        audit_res = json.loads(self.tools["justify_claim"](audit_req, session_id=session_id))
        
        # Store the audited result, but ensure it includes the sources for the report generator
        audit_res["evidence_sources"] = audit_req["evidence_sources"]
        session.update_scratchpad("Key_Findings", [audit_res])
        results["steps"].append({"name": "Epistemic", "result": audit_res})
        
        # Step 4: Generate Witness Statement
        logger.info(f"[{case_id}] Step 4: Witness Statement Generation")
        report_req = {"case_id": case_id}
        report_res = json.loads(self.tools["generate_witness_statement"](report_req, session_id=session_id))
        
        results["final_report"] = report_res
        
        return results
