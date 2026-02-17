import asyncio
import sys
import os
from pathlib import Path
import json

# Ensure SME src is importable
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from src.sme.bridge import crawler_sling

async def test_crawler_sling():
    print("[*] Testing Crawler Sling Bridge...")
    
    # We'll use a public domain often used for testing
    test_url = "https://example.com"
    
    print(f"[*] Ingesting target: {test_url}")
    result = await crawler_sling.ingest_forensic_target(test_url)
    
    print(f"[+] Result Status: {result.get('status')}")
    if result.get('status') == "Success":
        print(f"[+] URL: {result.get('url')}")
        print(f"[+] Token Count: {result.get('token_count')}")
        print(f"[+] SimHash: {result.get('simhash')}")
        print(f"[+] Lexical Richness: {result.get('fingerprint_summary', {}).get('lexical_richness')}")
        
        assert result.get('token_count', 0) > 0
        assert "simhash" in result
        print("[+] Crawler Sling bridge verified successfully!")
    else:
        print(f"[-] Bridge failed: {result.get('error')}")
        # If no internet, this might fail, so we'll note that.
        if "ConnectError" in str(result.get('error')):
            print("[!] Skipping live URL test due to connection issues (Expected in some environments).")
            return
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_crawler_sling())
    except Exception as e:
        print(f"[-] Test execution failed: {e}")
        sys.exit(1)
