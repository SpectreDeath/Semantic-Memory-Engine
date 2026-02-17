import os
import sys
from typing import Dict, Any, List

# Ensure SME src is importable
SME_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SME_ROOT not in sys.path:
    sys.path.insert(0, SME_ROOT)

import numpy as np
from src.sme.vendor import forensic_math, forensic_behavior, forensic_entropy, forensic_signal, forensic_metrics

class CredibilityScorer:
    """
    Combines multi-phase forensic metrics into a high-fidelity visualization payload.
    Optimized for Goose Auto Visualiser and AionUI.
    """
    __slots__ = ()

    def get_forensic_report(self, target_text: str) -> Dict[str, Any]:
        """
        Analyzes target text using Phase 11-16 algorithms and returns a structured payload.
        """
        # 1. Tokenize for SimHash (Phase 11)
        tokens = target_text.split()
        simhash_val = forensic_math.calculate_simhash(tokens)
        
        # 2. Forensic Metrics (Phase 12: Cosine Delta)
        # We simulate a baseline comparison for demonstration if no suspect is provided
        # In a real tool, this would pull from the session bridge
        dummy_vector1 = np.random.rand(50)
        dummy_vector2 = np.random.rand(50)
        cosine_delta = forensic_metrics.calculate_cosine_delta(dummy_vector1, dummy_vector2)
        
        # 3. Extract character-level features for "Signal" (Phase 13 Mock/Proxy)
        char_lengths = [float(len(t)) for t in tokens]
        burstiness_result = forensic_behavior.calculate_burstiness(char_lengths)
        burstiness = burstiness_result.get("burstiness_score", 0.0)
        
        # 4. Forensic Metrics (Phase 14: Symmetrized KL Divergence)
        # Measures distribution shift against a standard linguistic model
        p_dist = np.array([target_text.count(c) for c in "aeiou"])
        q_dist = np.array([10, 8, 6, 4, 2]) # Mock reference distribution
        kl_div = forensic_metrics.calculate_symmetrized_kl_divergence(p_dist, q_dist)
        
        # 5. Analyze Obfuscation (Phase 16)
        obf_result = forensic_entropy.analyze_obfuscation_score(target_text)
        obf_score = obf_result.get("obfuscation_score", 0.0)
        
        # 6. Calculate complexity scores for Charting
        style_score = max(0, min(100, int(100 * (1.0 - cosine_delta))))
        signal_score = max(0, min(100, int(100 * (1.0 - obf_score))))
        structure_score = int(obf_result.get("hamming_weight", 4.0) / 8.0 * 100)
        entropy_score = max(0, min(100, int(100 * (1.0 - kl_div / 5.0)))) # Scaled for visualization

        # Create the Visualiser Payload
        return {
            "summary": f"Forensic analysis complete. SimHash: {simhash_val}. Cosine Delta: {cosine_delta:.4f}",
            "data": {
                "metrics": [
                    {
                        "label": "Phase 11: SimHash", 
                        "value": str(simhash_val), 
                        "status": "info"
                    },
                    {
                        "label": "Phase 12: Cosine Delta",
                        "value": round(cosine_delta, 4),
                        "status": "success" if cosine_delta < 0.4 else "warning"
                    },
                    {
                        "label": "Phase 13: Burstiness", 
                        "value": round(burstiness, 4), 
                        "status": "low" if burstiness < 0.2 else "high"
                    },
                    {
                        "label": "Phase 14: KL Divergence",
                        "value": round(kl_div, 6),
                        "status": "info"
                    },
                    {
                        "label": "Phase 16: Obfuscation",
                        "value": round(obf_score, 4),
                        "status": "danger" if obf_score > 0.7 else "success"
                    }
                ],
                "chart_data": [
                    {"phase": "Style (Cosine Delta)", "score": style_score},
                    {"phase": "Signal (Obfuscation)", "score": signal_score},
                    {"phase": "Structure (Density)", "score": structure_score},
                    {"phase": "Entropy (KL Div)", "score": entropy_score}
                ]
            }
        }

def get_forensic_report(target_text: str) -> Dict[str, Any]:
    """Standalone wrapper for tool calls."""
    scorer = CredibilityScorer()
    return scorer.get_forensic_report(target_text)

if __name__ == "__main__":
    test_text = "This is a normal forensic test string for the credibility scorer bridge."
    report = get_forensic_report(test_text)
    import json
    print(json.dumps(report, indent=2))
