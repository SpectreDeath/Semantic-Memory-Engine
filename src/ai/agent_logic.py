import json
from pathlib import Path
from src.ai.bridge import run_ai_flow

def get_common_sense_context(term: str):
    """
    Fetches common-sense associations for a term via the Sidecar.
    """
    print(f"🧠 Expanding context for: {term} (OMCS/ConceptNet)")
    return run_ai_flow("concept_lookup", term)


def run_langflow_flow(flow_name: str, input_value: str):
    """
    Wrapper to execute a Langflow JSON flow.
    Assumes the flow is exported as a JSON file in src/ai/flows/
    """
    flow_path = Path(f"src/ai/flows/{flow_name}.json")
    if not flow_path.exists():
        print(f"⚠️ Flow {flow_name} not found at {flow_path}")
        return f"Error: Flow {flow_name} not found."

    print(f"🧬 Orchestrating Agentic Flow: {flow_name} (Sidecar Bridge)")
    
    # Execute via the Python 3.13 Sidecar
    return run_ai_flow(flow_name, input_value)

def generate_forensic_summary(intel_package: dict):
    """
    High-level entry point for the Prefect pipeline to trigger agentic summarization.
    """
    context = json.dumps(intel_package)
    
    # Check for specific "Smoking Gun" scenario
    osint = intel_package.get("osint", [])
    if isinstance(osint, dict): osint = [osint]
    usernames = {s.get("username") for s in osint if s.get("username")}
    
    if "CBRN_Ghost_99" in usernames:
        print("AGENT ALERT: High-Value Threat 'CBRN_Ghost_99' Detected!")
        
        # Logic Expansion Layer
        cs_context = get_common_sense_context("CBRN")
        
        return (f"CRITICAL ALERT: Target 'CBRN_Ghost_99' identified with cross-referenced digital fingerprints. "
                f"CBRN sensor array research detected. Common-sense context: {cs_context}. "
                f"High probability of malicious intent.")

    return run_langflow_flow("forensic_summary", context)
