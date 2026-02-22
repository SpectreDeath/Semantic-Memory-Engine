import sys
import os
import asyncio
import httpx
import json
import logging
import subprocess
import time
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extensions.ext_archival_diff.scout import WaybackScout
from src.utils.gephi_bridge import stream_archival_data
from extensions.ext_epistemic_gatekeeper.plugin import EpistemicGatekeeper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WaybackIntegration")

async def run_archival_pipeline(url: str):
    print(f"\n🚀 STARTING ARCHIVAL FORENSIC PIPELINE FOR: {url}")
    
    # 1. Start Sidecar
    brain_python = os.path.abspath(".brain_venv/Scripts/python.exe")
    if not os.path.exists(brain_python):
        brain_python = os.path.abspath(".brain_venv/bin/python")
    
    print(f"--- 🛰️ Spawning Warm-Start Sidecar ---")
    sidecar_proc = subprocess.Popen(
        [brain_python, "src/ai/sidecar.py"],
        env={**os.environ, "SME_AI_PROVIDER": "mock", "PYTHONPATH": str(PROJECT_ROOT)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5) # Wait for startup

    try:
        # 2. Scout Archival History
        print(f"--- 🛰️ Scouting Archival History ---")
        scout = WaybackScout()
        history = await scout.get_snapshot_history(url)
        
        if not history:
            print("No history found. Exiting.")
            return

        # Limit snapshots for demo efficiency
        history = history[:5] 
        print(f"Tracking {len(history)} snapshots.")

        # 3. Identify Divergent Points
        divergences = scout.identify_divergent_points(history)
        
        # 4. Deep Analysis via Sidecar and Nexus Logic
        gatekeeper = EpistemicGatekeeper({"plugin_id": "wayback_nexus"}, None)
        
        for d in divergences:
            print(f"--- 🔬 Analyzing Divergence: {d['pre_change']['human_date']} -> {d['post_change']['human_date']} ---")
            
            # Fetch content
            pre_content = await scout.fetch_snapshot_content(d['pre_change']['archive_url'])
            post_content = await scout.fetch_snapshot_content(d['post_change']['archive_url'])
            
            # Extract entities via Sidecar
            async with httpx.AsyncClient() as client:
                pre_r = await client.post("http://127.0.0.1:8089/forensics/nexus_verify", json={"new_content": pre_content})
                post_r = await client.post("http://127.0.0.1:8089/forensics/nexus_verify", json={"new_content": post_content})
                
                pre_entities = set(pre_r.json().get("entities_found", []))
                post_entities = set(post_r.json().get("entities_found", []))
            
            # Calculate Semantic Drift (Nexus Logic)
            drift_trust = await gatekeeper.semantic_nexus_check(list(post_entities), pre_entities)
            semantic_drift = 1.0 - drift_trust
            d['semantic_drift'] = semantic_drift
            
            print(f"    Semantic Drift detected: {semantic_drift:.2%}")

        # 5. Stream to Gephi
        print(f"--- 📊 Streaming Forensic Evidence to Gephi ---")
        stream_archival_data(url, history, divergences)
        
        print("\n✅ ARCHIVAL PIPELINE COMPLETE.")

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
    finally:
        print("--- 🛰️ Terminating Sidecar ---")
        sidecar_proc.terminate()

if __name__ == "__main__":
    test_url = "example.com" # Using a stable one for demo, but any works
    asyncio.run(run_archival_pipeline(test_url))
