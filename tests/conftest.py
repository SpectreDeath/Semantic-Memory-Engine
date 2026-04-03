"""
Pytest Configuration for Tests

Note: Pydantic v2 is used natively. No patches needed.
"""

import logging
import sys

logging.basicConfig(level=logging.INFO)


def pytest_collection_modifyitems(config, items):
    """Skip test_advanced_nlp.py on Python 3.14+ due to spacy/pydantic incompatibility."""
    if sys.version_info >= (3, 14):
        items[:] = [item for item in items if "test_advanced_nlp" not in str(item.fspath)]
