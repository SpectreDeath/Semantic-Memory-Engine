import sys
import os
import traceback
from pathlib import Path

# Robust path injection for Sidecar execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai.providers.factory import get_provider

def main():
    """
    Subprocess worker that runs in the Python 3.13 environment.
    Uses the SME_AI_Provider abstraction for silicon agnosticism.
    """
    if len(sys.argv) < 3:
        print("Usage: brain_worker.py <flow_name> <input_json>")
        sys.exit(1)
        
    flow_name = sys.argv[1]
    input_json = sys.argv[2]
    
    try:
        # 1. Get the configured provider from factory
        provider = get_provider()
        
        # 2. Add debug info if requested via env var
        if os.getenv("SME_DEBUG_AI"):
            metadata = provider.get_metadata()
            print(f"DEBUG: Using AI Provider: {metadata.get('provider')}", file=sys.stderr)

        # 3. Run the flow/logic via the provider
        result = provider.run(flow_name, input_json)
        
        # 4. Output results to stdout (captured by bridge)
        print(result)
        
    except Exception as e:
        print(f"Execution Error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(3)

if __name__ == "__main__":
    main()
