import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai.agent_logic import generate_forensic_summary
from src.utils.alerts import check_for_threat_collision
from src.utils.loaders import load_intel_data

def run_final_verify():
    print("=== FINAL SIMULATION VERIFICATION ===")
    
    # 1. Load Data
    osint_path = "data/raw/osint_results.json"
    news_path = "data/raw/forensic_news.json"
    
    intel_package = {
        "osint": load_intel_data(osint_path),
        "news": load_intel_data(news_path)
    }
    
    print(f"Loaded {len(intel_package['osint'])} OSINT records")
    print(f"Loaded {len(intel_package['news'])} News records")
    
    # Check if target is present in loaded data
    osint = intel_package.get("osint", [])
    if isinstance(osint, dict): osint = [osint]
    usernames = {s.get("username") for s in osint if s.get("username")}
    
    print(f"Usernames found: {usernames}")
    
    if "CBRN_Ghost_99" in usernames:
        print("SUCCESS: 'CBRN_Ghost_99' found in dataset.")
    else:
        print("FAILURE: 'CBRN_Ghost_99' NOT found. Re-injecting...")
        import subprocess
        subprocess.run([sys.executable, "tests/inject_mock_threat.py"])
        intel_package["osint"] = load_intel_data(osint_path)
        intel_package["news"] = load_intel_data(news_path)

    # 2. Trigger AI Brain Summary
    print("\n[AI BRAIN ANALYSIS]")
    summary = generate_forensic_summary(intel_package)
    print(f"AI SUMMARY: {summary}")
    
    # 3. Trigger Alert System
    print("\n[ALERT SYSTEM CHECK]")
    alert_fired = check_for_threat_collision(intel_package)
    print(f"ALERT TRIGGERED: {alert_fired}")
    
    if "CBRN_Ghost_99" in summary and alert_fired:
        print("\n🎯 MISSION SUCCESS: Poisoned Well simulation complete.")
        print("Forensic Stack fully operational on 1660 Ti environment.")
    else:
        print("\n❌ MISSION FAILURE: Logic did not trigger correctly.")

if __name__ == "__main__":
    run_final_verify()
