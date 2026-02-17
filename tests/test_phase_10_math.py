import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_math

def test_phonetic_fraud_math():
    print("[*] Testing Phonetic & Fraud Math algorithms...")
    
    # 1. Double Metaphone (Phonetics)
    word1 = "Smith"
    word2 = "Smyth"
    
    hash1 = forensic_math.calculate_phonetic_hash(word1)
    hash2 = forensic_math.calculate_phonetic_hash(word2)
    
    print(f"[+] '{word1}' Hash: {hash1['primary']}")
    print(f"[+] '{word2}' Hash: {hash2['primary']}")
    assert hash1['primary'] == hash2['primary']
    
    # 2. Benford's Law (Fraud)
    # Generate data following Benford's Law (e.g., 2^n)
    benford_data = [2**n for n in range(1, 100)]
    result = forensic_math.audit_benford_distribution(benford_data)
    
    print(f"[+] Benford Confidence: {result['confidence_score']}")
    print(f"[+] MAE: {result['mean_absolute_error']}")
    assert result['confidence_score'] > 0.8
    
    # Test non-Benford data (e.g., uniform distribution)
    uniform_data = list(range(100, 200)) # Leading digit mostly 1
    result_fail = forensic_math.audit_benford_distribution(uniform_data)
    print(f"[+] Uniform Benford Confidence: {result_fail['confidence_score']}")
    assert result_fail['confidence_score'] < 0.5
    
    print("[+] All Phase 10 algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_phonetic_fraud_math()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
