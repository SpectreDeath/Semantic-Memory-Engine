import os
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger("LawnmowerMan.TacticalPack")

class TacticalForensicExtension:
    """
    Tactical Intelligence Pack for Lawnmower Man v1.1.1.
    Specialized for analyzing physical evidence patterns at critical sites.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus_api = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        self.threat_signatures = {
            "IED_Component": ["nitrate", "detonator", "timer", "circuit"],
            "CBRN_Precursor": ["hazardous", "chemical", "radiation", "biological"],
            "Tactical_Comms": ["encrypted", "radio", "frequency", "signal"]
        }

    async def on_startup(self):
        """
        Connect to tactical intelligence databases and cache threat signatures.
        """
        logger.info(f"[{self.plugin_id}] Tactical Enclave online. Threat signatures loaded.")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Automatically screens all harvested evidence for tactical threat signatures.
        """
        found_threats = []
        lower_data = raw_data.lower()
        
        for threat, signatures in self.threat_signatures.items():
            if any(sig in lower_data for sig in signatures):
                found_threats.append(threat)
        
        if found_threats:
            logger.warning(f"[{self.plugin_id}] TACTICAL ALERT: Found signatures {found_threats} in evidence.")
            return {
                "tactical_hits": found_threats,
                "priority": "HIGH",
                "risk_assessment": "Immediate review required by Explosive Ordnance Disposal (EOD)."
            }
        
        return {"status": "cleared", "tactical_hits": []}

    def get_tools(self) -> list:
        """
        Exposes tactical analysis tools to the Lawnmower Man Gateway.
        """
        return [self.analyze_site_evidence, self.classify_threat_level]

    async def analyze_site_evidence(self, site_path: str) -> str:
        """
        Analyzes physical evidence patterns at a target site.
        Description: Scans site documentation for tactical signatures and returns a TPM-signed site report.
        """
        if not os.path.exists(site_path):
            return json.dumps({"error": f"Site documentation not found at {site_path}"})
            
        # Simulate scanning files in the directory
        hits = []
        if os.path.isdir(site_path):
            for root, _, files in os.walk(site_path):
                for file in files:
                    if file.endswith(('.txt', '.md', '.log')):
                        with open(os.path.join(root, file), 'r', errors='ignore') as f:
                            content = f.read().lower()
                            for threat, signatures in self.threat_signatures.items():
                                if any(sig in content for sig in signatures):
                                    hits.append({"file": file, "threat": threat})

        report = {
            "timestamp": datetime.now().isoformat(),
            "site": os.path.abspath(site_path),
            "threat_hits": hits,
            "status": "DANGER" if hits else "CLEAR"
        }
        
        # Hardware signature via SmeCoreBridge (through the bridge's nexus access)
        # Note: In a real scenario, we'd ensure hsm is reachable through nexus_api
        from gateway.hardware_security import get_hsm
        hsm = get_hsm()
        data_hash = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        signature = hsm.sign_evidence(self.plugin_id, data_hash)
        
        report["hw_signature"] = signature
        return json.dumps(report, indent=2)

    async def classify_threat_level(self, detected_keywords: List[str]) -> str:
        """
        Classifies the threat level based on specific tactical keywords.
        """
        score = 0
        for kw in detected_keywords:
            kw_lower = kw.lower()
            if any(sig in kw_lower for sig in self.threat_signatures["IED_Component"]):
                score += 5
            if any(sig in kw_lower for sig in self.threat_signatures["CBRN_Precursor"]):
                score += 10
        
        level = "LOW"
        if score > 15: level = "CRITICAL"
        elif score > 8: level = "HIGH"
        elif score > 3: level = "MEDIUM"
        
        result = {
            "threat_score": score,
            "threat_level": level,
            "classification": "CONIDENTIAL // LAW ENFORCEMENT SENSITIVE"
        }
        return json.dumps(result, indent=2)

def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """
    Standard Lawnmower Man v1.1.1 Extension Hook.
    """
    return TacticalForensicExtension(manifest, nexus_api)
