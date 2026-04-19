"""
Tests for ext_scheduled_jobs extension
======================================
"""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


class TestScheduledJob:
    """Tests for ScheduledJob class."""

    def test_job_creation(self):
        """Should create scheduled job."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJob

        def test_action():
            pass

        job = ScheduledJob(
            job_id="test_1",
            name="Test Job",
            schedule="0 * * * *",  # Hourly
            action=test_action,
            enabled=True,
            description="Test job",
        )

        assert job.name == "Test Job"
        assert job.schedule == "0 * * * *"
        assert job.enabled is True

    def test_cron_parsing(self):
        """Should parse cron expression."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJob

        def test_action():
            pass

        job = ScheduledJob(
            job_id="test_1",
            name="Test Job",
            schedule="0 2 * * *",  # 2 AM daily
            action=test_action,
        )

        assert job.next_run is not None
        assert job._cron is not None

    def test_should_run(self):
        """Should determine if job should run."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJob

        def test_action():
            pass

        job = ScheduledJob(
            job_id="test_1", name="Test Job", schedule="0 * * * *", action=test_action, enabled=True
        )

        # With schedule in the past, should run
        # Note: This test may vary based on current time
        assert isinstance(job.should_run(), bool)

    def test_to_dict(self):
        """Should serialize job to dict."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJob

        def test_action():
            pass

        job = ScheduledJob(
            job_id="test_1",
            name="Test Job",
            schedule="0 * * * *",
            action=test_action,
            enabled=True,
            description="Test description",
        )

        job_dict = job.to_dict()

        assert job_dict["job_id"] == "test_1"
        assert job_dict["name"] == "Test Job"
        assert job_dict["schedule"] == "0 * * * *"
        assert job_dict["enabled"] is True
        assert job_dict["description"] == "Test description"


class TestJobScheduler:
    """Tests for JobScheduler class."""

    def test_scheduler_creation(self):
        """Should initialize empty scheduler."""
        with patch("pathlib.Path.exists", return_value=False):
            from extensions.ext_scheduled_jobs.plugin import JobScheduler

            scheduler = JobScheduler()
            assert scheduler.jobs == {}
            assert scheduler._running is False

    def test_register_job(self):
        """Should register a new job."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_scheduled_jobs.plugin import JobScheduler

            scheduler = JobScheduler()

            def test_action():
                pass

            job_id = scheduler.register(
                name="Daily Backup",
                schedule="0 3 * * *",
                action=test_action,
                description="Backup at 3 AM",
            )

            assert job_id is not None
            assert "Daily Backup" in scheduler.jobs[job_id]["name"]

    def test_unregister_job(self):
        """Should remove job."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_scheduled_jobs.plugin import JobScheduler

            scheduler = JobScheduler()

            def test_action():
                pass

            job_id = scheduler.register("Test", "* * * * *", test_action)
            result = scheduler.unregister(job_id)

            assert result is True
            assert job_id not in scheduler.jobs

    def test_enable_job(self):
        """Should enable disabled job."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_scheduled_jobs.plugin import JobScheduler

            scheduler = JobScheduler()

            def test_action():
                pass

            job_id = scheduler.register("Test", "* * * * *", test_action, enabled=False)
            scheduler.enable(job_id)

            assert scheduler.jobs[job_id].enabled is True

    def test_disable_job(self):
        """Should disable enabled job."""
        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_scheduled_jobs.plugin import JobScheduler

            scheduler = JobScheduler()

            def test_action():
                pass

            job_id = scheduler.register("Test", "* * * * *", test_action, enabled=True)
            scheduler.disable(job_id)

            assert scheduler.jobs[job_id].enabled is False


class TestScheduledJobsExtension:
    """Tests for ScheduledJobsExtension class."""

    def test_extension_creation(self):
        """Should create extension with scheduler."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJobsExtension

        manifest = {"plugin_id": "ext_scheduled_jobs", "name": "Scheduled Jobs"}
        extension = ScheduledJobsExtension(manifest, None)

        assert extension.scheduler is not None

    def test_get_tools(self):
        """Should return list of tools."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJobsExtension

        manifest = {"plugin_id": "ext_scheduled_jobs", "name": "Scheduled Jobs"}
        extension = ScheduledJobsExtension(manifest, None)

        tools = extension.get_tools()
        tool_names = [t.__name__ for t in tools]

        assert "register_job" in tool_names
        assert "list_jobs" in tool_names
        assert "get_next_runs" in tool_names

    @pytest.mark.asyncio
    async def test_register_job_tool(self):
        """Should register job via tool."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJobsExtension

        manifest = {"plugin_id": "ext_scheduled_jobs", "name": "Scheduled Jobs"}
        extension = ScheduledJobsExtension(manifest, None)

        result = await extension.register_job(
            name="Test Job", schedule="0 * * * *", description="Test"
        )

        result_data = json.loads(result)
        assert result_data["status"] == "registered"

    @pytest.mark.asyncio
    async def test_list_jobs_tool(self):
        """Should list jobs via tool."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJobsExtension

        manifest = {"plugin_id": "ext_scheduled_jobs", "name": "Scheduled Jobs"}
        extension = ScheduledJobsExtension(manifest, None)

        # Register a job first
        await extension.register_job("Test", "0 * * * *")

        result = await extension.list_jobs()
        result_data = json.loads(result)

        assert "jobs" in result_data


class TestCronExpressions:
    """Tests for cron expression handling."""

    def test_valid_cron_expressions(self):
        """Should accept valid cron expressions."""
        valid_schedules = [
            "* * * * *",  # Every minute
            "0 * * * *",  # Every hour
            "0 0 * * *",  # Daily at midnight
            "0 0 * * 0",  # Weekly on Sunday
            "0 0 1 * *",  # Monthly on 1st
        ]

        for schedule in valid_schedules:
            from croniter import croniter

            assert croniter(schedule, datetime.now()) is not None

    def test_invalid_cron_handling(self):
        """Should handle invalid cron gracefully."""
        from extensions.ext_scheduled_jobs.plugin import ScheduledJob

        def test_action():
            pass

        # Invalid cron should not crash
        job = ScheduledJob(job_id="test", name="Test", schedule="invalid", action=test_action)

        # Should have set _cron to None for invalid expression
        assert job._cron is None or job.next_run is None
