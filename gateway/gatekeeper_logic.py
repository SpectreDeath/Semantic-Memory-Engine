import math
import statistics
import re
from collections import Counter
from typing import Dict, Any

def calculate_entropy(data: str) -> float:
    """Compute Shannon Entropy in bits per symbol."""
    if not data:
        return 0.0
    counter = Counter(data)
    length = len(data)
    entropy = 0.0
    for count in counter.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def calculate_burstiness(text: str) -> float:
    """Calculate Burstiness: Standard Deviation of sentence lengths (in words)."""
    if not text:
        return 0.0
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 2:
        return 0.0
    # Count words per sentence
    lengths = [len(s.split()) for s in sentences]
    if len(lengths) < 2:
        return 0.0
    try:
        return statistics.stdev(lengths)
    except Exception:
        return 0.0

def calculate_trust_score(entropy: float, burstiness: float) -> Dict[str, Any]:
    """
    Calculates the Normalized Trust Score (NTS) based on Entropy and Burstiness.
    
    Target Logic:
    - High Entropy (~5.0) + High Burstiness = Human (Score > 80)
    - Low Entropy (<4.0) + Low Burstiness = Synthetic (Score < 40)
    
    Formula (Experimental v1.2):
    - Entropy contribution: 60%
    - Burstiness contribution: 40%
    """
    
    # 1. Normalize Entropy (Base: 3.5 bits, Cap: 5.5 bits)
    # Range of interest: 3.5 to 5.0
    entropy_clamped = max(3.5, min(entropy, 5.5))
    entropy_score = ((entropy_clamped - 3.5) / 2.0) * 100
    
    # 2. Normalize Burstiness (Std Dev of sent lengths)
    # Human text often has std_dev > 5.0 chars (or words)
    # AI often has std_dev < 3.0
    # Let's assume burstiness is passed as std_dev of sentence lengths (in words)
    burst_clamped = max(0, min(burstiness, 10.0))
    burst_score = (burst_clamped / 10.0) * 100
    
    # Weighted Mix
    raw_nts = (0.6 * entropy_score) + (0.4 * burst_score)
    nts = round(max(0, min(raw_nts, 100)), 1)
    
    if nts < 40:
        label = "Synthetic Hazard"
        signal = "WARNING: SYNTHETIC SIGNAL DETECTED"
    elif nts > 80:
        label = "Grounded Human Content"
        signal = "VERIFIED: HUMAN AUTHORSHIP"
    else:
        label = "Indeterminate"
        signal = "CAUTION: MIXED SIGNALS"
        
    return {
        "nts": nts,
        "label": label,
        "signal": signal,
        "components": {
            "entropy_score": round(entropy_score, 1),
            "burstiness_score": round(burst_score, 1)
        }
    }
