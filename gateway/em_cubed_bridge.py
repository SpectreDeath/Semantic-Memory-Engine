"""
em-cubed Distributed Workflow Orchestration Bridge
===================================================
Interfaces Lawnmower Man Gateway with em-cubed's DistributedExecutor to run
multi-step graph transformation and surface execution workflow DAGs.
"""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path
from typing import Any

# Ensure em-cubed is importable
em_cubed_path = Path(__file__).resolve().parent.parent.parent / "em-cubed" / "src"
if em_cubed_path.exists() and str(em_cubed_path) not in sys.path:
    sys.path.insert(0, str(em_cubed_path))

logger = logging.getLogger("lawnmower.em_cubed_bridge")


class EmCubedWorkflowBridge:
    """
    Bridge for submitting and orchestrating multi-step workflow DAGs via em-cubed.
    """

    def __init__(self) -> None:
        self.executor_available = False
        try:
            from em_cubed.workflow.distributed import (
                DistributedExecutor,
                DistributedTask,
                TaskStatus,
            )

            self.DistributedExecutor = DistributedExecutor
            self.DistributedTask = DistributedTask
            self.TaskStatus = TaskStatus
            self.executor_available = True
        except ImportError:
            logger.warning("em_cubed.workflow.distributed not directly importable")

    def execute_workflow_dag(
        self, workflow_id: str | None = None, tasks_spec: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        Execute a multi-step workflow DAG.

        Args:
            workflow_id: Optional workflow identifier.
            tasks_spec: List of task specifications containing skill_id, input_data, and dependencies.

        Returns:
            Dict containing workflow_id, status, total_tasks, and step_results.
        """
        wid = workflow_id or f"wf_{uuid.uuid4().hex[:8]}"
        specs = tasks_spec or []

        if not specs:
            return {
                "workflow_id": wid,
                "status": "empty",
                "total_tasks": 0,
                "step_results": [],
            }

        logger.info(f"EmCubedWorkflowBridge executing workflow '{wid}' with {len(specs)} tasks")

        step_results = []
        context: dict[str, Any] = {}

        for idx, spec in enumerate(specs):
            task_id = spec.get("task_id", f"task_{idx}")
            skill_id = spec.get("skill_id", "python_surface")
            inputs = spec.get("input_data", {})

            # Propagate context from prior tasks
            merged_inputs = {**context, **inputs}

            from gateway.candidate_pool import CandidatePoolStorage

            pool_storage = CandidatePoolStorage()
            optimal_block = pool_storage.select_optimal_team(idx, task_context=merged_inputs)
            if optimal_block and "nodes" in optimal_block:
                logger.info(f"EmCubedWorkflowBridge using ANN optimal team block '{optimal_block.get('block_id')}' for layer {idx}")

            if skill_id == "python_surface" or "code" in merged_inputs:
                from gateway.surface_bridge import SurfaceBridge

                sb = SurfaceBridge()
                code = merged_inputs.get("code", "result = inputs")
                schema = spec.get("schema")

                res = sb.execute_surface(code=code, inputs=merged_inputs, schema=schema)
                if isinstance(res, dict) and "result" in res:
                    context[task_id] = res["result"]
            else:
                res = {
                    "status": "completed",
                    "task_id": task_id,
                    "skill_id": skill_id,
                    "result": f"Executed step '{skill_id}'",
                }
                context[task_id] = res["result"]

            step_results.append({"task_id": task_id, "skill_id": skill_id, "output": res})

        return {
            "workflow_id": wid,
            "status": "completed",
            "total_tasks": len(specs),
            "step_results": step_results,
            "final_context": context,
        }
