"""
Unit Tests for ExtensionManager Sandbox & Circuit Breaker Hardening
=====================================================================
Tests sandboxed tool execution, exception isolation, and circuit breaker tripping.
"""

from __future__ import annotations

import pytest

from gateway.extension_manager import ExtensionManager


class MockPlugin:
    """Mock extension plugin with valid tools and failing tool."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0

    def get_tools(self):
        return {
            "ping": self.ping,
            "flaky_tool": self.flaky_tool,
        }

    def ping(self) -> dict:
        return {"status": "pong"}

    def flaky_tool(self) -> str:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError(f"Simulated plugin failure #{self.call_count}")
        return "success"


class TestExtensionSandboxAndCircuitBreaker:
    """Test sandboxed tool wrapping and circuit breaker behavior."""

    def test_successful_tool_execution(self):
        manager = ExtensionManager(nexus_api=None)
        plugin = MockPlugin(should_fail=False)

        manager.extensions["mock_plugin"] = {
            "instance": plugin,
            "manifest": {"name": "Mock Plugin", "version": "1.0"},
        }

        tools = manager.get_extension_tools()
        ping_tool = next(t for t in tools if t["name"] == "ping")

        res = ping_tool["handler"]()
        assert res == {"status": "pong"}
        assert manager.is_extension_healthy("mock_plugin") is True

    def test_exception_isolation_and_circuit_breaker_tripping(self):
        manager = ExtensionManager(nexus_api=None)
        plugin = MockPlugin(should_fail=True)

        manager.extensions["failing_plugin"] = {
            "instance": plugin,
            "manifest": {"name": "Failing Plugin", "version": "1.0"},
        }

        tools = manager.get_extension_tools()
        flaky_tool = next(t for t in tools if t["name"] == "flaky_tool")

        # Failure 1
        res1 = flaky_tool["handler"]()
        assert res1["status"] == "error"
        assert res1["consecutive_failures"] == 1
        assert res1["circuit_breaker_tripped"] is False

        # Failure 2
        res2 = flaky_tool["handler"]()
        assert res2["status"] == "error"
        assert res2["consecutive_failures"] == 2
        assert res2["circuit_breaker_tripped"] is False

        # Failure 3 -> Trips Circuit Breaker
        res3 = flaky_tool["handler"]()
        assert res3["status"] == "error"
        assert res3["consecutive_failures"] == 3
        assert res3["circuit_breaker_tripped"] is True

        assert manager.is_extension_healthy("failing_plugin") is False

        # Subsequent call blocked by Circuit Breaker
        res4 = flaky_tool["handler"]()
        assert res4["status"] == "circuit_breaker_tripped"

    def test_circuit_breaker_reset(self):
        manager = ExtensionManager(nexus_api=None)
        plugin = MockPlugin(should_fail=True)

        manager.extensions["resettable_plugin"] = {
            "instance": plugin,
            "manifest": {"name": "Resettable Plugin", "version": "1.0"},
        }

        tools = manager.get_extension_tools()
        flaky_tool = next(t for t in tools if t["name"] == "flaky_tool")

        # Trip circuit breaker
        for _ in range(3):
            flaky_tool["handler"]()

        assert manager.is_extension_healthy("resettable_plugin") is False

        # Reset circuit breaker
        manager.reset_plugin_circuit_breaker("resettable_plugin")
        assert manager.is_extension_healthy("resettable_plugin") is True

        # Plugin works after fixing failure flag
        plugin.should_fail = False
        res = flaky_tool["handler"]()
        assert res == "success"
