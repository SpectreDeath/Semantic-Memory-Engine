from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from croniter import croniter

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.ScheduledJobs")

JOBS_FILE = Path(__file__).parent / "jobs.json"


class ScheduledJob:
    def __init__(
        self,
        job_id: str,
        name: str,
        schedule: str,
        action: Callable,
        enabled: bool = True,
        description: str = "",
    ):
        self.job_id = job_id
        self.name = name
        self.schedule = schedule
        self.action = action
        self.enabled = enabled
        self.description = description
        self.last_run = None
        self.next_run = None
        self._cron = None
        self._init_cron()

    def _init_cron(self):
        try:
            self._cron = croniter(self.schedule, datetime.now())
            self.next_run = self._cron.get_next(datetime)
        except Exception as e:
            logger.exception(f"Invalid cron expression for {self.name}: {e}")
            self._cron = None

    def should_run(self) -> bool:
        if not self.enabled or not self._cron:
            return False
        return datetime.now() >= self.next_run

    def mark_run(self):
        self.last_run = datetime.now()
        if self._cron:
            self.next_run = self._cron.get_next(datetime)

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "schedule": self.schedule,
            "enabled": self.enabled,
            "description": self.description,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
        }


class JobScheduler:
    def __init__(self):
        self.jobs: dict[str, ScheduledJob] = {}
        self._running = False
        self._task: asyncio.Task | None = None
        self._load_jobs()

    def _load_jobs(self):
        if JOBS_FILE.exists():
            try:
                with open(JOBS_FILE) as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} scheduled jobs")
            except Exception as e:
                logger.exception(f"Failed to load jobs: {e}")

    def _save_jobs(self):
        data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
        with open(JOBS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def register(
        self,
        name: str,
        schedule: str,
        action: Callable,
        enabled: bool = True,
        description: str = "",
    ) -> str:
        job_id = f"job_{len(self.jobs) + 1}"
        job = ScheduledJob(job_id, name, schedule, action, enabled, description)
        self.jobs[job_id] = job
        self._save_jobs()
        logger.info(f"Registered job: {name} (next run: {job.next_run})")
        return job_id

    def unregister(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            return True
        return False

    def list_jobs(self) -> list[dict]:
        return [job.to_dict() for job in self.jobs.values()]

    def enable(self, job_id: str) -> bool:
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            self._save_jobs()
            return True
        return False

    def disable(self, job_id: str) -> bool:
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            self._save_jobs()
            return True
        return False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Job scheduler started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Job scheduler stopped")

    async def _run_loop(self):
        while self._running:
            for job in self.jobs.values():
                if job.should_run():
                    logger.info(f"Running job: {job.name}")
                    try:
                        if asyncio.iscoroutinefunction(job.action):
                            await job.action()
                        else:
                            job.action()
                        job.mark_run()
                        self._save_jobs()
                    except Exception as e:
                        logger.exception(f"Job {job.name} failed: {e}")
            await asyncio.sleep(10)

    def get_next_runs(self) -> list[dict]:
        runs = []
        for job in self.jobs.values():
            if job.next_run:
                runs.append(
                    {"job_id": job.job_id, "name": job.name, "next_run": job.next_run.isoformat()}
                )
        return sorted(runs, key=lambda x: x["next_run"])


class ScheduledJobsExtension(BasePlugin):
    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.scheduler = JobScheduler()

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Scheduled Jobs extension activated")
        await self.scheduler.start()
        # Register default jobs
        self._register_default_jobs()

    def _register_default_jobs(self):
        # Example: Daily knowledge graph cleanup
        self.scheduler.register(
            name="Daily cleanup",
            schedule="0 2 * * *",  # 2 AM daily
            action=lambda: logger.info("Running daily cleanup"),
            description="Clean up temporary files daily at 2 AM",
        )

    async def on_shutdown(self):
        await self.scheduler.stop()
        logger.info(f"[{self.plugin_id}] Scheduled Jobs shutting down")

    def get_tools(self):
        return [
            self.register_job,
            self.unregister_job,
            self.list_jobs,
            self.enable_job,
            self.disable_job,
            self.get_next_runs,
            self.run_job_now,
        ]

    async def register_job(
        self,
        name: str,
        schedule: str,
        description: str = "",
    ) -> str:
        """Register a new scheduled job."""

        def job_action():
            logger.info(f"Executing job: {name}")

        job_id = self.scheduler.register(name, schedule, job_action, True, description)
        return json.dumps({"job_id": job_id, "status": "registered"})

    async def unregister_job(self, job_id: str) -> str:
        """Unregister a scheduled job."""
        success = self.scheduler.unregister(job_id)
        return json.dumps({"job_id": job_id, "status": "unregistered" if success else "not_found"})

    async def list_jobs(self) -> str:
        """List all scheduled jobs."""
        return json.dumps({"jobs": self.scheduler.list_jobs()})

    async def enable_job(self, job_id: str) -> str:
        """Enable a scheduled job."""
        success = self.scheduler.enable(job_id)
        return json.dumps({"job_id": job_id, "status": "enabled" if success else "not_found"})

    async def disable_job(self, job_id: str) -> str:
        """Disable a scheduled job."""
        success = self.scheduler.disable(job_id)
        return json.dumps({"job_id": job_id, "status": "disabled" if success else "not_found"})

    async def get_next_runs(self) -> str:
        """Get next scheduled run times."""
        return json.dumps({"next_runs": self.scheduler.get_next_runs()})

    async def run_job_now(self, job_id: str) -> str:
        """Manually trigger a job immediately."""
        if job_id in self.scheduler.jobs:
            job = self.scheduler.jobs[job_id]
            try:
                if asyncio.iscoroutinefunction(job.action):
                    await job.action()
                else:
                    job.action()
                job.mark_run()
                self.scheduler._save_jobs()
                return json.dumps({"job_id": job_id, "status": "executed"})
            except Exception as e:
                return json.dumps({"job_id": job_id, "status": "error", "error": str(e)})
        return json.dumps({"job_id": job_id, "status": "not_found"})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return ScheduledJobsExtension(manifest, nexus_api)
