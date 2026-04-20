"""
Tests for gateway/tools/diagnostics.py - Diagnostic tool definitions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from gateway.tools.diagnostics import DIAGNOSTIC_TOOLS
from gateway.tool_registry import ToolDefinition


def test_diagnostic_tools_keys():
    assert "verify_system" in DIAGNOSTIC_TOOLS
    assert "get_memory_stats" in DIAGNOSTIC_TOOLS


def test_verify_system_definition():
    tool: ToolDefinition = DIAGNOSTIC_TOOLS["verify_system"]
    assert tool.name == "verify_system"
    assert tool.category == "diagnostics"
    assert tool.factory_method == "create_system_monitor"


def test_get_memory_stats_definition():
    tool: ToolDefinition = DIAGNOSTIC_TOOLS["get_memory_stats"]
    assert tool.name == "get_memory_stats"
    assert tool.factory_method == "create_centrifuge"
