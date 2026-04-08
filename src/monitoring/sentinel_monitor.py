from __future__ import annotations

#!/usr/bin/env python3
"""
🛰️ Sentinel Monitor v3.0.0 — Hardware-Aware VRAM Guardian

Polls GPU memory and monitors VRAM pressure.
No longer signals sidecar (removed in v3.0.1).

Thresholds:
  WARNING : >= 5500 MB (Log warning)
  CRITICAL: >= 5900 MB (Log critical alert)
"""

import json
import logging
import os
import time
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VRAM_TOTAL_MB = 6144
WARNING_THRESHOLD_MB = 5500
CRITICAL_THRESHOLD_MB = 5900
POLL_INTERVAL_S = 10

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "sentinel_alerts.log")

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger("Sentinel")


def _emit(level: str, used: int, action: str | None = None):
    """Output JSON for telemetry consumption."""
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "level": level,
        "vram_used_mb": used,
        "action": action,
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
        logger.exception(f"NVML Error: {e}")
        return -1


def main():
    logger.info("Sentinel Monitor v3.0.0 active (no sidecar).")
    warning_active = False

    while True:
        used = _get_vram()
        if used < 0:
            time.sleep(POLL_INTERVAL_S)
            continue

        if used >= CRITICAL_THRESHOLD_MB:
            _emit("CRITICAL", used, "alert")
            logger.critical(f"VRAM CRITICAL: {used}MB / {VRAM_TOTAL_MB}MB")
        elif used >= WARNING_THRESHOLD_MB:
            if not warning_active:
                _emit("WARNING", used, "alert")
                logger.warning(f"VRAM HIGH: {used}MB / {VRAM_TOTAL_MB}MB")
                warning_active = True
        else:
            if warning_active:
                _emit("INFO", used, "normal")
                logger.info(f"VRAM normal: {used}MB / {VRAM_TOTAL_MB}MB")
                warning_active = False
            _emit("INFO", used)

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
