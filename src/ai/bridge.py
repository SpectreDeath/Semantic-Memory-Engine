import json
import logging
import os

from src.ai.providers.factory import get_provider

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Bridge")

_provider = None


def _get_provider():
    """Get or create the AI provider (lazy initialization)."""
    global _provider
    if _provider is None:
        logger.info("Initializing AI provider...")
        _provider = get_provider()
        logger.info(f"AI Provider initialized: {_provider.__class__.__name__}")
    return _provider


def run_ai_flow(flow_name, input_data):
    """
    Executes an AI flow using the configured provider.
    Uses direct provider calls instead of HTTP sidecar.
    """
    try:
        provider = _get_provider()
        logger.info(f"Running AI flow: {flow_name}")

        if hasattr(provider, "run"):
            result = provider.run(flow_name, input_data)
            return result
        elif hasattr(provider, "execute"):
            result = provider.execute(flow_name, input_data)
            return result
        else:
            logger.error(f"Provider {provider.__class__.__name__} has no run/execute method")
            return f"Error: Provider {provider.__class__.__name__} not supported"

    except Exception as e:
        logger.exception(f"AI flow failed: {e}")
        return f"AI Flow Error: {e!s}"
