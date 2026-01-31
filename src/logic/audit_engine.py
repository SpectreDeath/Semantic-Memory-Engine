import h5py
import numpy as np
from typing import List, Dict

class AuditEngine:
    def __init__(self, h5_path="data/knowledge_core.h5"):
        self.h5_path = h5_path

    def analyze_drift(self, claims: List[Dict]) -> Dict:
        """
        Compares claims against the HDF5 core.
        Claim format: {"subject": "FastMCP", "predicate": "is", "object": "plumbing"}
        """
        results = {"drift_score": 0.0, "anomalies": [], "verified": []}
        
        try:
            with h5py.File(self.h5_path, 'r') as f:
                # Access the relationship group directly via HDF5 pointers
                if 'relationships' in f:
                    rel_group = f['relationships']
                    
                    for claim in claims:
                        subj, obj = claim['subject'], claim['object']
                        # Check if this specific link exists in our local 'Common Sense' index
                        if subj in rel_group and obj in rel_group[subj]:
                            results["verified"].append(claim)
                        else:
                            results["anomalies"].append(claim)
                else:
                    results["anomalies"] = claims
        except FileNotFoundError:
            results["anomalies"] = claims
        except Exception as e:
            print(f"Error accessing HDF5: {e}")
            results["anomalies"] = claims
        
        # Calculate drift based on missing or contradictory links
        total = len(claims)
        if total > 0:
            results["drift_score"] = len(results["anomalies"]) / total
            
        return results
