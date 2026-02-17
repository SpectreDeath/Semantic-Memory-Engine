import sys
import os
from pathlib import Path
import json
import numpy as np

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_behavior

def test_forensic_behavior():
    print("[*] Testing Forensic Behavior (Temporal & Leakage) algorithms...")
    
    # 1. Temporal Burstiness Test
    # Perfectly periodic events (Low burstiness)
    periodic_ts = np.arange(0, 100, 10) # 0, 10, 20...
    res_periodic = forensic_behavior.calculate_burstiness(periodic_ts.tolist())
    print(f"[+] Periodic Burstiness Score: {res_periodic['burstiness_score']}")
    assert res_periodic['burstiness_score'] < 0
    
    # Highly bursty events (High burstiness)
    bursty_ts = [0, 1, 2, 80, 81, 82, 150, 151, 152]
    res_bursty = forensic_behavior.calculate_burstiness(bursty_ts)
    print(f"[+] Bursty Burstiness Score: {res_bursty['burstiness_score']}")
    assert res_bursty['burstiness_score'] > 0.2
    
    # 2. Luhn Leakage Test
    valid_card = "79927398713" # Standard Luhn test number
    res_valid = forensic_behavior.validate_luhn_checksum(valid_card)
    print(f"[+] Valid Luhn Checksum: {res_valid['is_valid']}")
    assert res_valid['is_valid'] is True
    
    invalid_card = "79927398714"
    res_invalid = forensic_behavior.validate_luhn_checksum(invalid_card)
    print(f"[+] Invalid Luhn Checksum: {res_invalid['is_valid']}")
    assert res_invalid['is_valid'] is False
    
    print("[+] All Phase 13 algorithms verified successfully!")

if __name__ == "__main__":
    try:
        test_forensic_behavior()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
