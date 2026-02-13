import subprocess
import sys
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Bridge")

def run_ai_flow(flow_name, input_data):
    """
    Executes a Langflow JSON flow using the dedicated Python 3.13 environment.
    
    Args:
        flow_name (str): Name of the flow file in src/ai/flows/ (without .json)
        input_data (dict/str): Data to pass to the flow. Will be serialized to JSON.
        
    Returns:
        str: Output from the AI flow or error message.
    """
    # Path to the 'Brain' interpreter
    # Using absolute path for robustness
    brain_python = os.path.abspath(".brain_venv/Scripts/python.exe")
    
    if not os.path.exists(brain_python):
        return f"Error: Sidecar environment not found at {brain_python}"
    
    # Path to the worker script
    worker_script = os.path.abspath("src/ai/brain_worker.py")
    
    if not os.path.exists(worker_script):
        return f"Error: Worker script not found at {worker_script}"
    
    # Serialize input data
    if not isinstance(input_data, str):
        input_json = json.dumps(input_data)
    else:
        input_json = input_data

    # Prepare environment with PYTHONPATH
    env = os.environ.copy()
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env["PYTHONPATH"] = project_root
    
    logger.info(f"Spawning Sidecar for flow: {flow_name}")
    
    # Call the brain environment
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
        logger.exception("Bridge failed to communicate with Sidecar")
        return f"Bridge Failure: {str(e)}"

if __name__ == "__main__":
    # Test call
    print(run_ai_flow("test_flow", {"test": "data"}))
