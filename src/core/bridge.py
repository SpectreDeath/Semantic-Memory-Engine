import subprocess
import os
import time

# Paths to your verified infrastructure
WEB_SEARCH_SCRIPT = "D:/mcp_servers/web_search.py"
WATCHER_LOGS = "D:/mcp_servers/logs"
STORAGE_JAIL = "D:/mcp_servers/storage"

def run_agent_mission(topic):
    print(f"🕵️ Agent Mission Started: Investigating '{topic}'")
    
    # 1. BROWSE: Trigger the WebSearcher with retry logic
    print("🌐 Step 1: Browsing the web for intelligence...")
    try:
        # We call your existing web_search.py which has the 3-try retry loop
        subprocess.run(["python", WEB_SEARCH_SCRIPT, topic], check=True)
    except Exception as e:
        print(f"❌ Search Failed: {e}")
        return

    # 2. SECURE & ANALYZE: Wait for the Watcher to detect the new file
    # Your 6,734-signal brain is already watching storage/
    print("🧠 Step 2: Analyzing rhetoric against 6,734 professional signals...")
    time.sleep(3)  # Give the watcher a moment to breathe

    # 3. REPORT: Find the latest log generated
    print("📂 Step 3: Compiling final intelligence report...")
    logs = [os.path.join(WATCHER_LOGS, f) for f in os.listdir(WATCHER_LOGS) if f.endswith('.json')]
    if not logs:
        print("⚠️ No logs found. Did the Watcher script crash?")
        return
    
    latest_log = max(logs, key=os.path.getctime)
    
    print(f"\n✨ MISSION COMPLETE ✨")
    print(f"📄 Full Report Saved: {latest_log}")
    print(f"👉 PASTE THE CONTENT OF THIS LOG TO WHITERABBITNEO FOR FINAL DEBRIEF.")

if __name__ == "__main__":
    query = input("Enter Topic or URL for investigation: ")
    run_agent_mission(query)
    