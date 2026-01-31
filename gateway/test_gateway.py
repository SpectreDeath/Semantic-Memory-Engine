"""Quick test script for the Lawnmower Man Gateway."""
import sys
import os
import json

# Ensure SME is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_registry():
    """Test the tool registry."""
    print("=" * 50)
    print("Testing Tool Registry")
    print("=" * 50)
    
    from gateway.tool_registry import get_registry
    
    registry = get_registry()
    tools = registry.list_tools()
    
    print(f"✅ Tool Registry loaded: {len(tools)} tools")
    print(f"   Categories: {registry.get_categories()}")
    
    # List tools by category
    for category in sorted(registry.get_categories()):
        cat_tools = registry.list_tools(category=category)
        print(f"\n   [{category.upper()}]")
        for tool in cat_tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
    
    return True


def test_mcp_server():
    """Test the MCP server import and basic functions."""
    print("\n" + "=" * 50)
    print("Testing MCP Server")
    print("=" * 50)
    
    # Import the module to check it loads
    from gateway import mcp_server
    
    print("✅ MCP Server imported successfully")
    
    # The decorated functions are now FunctionTool objects
    # We need to call their underlying function via .fn
    verify_fn = mcp_server.verify_system
    stats_fn = mcp_server.get_memory_stats
    list_fn = mcp_server.list_available_tools
    
    # Get the actual callable function
    if hasattr(verify_fn, 'fn'):
        verify_callable = verify_fn.fn
        stats_callable = stats_fn.fn
        list_callable = list_fn.fn
    else:
        # Fallback if it's already callable
        verify_callable = verify_fn
        stats_callable = stats_fn
        list_callable = list_fn
    
    # Test verify_system
    print("\n--- verify_system() ---")
    result = json.loads(verify_callable())
    print(f"   Status: {result['status']}")
    if 'telemetry' in result and result['telemetry']:
        print(f"   CPU: {result['telemetry'].get('cpu_percent', 'N/A')}%")
        print(f"   RAM: {result['telemetry'].get('memory_used_percent', 'N/A')}%")
    
    # Test get_memory_stats
    print("\n--- get_memory_stats() ---")
    stats = json.loads(stats_callable())
    print(f"   Health: {stats['health']}")
    print(f"   Storage: {stats.get('storage', {})}")
    
    # Test list_available_tools
    print("\n--- list_available_tools() ---")
    tools = json.loads(list_callable())
    print(f"   Gateway: {tools['gateway']} v{tools['version']}")
    print(f"   Tool count: {tools['tool_count']}")
    
    return True


def main():
    """Run all tests."""
    print("\n🌿 Lawnmower Man Gateway - Verification Tests\n")
    
    try:
        test_registry()
        test_mcp_server()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED")
        print("=" * 50)
        print("\nThe gateway is ready for use!")
        print("Run with: python -m gateway.mcp_server")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
