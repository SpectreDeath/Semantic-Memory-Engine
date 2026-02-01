import os
import sys
import inspect
from datetime import datetime

# Ensure SME src is importable (d:\SME)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# IMPORT MCP SERVER TO TRIGGER REGISTRATIONS (like Scribe Pro, Influence Tool)
try:
    import gateway.mcp_server
except ImportError as e:
    print(f"Warning: could not import gateway.mcp_server ({e}). Using static registry.")

from gateway.tool_registry import get_registry, ToolDefinition

def generate_markdown_manifest(output_file="d:/SME/gateway/User_Guide.md"):
    header = "\n\n## 🧬 System Manifest: Live Tool Registry\n"
    table_header = "| Tool Name | Description | Parameters |\n| :--- | :--- | :--- |\n"
    rows = []

    registry = get_registry()

    # Iterate through all tools registered in your Lawnmower Man gateway
    # Our registry.tools returns either a ToolDefinition or a live instance
    for tool_name, tool_item in registry.tools.items():
        if isinstance(tool_item, ToolDefinition):
            # It's a static definition (not yet instantiated)
            doc = tool_item.description
            params = ", ".join(f"`{p}`" for p in tool_item.parameters.keys())
        else:
            # It's a live instance or function (manually injected)
            # Try to find the primary method
            func = getattr(tool_item, tool_name, None)
            if not func:
                # Try common method names
                for method_name in ['run', 'analyze', 'evaluate_claim', 'get_influence_score', 'analyze_authorship']:
                    if hasattr(tool_item, method_name):
                        func = getattr(tool_item, method_name)
                        break
            
            if not func or not callable(func):
                doc = "No description provided."
                params = "N/A"
            else:
                doc = inspect.getdoc(func) or "No description provided."
                try:
                    sig = inspect.signature(func)
                    params_list = []
                    for p in sig.parameters:
                        if p in ["self", "session_id"]: continue
                        params_list.append(f"`{p}`")
                    params = ", ".join(params_list)
                except (ValueError, TypeError):
                    params = "N/A"

        rows.append(f"| `{tool_name}` | {doc.split('.')[0]} | {params} |")

    # Final assembly
    manifest = header + table_header + "\n".join(rows) + "\n\n*Last Updated: 2026-01-31*"

    # Create directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Reset/Append to your User Guide
    # The user asked to "Append", but usually for a manifest you might want to overwrite or clarify.
    # We will append as requested.
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(manifest)
    
    print(f"✅ Success! {len(rows)} tools exported to {output_file}")

if __name__ == "__main__":
    generate_markdown_manifest()
