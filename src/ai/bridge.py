import subprocess
import sys
import os
import json
import logging
import httpx # Required for sidecar communication

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Bridge")

SIDECAR_URL = os.getenv("SME_SIDECAR_URL", "http://127.0.0.1:8089")

def run_ai_flow(flow_name, input_data):
    """
    Executes a Langflow JSON flow. 
    Tries the Warm-Start sidecar first (HTTP), then falls back to subprocess for cold-start.
    """
    
    # 1. Try Warm-Start Sidecar via HTTP
    try:
        logger.info(f"Attempting Warm-Start via Sidecar: {flow_name}")
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{SIDECAR_URL}/run",
                json={"flow_name": flow_name, "input_data": input_data}
            )
            if response.status_code == 200:
                return response.json().get("result")
            else:
                logger.warning(f"Sidecar returned error {response.status_code}: {response.text}")
    except (httpx.ConnectError, httpx.HTTPError) as e:
        logger.warning(f"Sidecar unreachable or failed: {e}. Falling back to Cold-Start.")

    # 2. Fallback: Cold-Start via Subprocess
    # Path to the 'Brain' interpreter
    brain_python = os.path.abspath(".brain_venv/Scripts/python.exe")
    
    if not os.path.exists(brain_python):
        # On Linux/WSL it might be bin/python
        brain_python = os.path.abspath(".brain_venv/bin/python")
        if not os.path.exists(brain_python):
            return f"Error: Sidecar environment not found."
    
    worker_script = os.path.abspath("src/ai/brain_worker.py")
    if not os.path.exists(worker_script):
        return f"Error: Worker script not found."
    
    if not isinstance(input_data, str):
        input_json = json.dumps(input_data)
    else:
        input_json = input_data

    env = os.environ.copy()
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env["PYTHONPATH"] = project_root
    
    logger.info(f"Spawning Cold-Start Subprocess for flow: {flow_name}")
    
    try:
        result = subprocess.run(
            [brain_python, worker_script, flow_name, input_json],
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=env
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            logger.error(f"Brain Error: {error_msg}")
            return f"Error in Brain: {error_msg}"
            
        return result.stdout.strip()
        
    except Exception as e:
        logger.exception("Bridge failed to communicate with Sidecar (Cold-Start)")
        return f"Bridge Failure: {str(e)}"

if __name__ == "__main__":
    # Test call
    print(run_ai_flow("test_flow", {"test": "data"}))
