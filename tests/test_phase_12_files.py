import sys
import os
from pathlib import Path
import json

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.vendor import forensic_files

def test_forensic_files():
    print("[*] Testing Forensic Files (Structure & Masking) algorithms...")
    
    # Create temp files for testing
    pdf_path = "test_sample.pdf"
    txt_path = "test_sample.txt"
    packed_path = "test_packed.bin"
    
    try:
        # 1. PDF Signature Test
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\nTest content")
        
        sig_res = forensic_files.verify_file_signature(pdf_path)
        print(f"[+] PDF Match: {sig_res['is_match']}")
        assert sig_res['is_match'] is True
        
        # 2. Structural Complexity Test (Text)
        with open(txt_path, "wb") as f:
            f.write(b"Repeated " * 1000) # Highly compressible
            
        comp_res_low = forensic_files.calculate_structural_complexity(txt_path)
        print(f"[+] Text Complexity Ratio: {comp_res_low['complexity_ratio']}")
        assert comp_res_low['complexity_ratio'] < 0.2
        
        # 3. Structural Complexity Test (Random/Packed)
        with open(packed_path, "wb") as f:
            f.write(os.urandom(10000)) # Low compressibility
            
        comp_res_high = forensic_files.calculate_structural_complexity(packed_path)
        print(f"[+] Random Complexity Ratio: {comp_res_high['complexity_ratio']}")
        assert comp_res_high['complexity_ratio'] > 0.9
        assert comp_res_high['is_high_entropy'] is True
        
        print("[+] All Phase 12 algorithms verified successfully!")
        
    finally:
        # Cleanup
        for p in [pdf_path, txt_path, packed_path]:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    try:
        test_forensic_files()
    except Exception as e:
        print(f"[-] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
