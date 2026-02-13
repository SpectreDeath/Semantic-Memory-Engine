import sys
import os

# Add the src directory to path so it can find the vendored code
sys.path.append(os.path.abspath("src"))

try:
    from sme.vendor.faststylometry import burrows_delta
    print("✅ SME Forensic Lab: Vendored Faststylometry Verified.")
except ImportError as e:
    print(f"❌ Verification Failed: {e}")
    sys.exit(1)