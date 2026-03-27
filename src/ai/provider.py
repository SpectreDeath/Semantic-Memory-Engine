from abc import ABC, abstractmethod
from typing import Any


class SMEAIProvider(ABC):
    """
    Abstract Base Class for AI inference providers in the Semantic Memory Engine.
    Ensures 'Silicon Agnosticism' by defining a standard interface for execution
    and context expansion.
    """

    @abstractmethod
    def run(self, flow_name: str, input_data: Any) -> str:
        """
        Execute an AI flow/prompt and return the result as a string.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """
        Return provider-specific metadata (e.g., model name, version, status).
        """
        pass
