"""
    .. module:: automojo_tests.testbase.results.test_progress_status_tracking
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for progress status tracking in ResultRecorder.

    .. moduleauthor:: AutomationX
"""

import unittest
import tempfile
import os
import shutil

from datetime import datetime

from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.model.renderinfo import RenderInfo
from automojo.testbase.results.model.progressinfo import ProgressInfo
from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progresstype import ProgressType

from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder


class ProgressStatusTrackingTests(unittest.TestCase):
    """Tests for progress status tracking in ResultRecorder (Requirements 13.1-13.6)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.json"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "test-run-uuid-123"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-123",
            flavor="release",
            release="1.0.0",
            url="https://ci.example.com/build/123"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-uuid-456",
            name="CI Pipeline",
            instance="instance-uuid-789"
        )
        
        self.job_info = JobInfo(
            id="job-uuid-012",
            name="Integration Tests",
            type="TestRun",
            owner="QA Team",
            label="nightly",
            initiator="user@example.com",
            venue="staging",
            seed="12345",
            tag="correlation-tag"
        )
        
        self.recorder = JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_progress_info(self, task_id: str, status: ProgressCode) -> ProgressInfo:
        """Helper to create a ProgressInfo object with the given task ID and status."""
        return ProgressInfo(
            id=task_id,
            category="test-execution",
            moniker="test_module.test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="5",
            status=status,
            when=datetime.now(),
            data={"worker_id": "worker-1"}
        )


class CompletedStatusRemovesTaskTests(ProgressStatusTrackingTests):
    """Tests for Completed status removing task from running_tasks (Requirement 13.1)."""

    def test_completed_status_removes_task_from_running_tasks(self):
        """Test that Completed status removes the task from running_tasks (Requirement 13.1)."""
        task_id = "task-to-complete"
        
        # First add a running task
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        # Verify task is in running_tasks
        self.assertIn(task_id, self.recorder._running_tasks)
        
        # Now mark it as completed
        completed_progress = self._create_progress_info(task_id, ProgressCode.Completed)
        self.recorder.post_task_progress([completed_progress])
        
        # Verify task is removed from running_tasks
        self.assertNotIn(task_id, self.recorder._running_tasks)

    def test_completed_status_removes_only_specified_task(self):
        """Test that Completed status removes only the specified task (Requirement 13.1)."""
        task_id_1 = "task-1"
        task_id_2 = "task-2"
        
        # Add two running tasks
        running_progress_1 = self._create_progress_info(task_id_1, ProgressCode.Running)
        running_progress_2 = self._create_progress_info(task_id_2, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress_1, running_progress_2])
        
        # Verify both tasks are in running_tasks
        self.assertIn(task_id_1, self.recorder._running_tasks)
        self.assertIn(task_id_2, self.recorder._running_tasks)
        
        # Complete only task 1
        completed_progress = self._create_progress_info(task_id_1, ProgressCode.Completed)
        self.recorder.post_task_progress([completed_progress])
        
        # Verify task 1 is removed but task 2 remains
        self.assertNotIn(task_id_1, self.recorder._running_tasks)
        self.assertIn(task_id_2, self.recorder._running_tasks)


class RunningStatusUpdatesTaskTests(ProgressStatusTrackingTests):
    """Tests for Running status updating task in running_tasks (Requirement 13.2)."""

    def test_running_status_adds_task_to_running_tasks(self):
        """Test that Running status adds task to running_tasks (Requirement 13.2)."""
        task_id = "running-task"
        
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        self.assertIn(task_id, self.recorder._running_tasks)

    def test_running_status_updates_existing_task(self):
        """Test that Running status updates existing task in running_tasks (Requirement 13.2)."""
        task_id = "task-to-update"
        
        # Add initial running task
        initial_progress = ProgressInfo(
            id=task_id,
            category="test-execution",
            moniker="test_module.test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="3",
            status=ProgressCode.Running,
            when=datetime.now(),
            data={"worker_id": "worker-1"}
        )
        self.recorder.post_task_progress([initial_progress])
        
        initial_position = self.recorder._running_tasks[task_id]["position"]
        self.assertEqual(initial_position, "3")
        
        # Update with new position
        updated_progress = ProgressInfo(
            id=task_id,
            category="test-execution",
            moniker="test_module.test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="7",
            status=ProgressCode.Running,
            when=datetime.now(),
            data={"worker_id": "worker-1"}
        )
        self.recorder.post_task_progress([updated_progress])
        
        updated_position = self.recorder._running_tasks[task_id]["position"]
        self.assertEqual(updated_position, "7")

    def test_running_status_stores_task_as_dict(self):
        """Test that Running status stores task as dictionary (Requirement 13.2)."""
        task_id = "dict-task"
        
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        stored_task = self.recorder._running_tasks[task_id]
        self.assertIsInstance(stored_task, dict)
        self.assertEqual(stored_task["id"], task_id)
        self.assertEqual(stored_task["status"], "Running")


class PausedStatusUpdatesTaskTests(ProgressStatusTrackingTests):
    """Tests for Paused status updating task in running_tasks (Requirement 13.3)."""

    def test_paused_status_adds_task_to_running_tasks(self):
        """Test that Paused status adds task to running_tasks (Requirement 13.3)."""
        task_id = "paused-task"
        
        paused_progress = self._create_progress_info(task_id, ProgressCode.Paused)
        self.recorder.post_task_progress([paused_progress])
        
        self.assertIn(task_id, self.recorder._running_tasks)
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Paused")

    def test_paused_status_updates_running_task(self):
        """Test that Paused status updates a running task (Requirement 13.3)."""
        task_id = "task-to-pause"
        
        # Add running task
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Running")
        
        # Pause the task
        paused_progress = self._create_progress_info(task_id, ProgressCode.Paused)
        self.recorder.post_task_progress([paused_progress])
        
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Paused")


class NotStartedStatusUpdatesTaskTests(ProgressStatusTrackingTests):
    """Tests for NotStarted status updating task in running_tasks (Requirement 13.4)."""

    def test_notstarted_status_adds_task_to_running_tasks(self):
        """Test that NotStarted status adds task to running_tasks (Requirement 13.4)."""
        task_id = "notstarted-task"
        
        notstarted_progress = self._create_progress_info(task_id, ProgressCode.NotStarted)
        self.recorder.post_task_progress([notstarted_progress])
        
        self.assertIn(task_id, self.recorder._running_tasks)
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "NotStarted")

    def test_notstarted_status_updates_existing_task(self):
        """Test that NotStarted status updates existing task (Requirement 13.4)."""
        task_id = "task-reset"
        
        # Add running task
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        # Reset to NotStarted
        notstarted_progress = self._create_progress_info(task_id, ProgressCode.NotStarted)
        self.recorder.post_task_progress([notstarted_progress])
        
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "NotStarted")


class ErroredStatusUpdatesTaskTests(ProgressStatusTrackingTests):
    """Tests for Errored status updating task in running_tasks (Requirement 13.5)."""

    def test_errored_status_adds_task_to_running_tasks(self):
        """Test that Errored status adds task to running_tasks (Requirement 13.5)."""
        task_id = "errored-task"
        
        errored_progress = self._create_progress_info(task_id, ProgressCode.Errored)
        self.recorder.post_task_progress([errored_progress])
        
        self.assertIn(task_id, self.recorder._running_tasks)
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Errored")

    def test_errored_status_updates_running_task(self):
        """Test that Errored status updates a running task (Requirement 13.5)."""
        task_id = "task-with-error"
        
        # Add running task
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        # Mark as errored
        errored_progress = self._create_progress_info(task_id, ProgressCode.Errored)
        self.recorder.post_task_progress([errored_progress])
        
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Errored")


class FailedStatusUpdatesTaskTests(ProgressStatusTrackingTests):
    """Tests for Failed status updating task in running_tasks (Requirement 13.6)."""

    def test_failed_status_adds_task_to_running_tasks(self):
        """Test that Failed status adds task to running_tasks (Requirement 13.6)."""
        task_id = "failed-task"
        
        failed_progress = self._create_progress_info(task_id, ProgressCode.Failed)
        self.recorder.post_task_progress([failed_progress])
        
        self.assertIn(task_id, self.recorder._running_tasks)
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Failed")

    def test_failed_status_updates_running_task(self):
        """Test that Failed status updates a running task (Requirement 13.6)."""
        task_id = "task-that-failed"
        
        # Add running task
        running_progress = self._create_progress_info(task_id, ProgressCode.Running)
        self.recorder.post_task_progress([running_progress])
        
        # Mark as failed
        failed_progress = self._create_progress_info(task_id, ProgressCode.Failed)
        self.recorder.post_task_progress([failed_progress])
        
        self.assertEqual(self.recorder._running_tasks[task_id]["status"], "Failed")


class MultipleProgressUpdatesTests(ProgressStatusTrackingTests):
    """Tests for handling multiple progress updates in a single call."""

    def test_multiple_updates_in_single_call(self):
        """Test that multiple progress updates are processed in a single call."""
        progress_list = [
            self._create_progress_info("task-1", ProgressCode.Running),
            self._create_progress_info("task-2", ProgressCode.Paused),
            self._create_progress_info("task-3", ProgressCode.NotStarted),
        ]
        
        self.recorder.post_task_progress(progress_list)
        
        self.assertIn("task-1", self.recorder._running_tasks)
        self.assertIn("task-2", self.recorder._running_tasks)
        self.assertIn("task-3", self.recorder._running_tasks)
        
        self.assertEqual(self.recorder._running_tasks["task-1"]["status"], "Running")
        self.assertEqual(self.recorder._running_tasks["task-2"]["status"], "Paused")
        self.assertEqual(self.recorder._running_tasks["task-3"]["status"], "NotStarted")

    def test_mixed_updates_and_completions(self):
        """Test that mixed updates and completions are handled correctly."""
        # First add some running tasks
        initial_progress = [
            self._create_progress_info("task-a", ProgressCode.Running),
            self._create_progress_info("task-b", ProgressCode.Running),
            self._create_progress_info("task-c", ProgressCode.Running),
        ]
        self.recorder.post_task_progress(initial_progress)
        
        # Now complete one and update another
        mixed_progress = [
            self._create_progress_info("task-a", ProgressCode.Completed),
            self._create_progress_info("task-b", ProgressCode.Paused),
        ]
        self.recorder.post_task_progress(mixed_progress)
        
        self.assertNotIn("task-a", self.recorder._running_tasks)
        self.assertIn("task-b", self.recorder._running_tasks)
        self.assertIn("task-c", self.recorder._running_tasks)
        
        self.assertEqual(self.recorder._running_tasks["task-b"]["status"], "Paused")
        self.assertEqual(self.recorder._running_tasks["task-c"]["status"], "Running")


if __name__ == "__main__":
    unittest.main()
