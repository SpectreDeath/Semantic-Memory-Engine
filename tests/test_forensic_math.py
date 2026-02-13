import sys
import os
from pathlib import Path
import json

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_math

def test_forensic_math():
    print("[*] Testing Forensic Math algorithms...")
    
    # 1. Cosine Similarity
    v1 = {"the": 0.5, "and": 0.3, "hacker": 0.1}
    v2 = {"the": 0.4, "and": 0.3, "victim": 0.1}
    
    from src.sme.vendor.forensic_math import dict_to_vectors
    nv1, nv2 = dict_to_vectors(v1, v2)
    similarity = forensic_math.calculate_cosine_similarity(nv1, nv2)
    print(f"[+] Cosine Similarity: {similarity:.4f}")
    assert 0.8 < similarity < 1.0
    
    # 2. Levenshtein Distance
    s1 = "administrator"
    s2 = "adminstrator" # Typo (missing 'i')
    distance = forensic_math.calculate_typo_distance(s1, s2)
    print(f"[+] Typo Distance: {distance}")
    assert distance == 1
    
    # 3. Jaccard Index
    list1 = ["exploit", "buffer", "overflow", "nop"]
    list2 = ["exploit", "buffer", "underflow", "shellcode"]
    overlap = forensic_math.calculate_set_overlap(list1, list2)
    print(f"[+] Set Overlap (Jaccard): {overlap:.4f}")
    assert overlap == 2/6 # intersection {exploit, buffer} (2), union {exploit, buffer, overflow, underflow, nop, shellcode} (6)
    
    print("[+] All math algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_forensic_math()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
