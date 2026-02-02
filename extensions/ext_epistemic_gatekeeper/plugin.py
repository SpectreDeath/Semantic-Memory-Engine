import os
import json
import logging
from typing import Dict, Any, List

# Import shared trust logic
from gateway.gatekeeper_logic import calculate_trust_score, calculate_entropy, calculate_burstiness

logger = logging.getLogger("LawnmowerMan.Gatekeeper")

class EpistemicGatekeeper:
    """
    Epistemic Gatekeeper Extension (v1.2.0).
    Provides volume-based trust auditing (Heat Maps) and governance.
    """
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api
        self.plugin_id = manifest.get("plugin_id")

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Gatekeeper Online. Trust algorithms active.")

    def get_tools(self) -> list:
        return [self.audit_folder_veracity]

    async def audit_folder_veracity(self, folder_path: str) -> str:
        """
        Recursively audits a folder, generating a Heat Map of Trust Scores (NTS).
        Returns a JSON report classifying files as Human, Synthetic, or Mixed.
        """
        if not os.path.exists(folder_path):
            return json.dumps({"error": f"Path not found: {folder_path}"})
            
        file_stats = []
        total_files = 0
        synthetic_count = 0
        human_count = 0
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.txt', '.md', '.log', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if len(content) < 50:
                            continue
                            
                        # Calculate Metrics
                        entropy = calculate_entropy(content)
                        burstiness = calculate_burstiness(content)
                        trust_data = calculate_trust_score(entropy, burstiness)
                        
                        nts = trust_data["nts"]
                        verdict = trust_data["label"]
                        
                        if nts < 40:
                            synthetic_count += 1
                        elif nts > 80:
                            human_count += 1
                            
                        file_stats.append({
                            "file": file,
                            "path": file_path,
                            "entropy": entropy,
                            "burstiness": burstiness,
                            "nts": nts,
                            "verdict": verdict
                        })
                        total_files += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to audit {file}: {e}")

        # Generate Heat Map Summary
        heat_map = {
            "target": folder_path,
            "total_scanned": total_files,
            "summary": {
                "grounded_human": human_count,
                "synthetic_hazard": synthetic_count,
                "uncertain": total_files - (human_count + synthetic_count)
            },
            "trust_ratio": round(human_count / total_files, 2) if total_files > 0 else 0,
            "detailed_map": sorted(file_stats, key=lambda x: x['nts']) # Sort by NTS (ascending - synthetic first)
        }
        
        return json.dumps(heat_map, indent=2)

def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    return EpistemicGatekeeper(manifest, nexus_api)
