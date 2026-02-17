#!/usr/bin/env python3
"""
🛰️ Sentinel Monitor v2.2.0 — Hardware-Aware VRAM Guardian

Polls GPU memory and signals the AI Sidecar to adjust offloading strategy.
Prioritizes GGUF stability over EXL2 speed.

Thresholds:
  OFFLOAD : >= 5500 MB (Trigger GGUF-to-RAM offloading)
  CRITICAL: >= 5900 MB (Issue SIGTERM if offloading fails to stabilize)
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
import httpx
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VRAM_TOTAL_MB = 6144
OFFLOAD_THRESHOLD_MB = 5500
CRITICAL_THRESHOLD_MB = 5900
POLL_INTERVAL_S = 10
SIDECAR_URL = os.getenv("SME_SIDECAR_URL", "http://127.0.0.1:8089")

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "sentinel_alerts.log")

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")]
)
logger = logging.getLogger("Sentinel")

def _emit(level: str, used: int, action: str | None = None):
    """Output JSON for telemetry consumption."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "vram_used_mb": used,
        "action": action
    }
    print(json.dumps(record), flush=True)

def _get_vram():
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        used = mem.used // (1024 * 1024)
        pynvml.nvmlShutdown()
        return used
    except Exception as e:
        logger.error(f"NVML Error: {e}")
        return -1

def _signal_offload():
    """Notify sidecar to move layers to System RAM."""
    logger.warning("VRAM high. Signaling Sidecar to OFFLOAD layers to System RAM.")
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(f"{SIDECAR_URL}/sentinel/offload", json={"vram_pressure": "high"})
    except Exception as e:
        logger.error(f"Failed to signal sidecar: {e}")

def _kill_sidecar():
    logger.critical("CRITICAL VRAM. Terminating sidecar.")
    try:
        # Resolve brain_worker PIDs via wmic (Windows legacy support)
        cmd = ["wmic", "process", "where", "commandline like '%brain_worker%'", "get", "processid"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if line.strip().isdigit():
                pid = int(line.strip())
                os.kill(pid, signal.SIGTERM)
    except Exception as e:
        logger.error(f"Kill failed: {e}")

def main():
    logger.info("Sentinel Monitor v2.2.0 active.")
    offload_active = False

    while True:
        used = _get_vram()
        if used < 0:
            time.sleep(POLL_INTERVAL_S)
            continue

        if used >= CRITICAL_THRESHOLD_MB:
            _emit("CRITICAL", used, "kill")
            _kill_sidecar()
        elif used >= OFFLOAD_THRESHOLD_MB:
            if not offload_active:
                _emit("WARNING", used, "offload")
                _signal_offload()
                offload_active = True
        else:
            if offload_active:
                _emit("INFO", used, "normal")
                offload_active = False
            _emit("INFO", used)

        time.sleep(POLL_INTERVAL_S)

if __name__ == "__main__":
    main()
