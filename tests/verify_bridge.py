import sys
import os
import subprocess

# Add project root to path for main imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_handshake():
    print("=== SME SIDE-BY-SIDE HEALTH CHECK ===")
    
    # 1. Check Main Environment (Body)
    print(f"[*] Main Env (Body): Python {sys.version.split()[0]}")
    
    # 2. Check Sidecar Environment (Brain)
    brain_python = os.path.abspath(".brain_venv/Scripts/python.exe")
    if not os.path.exists(brain_python):
        print("[!] ERROR: Sidecar python not found!")
        return False
        
    try:
        brain_ver = subprocess.check_output([brain_python, "--version"], text=True).strip()
        print(f"[*] Sidecar Env (Brain): {brain_ver}")
    except Exception as e:
        print(f"[!] ERROR checking Sidecar version: {e}")
        return False
        
    # 3. Test Bridge Handshake
    print("\n[*] Testing Bridge Handshake...")
    from src.ai.bridge import run_ai_flow
    
    result = run_ai_flow("test_flow", {"status": "ok"})
    
    if "SIMULATED AI VERDICT" in result or "Analysis" in result:
        print("[+] HANDSHAKE SUCCESSFUL!")
        print(f"    Message from Brain: {result}")
        return True
    else:
        print(f"[!] HANDSHAKE FAILED: {result}")
        return False

if __name__ == "__main__":
    success = test_handshake()
    sys.exit(0 if success else 1)
