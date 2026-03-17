
try:
    import sys
    import os
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.absolute()))
    
    print("[*] Attempting to import crawler_sling...")
    from src.sme.bridge import crawler_sling
    print("[+] Successfully imported crawler_sling")
    
    print("[*] Attempting to import plugin from scrapegraph_harvester...")
    from extensions.ext_scrapegraph_harvester import plugin
    print("[+] Successfully imported scrapegraph_harvester plugin")
    
except Exception as e:
    import traceback
    print("[-] CRITICAL ERROR during import:")
    traceback.print_exc()
    sys.exit(1)
