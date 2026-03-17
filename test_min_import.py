
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

print("[*] Importing src.sme.vendor.faststylometry...")
try:
    import src.sme.vendor.faststylometry
    print("[+] Success")
except Exception as e:
    import traceback
    traceback.print_exc()
