"""
Pytest Configuration

Note: Pydantic v2 is now used natively. No monkey patches needed.
"""

import logging
import os

os.environ.setdefault("SME_GATEWAY_SECRET", "test-secret-key-for-unit-tests")

logging.basicConfig(level=logging.INFO)
