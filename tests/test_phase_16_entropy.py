import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_entropy

def test_forensic_entropy():
    print("[*] Testing Forensic Entropy (Mapping & Obfuscation) algorithms...")
    
    # 1. Sliding Window Entropy Mapping Test
    # Random data (High entropy)
    high_entropy_data = np.random.randint(0, 256, size=1000).tolist()
    res_high = forensic_entropy.map_stream_entropy(high_entropy_data, window_size=256)
    print(f"[+] Mean High Entropy: {res_high['mean_entropy']}")
    assert res_high['mean_entropy'] > 7.0
    
    # Low entropy data (Repeated bytes)
    low_entropy_data = [0] * 1000
    res_low = forensic_entropy.map_stream_entropy(low_entropy_data, window_size=256)
    print(f"[+] Mean Low Entropy: {res_low['mean_entropy']}")
    assert res_low['mean_entropy'] < 0.1
    
    # 2. Obfuscation Analysis Test
    # Normal text
    normal_text = "This is a normal forensic report with clear ASCII text. " * 20
    res_normal = forensic_entropy.analyze_obfuscation_score(normal_text)
    print(f"[+] Normal Text Obfuscation Score: {res_normal['obfuscation_score']} (Weight: {res_normal['hamming_weight']})")
    assert res_normal['obfuscation_score'] < 0.5
    
    # "Obfuscated" data (Random bytes)
    random_bytes = os.urandom(1000)
    res_obf = forensic_entropy.analyze_obfuscation_score(random_bytes)
    print(f"[+] Obfuscated Data Score: {res_obf['obfuscation_score']} (Weight: {res_obf['hamming_weight']})")
    assert res_obf['obfuscation_score'] > 0.7
    assert res_obf['is_likely_obfuscated'] is True
    
    print("[+] All Phase 16 algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_forensic_entropy()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
