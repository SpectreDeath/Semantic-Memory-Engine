import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_signal

def test_forensic_signal():
    print("[*] Testing Forensic Signal (Sequence & Frequency) algorithms...")
    
    # 1. DTW Sequence Similarity Test
    # Similar patterns but shifted/stretched
    seq1 = [1, 2, 3, 2, 1]
    seq2 = [1, 1, 2, 2, 3, 3, 2, 2, 1, 1]
    
    res_sim = forensic_signal.calculate_sequence_similarity(seq1, seq2)
    print(f"[+] DTW Alignment Cost: {res_sim['alignment_cost']} (Similarity: {res_sim['similarity_score']})")
    assert res_sim['similarity_score'] > 0.8
    
    # Very different patterns
    seq3 = [1, 1, 1, 1, 1]
    seq4 = [9, 9, 9, 9, 9]
    res_diff = forensic_signal.calculate_sequence_similarity(seq3, seq4)
    print(f"[+] DTW Diff Cost: {res_diff['alignment_cost']} (Similarity: {res_diff['similarity_score']})")
    assert res_diff['similarity_score'] < 0.2
    
    # 2. Fourier Periodicity Test
    # Sine wave with period of 10 samples
    x = np.linspace(0, 100, 100)
    data = np.sin(2 * np.pi * x / 10).tolist()
    
    res_freq = forensic_signal.detect_event_periodicity(data)
    print(f"[+] Dominant Period: {res_freq['dominant_frequencies'][0]['period_samples']}")
    # Expected frequency = 1/10 = 0.1
    # period_samples should be close to 10
    assert abs(res_freq['dominant_frequencies'][0]['period_samples'] - 10.0) < 1.0
    
    print("[+] All Phase 15 algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_forensic_signal()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
