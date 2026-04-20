"""
Tests for gateway/tools/memory.py - Memory tool definitions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from gateway.tools.memory import MEMORY_TOOLS
from gateway.tool_registry import ToolDefinition


def test_memory_tools_keys():
    assert "save_memory" in MEMORY_TOOLS
    assert "get_session_info" in MEMORY_TOOLS
    assert "update_scratchpad" in MEMORY_TOOLS


def test_save_memory_definition():
    tool: ToolDefinition = MEMORY_TOOLS["save_memory"]
    assert tool.name == "save_memory"
    assert tool.category == "memory"
    assert tool.factory_method == "create_synapse"
    assert "fact" in tool.parameters
    assert "source" in tool.parameters


def test_session_tools():
    assert MEMORY_TOOLS["get_session_info"].category == "session"
    assert MEMORY_TOOLS["update_scratchpad"].category == "session"
