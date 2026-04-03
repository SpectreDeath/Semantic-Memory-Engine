from __future__ import annotations

from typing import Any

from src.ai.provider import SMEAIProvider


class MockProvider(SMEAIProvider):
    """
    Mock AI Provider for development and CI verification.
    """

    def run(self, flow_name: str, input_data: Any) -> str:
        return f"[MOCK AI RESULT] Flow: {flow_name} | Input: {input_data}"

    def get_metadata(self) -> dict[str, Any]:
        return {"provider": "Mock", "status": "simulated"}
