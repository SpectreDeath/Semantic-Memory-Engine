"""
Unit Tests for MimoControlBridge (MIMO 6D Control Surface)
===========================================================
Tests 6D harness configuration synthesis, payload decoration, and TrafficRouter override.
"""

from __future__ import annotations

import pytest

from gateway.mimo_bridge import Mimo6DConfig, MimoControlBridge
from gateway.traffic_router import TrafficRouter


class TestMimoControlBridge:
    """Test MIMO 6D Control Surface Bridge."""

    def test_mimo_6d_config_defaults_and_dict(self):
        config = Mimo6DConfig()

        assert config.d1_context_max_triplets == 10
        assert config.d2_tool_timeout == 30.0
        assert config.d4_routing_mode == "auto"

        as_dict = config.to_dict()
        reconstructed = Mimo6DConfig.from_dict(as_dict)

        assert reconstructed.d1_context_max_triplets == 10
        assert reconstructed.d2_tool_timeout == 30.0

    def test_get_harness_config_synthesis(self):
        bridge = MimoControlBridge()

        cg_config = bridge.get_harness_config(task_type="code_gen")
        assert cg_config.d4_routing_mode == "em_cubed_workflow"
        assert cg_config.d3_decoding_temperature == 0.1

        lh_config = bridge.get_harness_config(task_type="long_horizon_repair")
        assert lh_config.d1_context_max_triplets == 25
        assert lh_config.d2_tool_timeout == 60.0

    def test_apply_harness_payload_decoration(self):
        bridge = MimoControlBridge()
        config = bridge.get_harness_config(task_type="code_gen")

        payload = {"code": "42"}
        decorated = bridge.apply_harness(config, payload)

        assert decorated["_mimo_harness"]["d4_routing_mode"] == "em_cubed_workflow"
        assert decorated["timeout"] == 15.0

    def test_traffic_router_mimo_override(self):
        router = TrafficRouter()
        bridge = MimoControlBridge()
        config = bridge.get_harness_config(task_type="code_gen")

        res = router.dispatch_workload(
            tool_name="verify_system",
            payload={"check": True},
            mode="local_only",
            mimo_config=config,
        )

        assert res["executed_by"] == "em_cubed_node"
