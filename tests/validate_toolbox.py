#!/usr/bin/env python3
"""
Toolbox Validation Script
Verifies all new tools can be imported and initialized.
"""

import sys
import json
from pathlib import Path

def validate_tool(tool_name: str, module_name: str) -> bool:
    """Validates a single tool module."""
    try:
        module = __import__(module_name)
        if hasattr(module, 'mcp'):
            print(f"✓ {tool_name:30} - MCP initialized")
            return True
        else:
            print(f"⚠ {tool_name:30} - No MCP instance found")
            return False
    except Exception as e:
        print(f"✗ {tool_name:30} - ERROR: {str(e)[:50]}")
        return False

def main():
    """Run validation."""
    print("\n" + "="*70)
    print("SimpleMem Toolbox Validation")
    print("="*70 + "\n")
    
    tools = {
        "The Loom (Semantic Distillation)": "semantic_loom",
        "The Synapse (Memory Consolidation)": "memory_synapse",
        "The Scout (Adaptive Retrieval)": "adaptive_scout",
        "Data Processor (Processing & Analysis)": "data_processor",
        "Monitoring & Diagnostics": "monitoring_diagnostics",
        "Pipeline Orchestrator (Integration)": "pipeline_orchestrator",
        "Retrieval & Query Engine": "retrieval_query",
    }
    
    results = {}
    for category, module_name in tools.items():
        print(f"\n{category}")
        print("-" * 70)
        results[category] = validate_tool(module_name, module_name)
    
    # Summary
    print("\n" + "="*70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Validation Result: {passed}/{total} passed")
    print("="*70 + "\n")
    
    if passed == total:
        print("✅ All tools validated successfully!")
        print("\nNext steps:")
        print("1. Review TOOLBOX_SUMMARY.md for overview")
        print("2. Check INTEGRATION_GUIDE.md for usage patterns")
        print("3. See TOOLBOX_REGISTRY.py for complete tool list")
        print("4. Run individual tools to test MCP endpoints")
        return 0
    else:
        print("⚠️  Some tools need attention. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
