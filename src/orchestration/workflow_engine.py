"""
🔧 SME Workflow Engine
=====================
A flexible workflow orchestration system for SME.
Enables chaining skills/tools into executable workflows with state management,
error handling, and parallel execution support.

Usage:
    engine = WorkflowEngine()
    workflow = engine.create_workflow("research_topic", steps=[...])
    result = engine.execute(workflow, {"topic": "AI ethics"})
"""

import asyncio
import json
import logging
import sqlite3
import uuid
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WorkflowEngine")

DB_PATH = Config().get_path("storage.db_path")


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """A single step in a workflow."""

    def __init__(
        self,
        step_id: str,
        name: str,
        handler: Callable,
        params: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
        retry: int = 0,
        timeout: int = 300,
    ):
        self.step_id = step_id
        self.name = name
        self.handler = handler
        self.params = params or {}
        self.depends_on = depends_on or []
        self.retry = retry
        self.timeout = timeout
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None


class Workflow:
    """A collection of steps that execute in sequence or parallel."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        steps: list[WorkflowStep],
        parallel: bool = False,
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps
        self.parallel = parallel
        self.status = WorkflowStatus.CREATED
        self.context: dict[str, Any] = {}


class WorkflowEngine:
    """Core workflow execution engine."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH
        self._init_db()
        self._step_registry: dict[str, Callable] = {}

    def _init_db(self):
        """Initialize workflow database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                definition TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id TEXT PRIMARY KEY,
                workflow_id TEXT,
                status TEXT,
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                FOREIGN KEY(workflow_id) REFERENCES workflows(workflow_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_steps (
                step_id TEXT PRIMARY KEY,
                run_id TEXT,
                step_order INTEGER,
                name TEXT,
                status TEXT,
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                FOREIGN KEY(run_id) REFERENCES workflow_runs(run_id)
            )
        """)

        conn.commit()
        conn.close()

    def register_step(self, step_name: str, handler: Callable):
        """Register a step handler."""
        self._step_registry[step_name] = handler

    def create_workflow(
        self,
        name: str,
        description: str = "",
        steps: list[dict[str, Any]] | None = None,
        parallel: bool = False,
    ) -> Workflow:
        """Create a new workflow definition."""
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        workflow_steps = []

        if steps:
            for step_def in steps:
                step = WorkflowStep(
                    step_id=step_def.get("id", f"step_{len(workflow_steps)}"),
                    name=step_def["name"],
                    handler=self._step_registry.get(step_def["handler"]),
                    params=step_def.get("params", {}),
                    depends_on=step_def.get("depends_on", []),
                    retry=step_def.get("retry", 0),
                    timeout=step_def.get("timeout", 300),
                )
                workflow_steps.append(step)

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
            parallel=parallel,
        )

        self._save_workflow(workflow)
        return workflow

    def _save_workflow(self, workflow: Workflow):
        """Save workflow to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        definition = {
            "steps": [
                {
                    "id": s.step_id,
                    "name": s.name,
                    "handler": s.name,
                    "params": s.params,
                    "depends_on": s.depends_on,
                    "retry": s.retry,
                    "timeout": s.timeout,
                }
                for s in workflow.steps
            ],
            "parallel": workflow.parallel,
        }

        cursor.execute(
            """
            INSERT OR REPLACE INTO workflows (workflow_id, name, description, definition, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                workflow.workflow_id,
                workflow.name,
                workflow.description,
                json.dumps(definition),
                datetime.now(),
            ),
        )

        conn.commit()
        conn.close()

    async def execute(self, workflow: Workflow, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a workflow with input data."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        workflow.context = {"input": input_data, "steps": {}}

        logger.info(f"Starting workflow execution: {workflow.name} ({run_id})")
        workflow.status = WorkflowStatus.RUNNING

        self._save_run(run_id, workflow, input_data)

        try:
            if workflow.parallel:
                result = await self._execute_parallel(workflow)
            else:
                result = await self._execute_sequential(workflow)

            workflow.status = WorkflowStatus.COMPLETED
            self._update_run(run_id, "completed", result)

            return {
                "run_id": run_id,
                "status": "completed",
                "result": result,
            }

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            logger.exception(f"Workflow failed: {e}")
            self._update_run(run_id, "failed", None, str(e))

            return {
                "run_id": run_id,
                "status": "failed",
                "error": str(e),
            }

    async def _execute_sequential(self, workflow: Workflow) -> dict[str, Any]:
        """Execute steps sequentially."""
        for step in workflow.steps:
            if not self._can_execute(step, workflow.context):
                step.status = StepStatus.SKIPPED
                continue

            result = await self._execute_step(step, workflow.context)
            workflow.context["steps"][step.step_id] = result

            if step.status == StepStatus.FAILED:
                raise Exception(f"Step {step.name} failed: {step.error}")

        return workflow.context.get("steps", {})

    async def _execute_parallel(self, workflow: Workflow) -> dict[str, Any]:
        """Execute independent steps in parallel."""
        completed = {}
        pending = workflow.steps.copy()

        while pending:
            ready = [s for s in pending if self._can_execute(s, workflow.context)]

            if not ready:
                if pending:
                    raise Exception("Circular dependency or blocked steps")
                break

            tasks = [self._execute_step(s, workflow.context) for s in ready]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for step, result in zip(ready, results, strict=True):
                if isinstance(result, Exception):
                    step.status = StepStatus.FAILED
                    step.error = str(result)
                    raise result

                workflow.context["steps"][step.step_id] = result
                completed[step.step_id] = result
                pending.remove(step)

        return completed

    def _can_execute(self, step: WorkflowStep, context: dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied."""
        for dep in step.depends_on:
            if dep not in context.get("steps", {}):
                return False
            dep_step = next(
                (s for s in context.get("steps", {}).values() if s.step_id == dep), None
            )
            if dep_step and dep_step.status == StepStatus.FAILED:
                return False
        return True

    async def _execute_step(self, step: WorkflowStep, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single step."""
        logger.info(f"Executing step: {step.name}")
        step.status = StepStatus.RUNNING

        self._save_step(step, context.get("input", {}), "running")

        try:
            if step.handler:
                resolved_params = self._resolve_params(step.params, context)
                result = await asyncio.wait_for(
                    asyncio.to_thread(step.handler, **resolved_params),
                    timeout=step.timeout,
                )
            else:
                result = {"status": "no_handler", "message": "Step has no handler"}

            step.status = StepStatus.COMPLETED
            step.result = result
            self._save_step(step, context.get("input", {}), "completed", result)

            return result

        except TimeoutError:
            step.status = StepStatus.FAILED
            step.error = f"Timeout after {step.timeout}s"
            self._save_step(step, context.get("input", {}), "failed", None, step.error)
            raise Exception(step.error)

        except Exception as e:
            if step.retry > 0:
                logger.warning(f"Step failed, retrying ({step.retry} left): {e}")
                step.retry -= 0
                return await self._execute_step(step, context)

            step.status = StepStatus.FAILED
            step.error = str(e)
            self._save_step(step, context.get("input", {}), "failed", None, str(e))
            raise

    def _resolve_params(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Resolve parameter references in context."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                ref = value[1:]
                resolved[key] = context.get("steps", {}).get(ref, {}).get("result", {})
            else:
                resolved[key] = value
        return resolved

    def _save_run(self, run_id: str, workflow: Workflow, input_data: dict):
        """Save workflow run to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO workflow_runs (run_id, workflow_id, status, input_data, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                workflow.workflow_id,
                "running",
                json.dumps(input_data),
                datetime.now(),
            ),
        )

        conn.commit()
        conn.close()

    def _update_run(
        self, run_id: str, status: str, output: dict | None = None, error: str | None = None
    ):
        """Update workflow run status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE workflow_runs
            SET status = ?, output_data = ?, error_message = ?, completed_at = ?
            WHERE run_id = ?
            """,
            (status, json.dumps(output) if output else None, error, datetime.now(), run_id),
        )

        conn.commit()
        conn.close()

    def _save_step(
        self,
        step: WorkflowStep,
        input_data: dict,
        status: str,
        output: dict | None = None,
        error: str | None = None,
    ):
        """Save step execution to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO workflow_steps (step_id, run_id, name, status, input_data, output_data, error_message, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                step.step_id,
                f"run_{step.step_id.split('_')[-1]}",
                step.name,
                status,
                json.dumps(input_data),
                json.dumps(output) if output else None,
                error,
                datetime.now(),
                datetime.now(),
            ),
        )

        conn.commit()
        conn.close()

    def list_workflows(self) -> list[dict[str, Any]]:
        """List all saved workflows."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT workflow_id, name, description, created_at FROM workflows ORDER BY created_at DESC"
        )

        results = cursor.fetchall()
        conn.close()

        return [
            {
                "workflow_id": r[0],
                "name": r[1],
                "description": r[2],
                "created_at": r[3],
            }
            for r in results
        ]

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT workflow_id, name, description, definition FROM workflows WHERE workflow_id = ?",
            (workflow_id,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "workflow_id": result[0],
                "name": result[1],
                "description": result[2],
                "definition": json.loads(result[3]),
            }
        return None


def get_engine() -> WorkflowEngine:
    """Get a WorkflowEngine instance."""
    return WorkflowEngine()
