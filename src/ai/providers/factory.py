import os
from typing import Optional
from src.ai.provider import SME_AI_Provider

def get_provider() -> SME_AI_Provider:
    """
    Provider Factory: returns the configured AI provider.
    Defaults to Langflow if not specified.
    """
    provider_type = os.getenv("SME_AI_PROVIDER", "langflow").lower()

    if provider_type == "langflow":
        from src.ai.providers.langflow_provider import LangflowProvider
        return LangflowProvider()

    elif provider_type == "sentinel":
        from src.ai.providers.sentinel_provider import SentinelProvider
        return SentinelProvider()

    elif provider_type == "mock":
        from src.ai.providers.mock_provider import MockProvider
        return MockProvider()

    raise ValueError(f"Unknown AI provider type: {provider_type}")