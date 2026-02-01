import random
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("lawnmower.red_team")

class AdversarialGenerator:
    """
    Generates 'stylometric spoofs' to test the Scribe Pro engine.
    Uses linguistic perturbation (synonym substitution, noise injection).
    """
    def __init__(self):
        # High-frequency formal words to substitute
        self.substitutions = {
            "moreover": ["furthermore", "additionally", "also"],
            "therefore": ["consequently", "thus", "so"],
            "however": ["nevertheless", "nonetheless", "but"],
            "consistent": ["uniform", "compatible", "steady"],
            "substantial": ["significant", "considerable", "large"],
            "administrative": ["management", "executive", "operational"]
        }

    def generate_mimicry(self, base_text: str, intensity: float = 0.5) -> str:
        """
        Perturbs a base text to create an adversarial sample.
        Intensity 0.0 (No change) to 1.0 (Heavy perturbation).
        """
        words = base_text.split()
        perturbed = []
        
        for word in words:
            clean_word = word.lower().strip(".,!?;:")
            if clean_word in self.substitutions and random.random() < intensity:
                sub = random.choice(self.substitutions[clean_word])
                # Preserve case and punctuation if possible (simple version)
                if word[0].isupper():
                    sub = sub.capitalize()
                perturbed.append(sub + word[len(clean_word):])
            else:
                perturbed.append(word)
                
        return " ".join(perturbed)

    def generate_noise(self, base_text: str, noise_ratio: float = 0.1) -> str:
        """Injects random 'junk' tokens to disrupt stylometric signatures."""
        words = base_text.split()
        num_noise = int(len(words) * noise_ratio)
        
        for _ in range(num_noise):
            pos = random.randint(0, len(words))
            words.insert(pos, "SYSTEM_ERR_TOKEN")
            
        return " ".join(words)

class ThresholdTuner:
    """
    Automates the process of finding the 'Break-Even' probability 
    threshold for forensic verification.
    """
    def __init__(self, analyze_fn: Any):
        self.analyze_fn = analyze_fn

    def tune_threshold(self, baseline_text: str, adversary_samples: List[str], **kwargs) -> float:
        """
        Analyzes a set of adversarial samples and returns the average 
        'Attack Success' probability.
        """
        probs = []
        for sample in adversary_samples:
            try:
                # Use the analyze_authorship_pro core logic
                # It expects AuthorshipProRequest or dict
                res = self.analyze_fn({"text": sample}, **kwargs)
                if isinstance(res, str):
                    res = json.loads(res)
                
                # Get max probability (how much it fooled the system)
                if "probabilities" in res:
                    max_prob = max(res["probabilities"].values(), default=0.0)
                    probs.append(float(max_prob))
            except Exception as e:
                logger.error(f"Tuning error: {e}")
        
        if not probs:
            return 0.8 # Default baseline
            
        avg_attack_prob = sum(probs) / len(probs)
        # We recommend a threshold 10% higher than the average attack success
        recommended_threshold = min(avg_attack_prob + 0.1, 0.95)
        return round(recommended_threshold, 3)

def run_stress_test(mcp_tools: Dict[str, Any], session_id: str):
    """
    Automated Red-Team cycle.
    """
    gen = AdversarialGenerator()
    tuner = ThresholdTuner(mcp_tools["analyze_authorship_pro"])
    
    # 1. Load Baseline (simulated from a previous turn's text or common formal patterns)
    baseline = "The suspect was observed accessing the primary mainframe using an administrative token. Moreover, the audit logs are consistent with previous patterns."
    
    # 2. Generate Attacks
    attacks = [gen.generate_mimicry(baseline, intensity=i/10.0) for i in range(1, 11)]
    
    # 3. Tune
    recommended = tuner.tune_threshold(baseline, attacks)
    
    return {
        "recommended_cq_threshold": recommended,
        "attack_samples_count": len(attacks),
        "status": "Calibration Complete"
    }
