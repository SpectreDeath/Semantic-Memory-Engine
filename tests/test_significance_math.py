import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_math

def test_significance_math():
    print("[*] Testing Significance Math algorithms...")
    
    # 1. TF-IDF
    docs = [
        ["the", "hacker", "attacked", "the", "server"],
        ["the", "victim", "reported", "the", "attack"],
        ["a", "new", "vulnerability", "was", "found"]
    ]
    
    tfidf_matrix, vocab = forensic_math.calculate_tfidf(docs)
    print(f"[+] Vocabulary: {vocab}")
    print(f"[+] TF-IDF Matrix Shape: {tfidf_matrix.shape}")
    assert tfidf_matrix.shape == (3, len(vocab))
    # "hacker" should have higher significance in doc 0 than "the"
    hacker_idx = vocab.index("hacker")
    the_idx = vocab.index("the")
    assert tfidf_matrix[0, hacker_idx] > tfidf_matrix[0, the_idx]
    
    # 2. KL Divergence
    # Distribution P (Target)
    p = np.array([0.4, 0.4, 0.2])
    # Distribution Q (Reference)
    q = np.array([0.1, 0.1, 0.8])
    
    divergence = forensic_math.calculate_kl_divergence(p, q)
    print(f"[+] KL Divergence: {divergence:.6f}")
    assert divergence > 0
    
    # Test identical distributions (should be near 0)
    div_ident = forensic_math.calculate_kl_divergence(p, p)
    print(f"[+] Identical Distribution KL: {div_ident:.6f}")
    assert div_ident < 1e-5
    
    print("[+] All significance algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_significance_math()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
