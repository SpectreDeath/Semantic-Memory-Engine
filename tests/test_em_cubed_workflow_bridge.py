"""
Unit Tests for em-cubed Distributed Workflow Orchestration Bridge
===================================================================
Tests multi-step DAG submission, payload propagation, and TrafficRouter delegation.
"""

from __future__ import annotations

import pytest

from gateway.em_cubed_bridge import EmCubedWorkflowBridge
from gateway.traffic_router import RULE_EM_CUBED_WORKFLOW, TrafficRouter


class TestEmCubedWorkflowBridge:
    """Test EmCubedWorkflowBridge DAG orchestration."""

    def test_execute_empty_workflow_dag(self):
        bridge = EmCubedWorkflowBridge()
        res = bridge.execute_workflow_dag(workflow_id="empty_wf", tasks_spec=[])

        assert res["workflow_id"] == "empty_wf"
        assert res["status"] == "empty"
        assert res["total_tasks"] == 0

    def test_execute_multi_step_surface_dag(self):
        bridge = EmCubedWorkflowBridge()
        specs = [
            {
                "task_id": "step_1",
                "skill_id": "python_surface",
                "input_data": {"code": "val = 10\nval * 2"},
            },
            {
                "task_id": "step_2",
                "skill_id": "python_surface",
                "input_data": {"code": "step_1 + 5"},
            },
        ]

        res = bridge.execute_workflow_dag(workflow_id="multi_step_dag", tasks_spec=specs)

        assert res["workflow_id"] == "multi_step_dag"
        assert res["status"] == "completed"
        assert res["total_tasks"] == 2
        assert res["final_context"]["step_1"] == 20
        assert res["final_context"]["step_2"] == 25

    def test_traffic_router_delegation(self):
        router = TrafficRouter()
        specs = [
            {
                "task_id": "t1",
                "skill_id": "python_surface",
                "input_data": {"code": "42"},
            }
        ]

        res = router.dispatch_workload(
            tool_name="execute_distributed_workflow",
            payload={"workflow_id": "tr_wf", "tasks_spec": specs},
            mode=RULE_EM_CUBED_WORKFLOW,
        )

        assert res["workflow_id"] == "tr_wf"
        assert res["status"] == "completed"
        assert res["final_context"]["t1"] == 42
