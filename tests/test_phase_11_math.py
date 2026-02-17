import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_math

def test_advanced_math():
    print("[*] Testing Advanced Similarity & Entropy algorithms...")
    
    # 1. SimHash (Near-duplicates)
    doc1 = {"the": 1.0, "quick": 1.0, "brown": 1.0, "fox": 1.0}
    doc2 = {"the": 1.0, "quick": 1.0, "brown": 1.0, "dog": 1.0}
    
    sh1 = forensic_math.calculate_simhash(doc1)
    sh2 = forensic_math.calculate_simhash(doc2)
    
    similarity = forensic_math.calculate_simhash_similarity(sh1, sh2)
    print(f"[+] SimHash Similarity: {similarity:.4f}")
    assert similarity >= 0.75 # Should be quite similar
    
    # 2. Entropy Divergence (Drift)
    # p = normal, q = uniform (drifted)
    p = [0.1, 0.2, 0.4, 0.2, 0.1]
    q = [0.2, 0.2, 0.2, 0.2, 0.2]
    
    div = forensic_math.calculate_entropy_divergence(p, q)
    print(f"[+] Entropy Divergence (nats): {div:.6f}")
    assert div > 0
    
    # Identical
    div_zero = forensic_math.calculate_entropy_divergence(p, p)
    print(f"[+] Zero Divergence: {div_zero:.6f}")
    assert div_zero < 1e-10
    
    print("[+] All Phase 11 algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_advanced_math()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
