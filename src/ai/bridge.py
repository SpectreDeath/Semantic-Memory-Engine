import json
import logging
import os
import subprocess

import httpx  # Required for sidecar communication

from gateway.circuit_breaker import get_sidecar_circuit_breaker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Bridge")

SIDECAR_URL = os.getenv("SME_SIDECAR_URL", "http://127.0.0.1:8089")


def _cold_start(flow_name, input_data):
    """Fallback: Cold-Start via Subprocess."""
    brain_python = os.path.abspath(".brain_venv/Scripts/python.exe")

    if not os.path.exists(brain_python):
        brain_python = os.path.abspath(".brain_venv/bin/python")
        if not os.path.exists(brain_python):
            return "Error: Sidecar environment not found."

    worker_script = os.path.abspath("src/ai/brain_worker.py")
    if not os.path.exists(worker_script):
        return "Error: Worker script not found."

    input_json = json.dumps(input_data) if not isinstance(input_data, str) else input_data

    env = os.environ.copy()
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env["PYTHONPATH"] = project_root

    logger.info(f"Spawning Cold-Start Subprocess for flow: {flow_name}")

    try:
        result = subprocess.run(
            [brain_python, worker_script, flow_name, input_json],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip()
            logger.error(f"Brain Error: {error_msg}")
            return f"Error in Brain: {error_msg}"

        return result.stdout.strip()

    except Exception as e:
        logger.exception("Bridge failed to communicate with Sidecar (Cold-Start)")
        return f"Bridge Failure: {e!s}"


def run_ai_flow(flow_name, input_data):
    """
    Executes a Langflow JSON flow.
    Uses circuit breaker for sidecar communication with fallback to cold-start.
    """

    circuit_breaker = get_sidecar_circuit_breaker()

    def _warm_start():
        """Try Warm-Start Sidecar via HTTP."""
        logger.info(f"Attempting Warm-Start via Sidecar: {flow_name}")
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{SIDECAR_URL}/run", json={"flow_name": flow_name, "input_data": input_data}
            )
            if response.status_code == 200:
                return response.json().get("result")
            else:
                logger.warning(f"Sidecar returned error {response.status_code}: {response.text}")
                raise httpx.HTTPStatusError(
                    f"Sidecar error: {response.status_code}",
                    request=response.request,
                    response=response,
                )

    state = circuit_breaker.state
    if state.value == "open":
        logger.warning(f"Circuit 'sidecar': OPEN - skipping to Cold-Start for flow: {flow_name}")
        return _cold_start(flow_name, input_data)
    elif state.value == "half_open":
        logger.info(f"Circuit 'sidecar': HALF_OPEN - testing recovery for flow: {flow_name}")

    result = circuit_breaker.call(_warm_start, fallback=None)

    if result is None:
        logger.warning(f"Circuit breaker fallback triggered for flow: {flow_name}")
        return _cold_start(flow_name, input_data)

    return result
