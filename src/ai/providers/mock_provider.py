from typing import Any, Dict
from src.ai.provider import SME_AI_Provider

class MockProvider(SME_AI_Provider):
    """
    Mock AI Provider for development and CI verification.
    """

    def run(self, flow_name: str, input_data: Any) -> str:
        return f"[MOCK AI RESULT] Flow: {flow_name} | Input: {input_data}"

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "provider": "Mock",
            "status": "simulated"
        }
