import json
import os
from typing import Any

from src.ai.provider import SMEAIProvider


class LangflowProvider(SMEAIProvider):
    """
    Concrete implementation of SMEAIProvider using Langflow JSON flows.
    """

    def __init__(self, flows_dir: str = "src/ai/flows"):
        self.flows_dir = flows_dir

    def run(self, flow_name: str, input_data: Any) -> str:
        # Import Langflow only when needed (Sidecar environment)
        from langflow.load import load_flow_from_json

        # Special casing for legacy concept_lookup tool if needed,
        # but ideally this should be a flow too.
        if flow_name == "concept_lookup":
            # This is a bit of a leak, but keeps current logic working
            from src.ai.tools.conceptnet import format_concept_summary, get_concept_with_cache
            results = get_concept_with_cache(input_data)
            return format_concept_summary(results)

        flow_path = os.path.join(self.flows_dir, f"{flow_name}.json")

        if not os.path.exists(flow_path):
            raise FileNotFoundError(f"Langflow file not found: {flow_path}")

        flow = load_flow_from_json(flow_path)

        # input_data might need to be stringified for some Langflow versions
        input_val = json.dumps(input_data) if not isinstance(input_data, str) else input_data

        result = flow.run(input_val)
        return str(result)

    def get_metadata(self) -> dict[str, Any]:
        return {
            "provider": "Langflow",
            "flows_directory": self.flows_dir,
            "status": "active"
        }
