#!/usr/bin/env python3
"""
VRAM Watchdog for AionUi — GTX 1660 Ti Hardware Guardrail

Polls GPU memory every N seconds and emits JSON lines to stdout.
AionUi's process manager consumes this stream for real-time VRAM alerts.

Thresholds (from constitution & spec 004):
  CAUTION  : >= 5800 MB  (94.4%)
  CRITICAL : >= 5900 MB for 30s sustained  (96.0%)

On CRITICAL: sends SIGTERM to the Sidecar (brain_worker) process.
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration — mirrors hardwareGuardrails in aionui_settings.json
# ---------------------------------------------------------------------------
VRAM_TOTAL_MB = 6144
CAUTION_THRESHOLD_MB = 5800
CRITICAL_THRESHOLD_MB = 5900
POLL_INTERVAL_S = 10
SUSTAINED_ALERT_S = 30

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "vram_alerts.log")

# ---------------------------------------------------------------------------
# Logging setup (file-based, NOT stdout — stdout is reserved for JSON lines)
# ---------------------------------------------------------------------------
os.makedirs(LOG_DIR, exist_ok=True)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger = logging.getLogger("VRAMWatchdog")
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def _emit(level: str, vram_used_mb: int, vram_total_mb: int, action: str | None = None):
    """Write a single JSON line to stdout for AionUi consumption."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "vram_used_mb": vram_used_mb,
        "vram_total_mb": vram_total_mb,
        "pct": round(vram_used_mb / vram_total_mb * 100, 1),
    }
    if action:
        record["action"] = action
    print(json.dumps(record), flush=True)


def _get_vram_usage() -> tuple[int, int]:
    """Return (used_mb, total_mb) via pynvml.  Returns (-1, -1) on failure."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        used = mem.used // (1024 * 1024)
        total = mem.total // (1024 * 1024)
        pynvml.nvmlShutdown()
        return used, total
    except Exception as exc:
        logger.warning("pynvml query failed: %s", exc)
        return -1, -1


def _kill_sidecar():
    """Attempt to terminate the brain_worker (Sidecar) process."""
    logger.critical("Issuing SIGTERM to Sidecar processes (brain_worker.py)")
    try:
        # Find brain_worker processes
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, encoding="utf-8",
        )
        for line in result.stdout.strip().splitlines():
            # Check if this is a brain_worker process by inspecting command line
            # Fallback: kill all .brain_venv python processes
            pass  # Platform-specific PID resolution below

        # Use WMIC to find the exact PID running brain_worker.py
        wmic = subprocess.run(
            ["wmic", "process", "where",
             "commandline like '%brain_worker%' and commandline like '%.brain_venv%'",
             "get", "processid"],
            capture_output=True, text=True, encoding="utf-8",
        )
        for token in wmic.stdout.split():
            if token.strip().isdigit():
                pid = int(token.strip())
                logger.critical("Terminating Sidecar PID %d", pid)
                os.kill(pid, signal.SIGTERM)
    except Exception as exc:
        logger.error("Failed to kill sidecar: %s", exc)


def main():
    logger.info("VRAM Watchdog started — poll every %ds, CAUTION@%dMB, CRITICAL@%dMB",
                POLL_INTERVAL_S, CAUTION_THRESHOLD_MB, CRITICAL_THRESHOLD_MB)

    critical_since: float | None = None  # timestamp when CRITICAL first triggered

    while True:
        used, total = _get_vram_usage()

        if used < 0:
            # GPU unavailable — emit degraded status and back off
            _emit("DEGRADED", 0, VRAM_TOTAL_MB)
            time.sleep(POLL_INTERVAL_S * 3)
            continue

        # --- CRITICAL ---
        if used >= CRITICAL_THRESHOLD_MB:
            if critical_since is None:
                critical_since = time.monotonic()
            sustained = time.monotonic() - critical_since

            if sustained >= SUSTAINED_ALERT_S:
                _emit("CRITICAL", used, total, action="kill_sidecar")
                logger.critical("VRAM %dMB >= %dMB for %ds — killing sidecar",
                                used, CRITICAL_THRESHOLD_MB, int(sustained))
                _kill_sidecar()
                critical_since = None  # reset after action
            else:
                _emit("CRITICAL", used, total, action="alert")
                logger.warning("VRAM %dMB — CRITICAL for %ds / %ds",
                               used, int(sustained), SUSTAINED_ALERT_S)

        # --- CAUTION ---
        elif used >= CAUTION_THRESHOLD_MB:
            critical_since = None  # reset sustained counter
            _emit("CAUTION", used, total, action="alert")
            logger.warning("VRAM %dMB — CAUTION threshold reached", used)

        # --- NOMINAL ---
        else:
            critical_since = None
            _emit("INFO", used, total)

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("VRAM Watchdog stopped by user")
        sys.exit(0)
