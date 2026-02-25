"""
    .. module:: automojo_tests.testbase.results.test_thread_safety
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for thread safety in ResultRecorder and JsonResultRecorder.

    .. moduleauthor:: AutomationX
"""

import unittest
import tempfile
import os
import shutil
import threading
import time
import concurrent.futures

from datetime import datetime

from automojo.testbase.results.model.buildinfo import BuildInfo
from automojo.testbase.results.model.pipelineinfo import PipelineInfo
from automojo.testbase.results.model.jobinfo import JobInfo
from automojo.testbase.results.model.renderinfo import RenderInfo
from automojo.testbase.results.model.resultcode import ResultCode
from automojo.testbase.results.model.resulttype import ResultType
from automojo.testbase.results.model.testresult import TestResult
from automojo.testbase.results.model.progressinfo import ProgressInfo
from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progresstype import ProgressType

from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder


class ThreadSafetyTestBase(unittest.TestCase):
    """Base class for thread safety tests with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.render_info = RenderInfo(
            title="Thread Safety Test Run",
            summary_filename=os.path.join(self.temp_dir, "summary.json"),
            summary_template=os.path.join(self.temp_dir, "template.html"),
            stream_results_filename=os.path.join(self.temp_dir, "results.jsos"),
            consolidated_results_filename=os.path.join(self.temp_dir, "consolidated.json"),
            static_resource_source=None,
            static_resource_destination=self.temp_dir
        )
        
        # Create a dummy template file
        with open(self.render_info.summary_template, 'w') as f:
            f.write("<html></html>")
        
        self.runid = "thread-safety-test-uuid"
        self.start = datetime.now()
        
        self.build_info = BuildInfo(
            branch="main",
            build="build-thread-safety",
            flavor="test",
            release="1.0.0",
            url="https://ci.example.com/build/thread-safety"
        )
        
        self.pipeline_info = PipelineInfo(
            id="pipeline-thread-safety",
            name="Thread Safety Pipeline",
            instance="thread-safety-instance"
        )
        
        self.job_info = JobInfo(
            id="job-thread-safety",
            name="Thread Safety Tests",
            type="TestRun",
            owner="Test Team",
            label="thread-safety",
            initiator="test@example.com",
            venue="test-env",
            seed="12345",
            tag="thread-safety-tag"
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_recorder(self):
        """Helper to create a JsonResultRecorder."""
        return JsonResultRecorder(
            runid=self.runid,
            start=self.start,
            render_info=self.render_info,
            build_info=self.build_info,
            pipeline_info=self.pipeline_info,
            job_info=self.job_info
        )

    def _create_test_result(self, inst_id: str, result_code: ResultCode = ResultCode.PASSED):
        """Helper to create a TestResult."""
        result = TestResult(
            inst_id=inst_id,
            name=f"test_{inst_id}",
            parent_inst="parent-1",
            monikers=[],
            pivots={},
            result_code=ResultCode.UNSET
        )
        if result_code == ResultCode.PASSED:
            result.mark_passed()
        result.finalize()
        return result

    def _create_progress_info(self, task_id: str, status: ProgressCode) -> ProgressInfo:
        """Helper to create a ProgressInfo object."""
        return ProgressInfo(
            id=task_id,
            category="test-execution",
            moniker=f"test_module.{task_id}",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="5",
            status=status,
            when=datetime.now(),
            data={"worker_id": "worker-1"}
        )


class ConcurrentRecordCallsTests(ThreadSafetyTestBase):
    """Tests for concurrent record calls (Requirement 41.6)."""

    def test_concurrent_record_calls_maintain_accurate_counts(self):
        """Test that concurrent record calls maintain accurate result counts (Requirement 41.6)."""
        recorder = self._create_recorder()
        num_threads = 10
        results_per_thread = 5
        total_expected = num_threads * results_per_thread
        
        with recorder:
            def record_results(thread_id):
                for i in range(results_per_thread):
                    result = self._create_test_result(f"test-{thread_id}-{i}")
                    recorder.record(result)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(record_results, tid) for tid in range(num_threads)]
                concurrent.futures.wait(futures)
        
        self.assertEqual(recorder._total_count, total_expected)
        self.assertEqual(recorder._pass_count, total_expected)

    def test_concurrent_record_calls_do_not_corrupt_counters(self):
        """Test that concurrent record calls do not corrupt counter values (Requirement 41.6)."""
        recorder = self._create_recorder()
        num_threads = 20
        results_per_thread = 10
        
        with recorder:
            def record_results(thread_id):
                for i in range(results_per_thread):
                    result = self._create_test_result(f"test-{thread_id}-{i}")
                    recorder.record(result)
            
            threads = []
            for tid in range(num_threads):
                t = threading.Thread(target=record_results, args=(tid,))
                threads.append(t)
            
            for t in threads:
                t.start()
            
            for t in threads:
                t.join()
        
        # Verify counters are consistent
        self.assertEqual(recorder._total_count, recorder._pass_count)
        self.assertEqual(recorder._error_count, 0)
        self.assertEqual(recorder._failure_count, 0)
        self.assertEqual(recorder._skip_count, 0)
        self.assertEqual(recorder._unknown_count, 0)


class ConcurrentProgressUpdatesTests(ThreadSafetyTestBase):
    """Tests for concurrent progress updates (Requirement 41.3)."""

    def test_concurrent_progress_updates_maintain_consistency(self):
        """Test that concurrent progress updates maintain running_tasks consistency (Requirement 41.3)."""
        recorder = self._create_recorder()
        num_threads = 10
        updates_per_thread = 5
        
        def post_progress(thread_id):
            for i in range(updates_per_thread):
                task_id = f"task-{thread_id}-{i}"
                progress = self._create_progress_info(task_id, ProgressCode.Running)
                recorder.post_task_progress([progress])
        
        threads = []
        for tid in range(num_threads):
            t = threading.Thread(target=post_progress, args=(tid,))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # All tasks should be in running_tasks
        expected_tasks = num_threads * updates_per_thread
        self.assertEqual(len(recorder._running_tasks), expected_tasks)

    def test_concurrent_progress_updates_and_completions(self):
        """Test that concurrent progress updates and completions are handled correctly (Requirement 41.3)."""
        recorder = self._create_recorder()
        num_tasks = 50
        
        # First add all tasks as running
        for i in range(num_tasks):
            progress = self._create_progress_info(f"task-{i}", ProgressCode.Running)
            recorder.post_task_progress([progress])
        
        self.assertEqual(len(recorder._running_tasks), num_tasks)
        
        # Now concurrently complete half and update the other half
        def complete_task(task_id):
            progress = self._create_progress_info(task_id, ProgressCode.Completed)
            recorder.post_task_progress([progress])
        
        def update_task(task_id):
            progress = self._create_progress_info(task_id, ProgressCode.Paused)
            recorder.post_task_progress([progress])
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(num_tasks):
                if i % 2 == 0:
                    futures.append(executor.submit(complete_task, f"task-{i}"))
                else:
                    futures.append(executor.submit(update_task, f"task-{i}"))
            concurrent.futures.wait(futures)
        
        # Half should be completed (removed), half should be paused
        self.assertEqual(len(recorder._running_tasks), num_tasks // 2)
        for task_id, task_data in recorder._running_tasks.items():
            self.assertEqual(task_data["status"], "Paused")


class ConcurrentClearTaskProgressTests(ThreadSafetyTestBase):
    """Tests for concurrent clear_task_progress calls (Requirement 41.4)."""

    def test_concurrent_clear_task_progress_removes_tasks(self):
        """Test that concurrent clear_task_progress calls correctly remove tasks (Requirement 41.4)."""
        recorder = self._create_recorder()
        num_tasks = 100
        
        # Add all tasks
        for i in range(num_tasks):
            progress = self._create_progress_info(f"task-{i}", ProgressCode.Running)
            recorder.post_task_progress([progress])
        
        self.assertEqual(len(recorder._running_tasks), num_tasks)
        
        # Concurrently clear tasks in batches
        def clear_batch(start, end):
            task_ids = [f"task-{i}" for i in range(start, end)]
            recorder.clear_task_progress(task_ids)
        
        batch_size = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for start in range(0, num_tasks, batch_size):
                end = min(start + batch_size, num_tasks)
                futures.append(executor.submit(clear_batch, start, end))
            concurrent.futures.wait(futures)
        
        # All tasks should be cleared
        self.assertEqual(len(recorder._running_tasks), 0)


class LockAcquisitionAndReleaseTests(ThreadSafetyTestBase):
    """Tests for lock acquisition and release patterns (Requirements 41.1-41.6)."""

    def test_lock_is_threading_lock(self):
        """Test that ResultRecorder uses threading.Lock (Requirement 41.1)."""
        recorder = self._create_recorder()
        self.assertIsInstance(recorder._lock, type(threading.Lock()))

    def test_summary_property_acquires_lock(self):
        """Test that summary property acquires lock before copying (Requirement 41.2)."""
        recorder = self._create_recorder()
        
        # Acquire the lock manually
        recorder._lock.acquire()
        
        # Try to get summary in another thread - should block
        summary_result = [None]
        summary_acquired = threading.Event()
        
        def get_summary():
            summary_result[0] = recorder.summary
            summary_acquired.set()
        
        t = threading.Thread(target=get_summary)
        t.start()
        
        # Give the thread time to attempt lock acquisition
        time.sleep(0.1)
        
        # Summary should not have been acquired yet
        self.assertFalse(summary_acquired.is_set())
        
        # Release the lock
        recorder._lock.release()
        
        # Now summary should be acquired
        t.join(timeout=1.0)
        self.assertTrue(summary_acquired.is_set())
        self.assertIsNotNone(summary_result[0])

    def test_post_task_progress_acquires_lock(self):
        """Test that post_task_progress acquires lock (Requirement 41.3)."""
        recorder = self._create_recorder()
        
        # Acquire the lock manually
        recorder._lock.acquire()
        
        # Try to post progress in another thread - should block
        progress_posted = threading.Event()
        
        def post_progress():
            progress = self._create_progress_info("test-task", ProgressCode.Running)
            recorder.post_task_progress([progress])
            progress_posted.set()
        
        t = threading.Thread(target=post_progress)
        t.start()
        
        # Give the thread time to attempt lock acquisition
        time.sleep(0.1)
        
        # Progress should not have been posted yet
        self.assertFalse(progress_posted.is_set())
        
        # Release the lock
        recorder._lock.release()
        
        # Now progress should be posted
        t.join(timeout=1.0)
        self.assertTrue(progress_posted.is_set())
        self.assertIn("test-task", recorder._running_tasks)

    def test_clear_task_progress_acquires_lock(self):
        """Test that clear_task_progress acquires lock (Requirement 41.4)."""
        recorder = self._create_recorder()
        
        # Add a task first
        progress = self._create_progress_info("task-to-clear", ProgressCode.Running)
        recorder.post_task_progress([progress])
        
        # Acquire the lock manually
        recorder._lock.acquire()
        
        # Try to clear progress in another thread - should block
        progress_cleared = threading.Event()
        
        def clear_progress():
            recorder.clear_task_progress(["task-to-clear"])
            progress_cleared.set()
        
        t = threading.Thread(target=clear_progress)
        t.start()
        
        # Give the thread time to attempt lock acquisition
        time.sleep(0.1)
        
        # Progress should not have been cleared yet
        self.assertFalse(progress_cleared.is_set())
        self.assertIn("task-to-clear", recorder._running_tasks)
        
        # Release the lock
        recorder._lock.release()
        
        # Now progress should be cleared
        t.join(timeout=1.0)
        self.assertTrue(progress_cleared.is_set())
        self.assertNotIn("task-to-clear", recorder._running_tasks)

    def test_finalize_acquires_lock(self):
        """Test that finalize acquires lock (Requirement 41.5)."""
        recorder = self._create_recorder()
        recorder.__enter__()
        
        # Acquire the lock manually
        recorder._lock.acquire()
        
        # Try to finalize in another thread - should block
        finalize_completed = threading.Event()
        
        def do_finalize():
            recorder.finalize()
            finalize_completed.set()
        
        t = threading.Thread(target=do_finalize)
        t.start()
        
        # Give the thread time to attempt lock acquisition
        time.sleep(0.1)
        
        # Finalize should not have completed yet
        self.assertFalse(finalize_completed.is_set())
        self.assertFalse(recorder._finalized)
        
        # Release the lock
        recorder._lock.release()
        
        # Now finalize should complete
        t.join(timeout=1.0)
        self.assertTrue(finalize_completed.is_set())
        self.assertTrue(recorder._finalized)

    def test_record_acquires_lock(self):
        """Test that record acquires lock before updating counters (Requirement 41.6)."""
        recorder = self._create_recorder()
        recorder.__enter__()
        
        # Acquire the lock manually
        recorder._lock.acquire()
        
        # Try to record in another thread - should block at counter update
        record_completed = threading.Event()
        initial_count = recorder._total_count
        
        def do_record():
            result = self._create_test_result("test-lock")
            recorder.record(result)
            record_completed.set()
        
        t = threading.Thread(target=do_record)
        t.start()
        
        # Give the thread time to attempt lock acquisition
        time.sleep(0.1)
        
        # Record should not have completed counter update yet
        self.assertFalse(record_completed.is_set())
        
        # Release the lock
        recorder._lock.release()
        
        # Now record should complete
        t.join(timeout=1.0)
        self.assertTrue(record_completed.is_set())
        self.assertEqual(recorder._total_count, initial_count + 1)
        
        # Clean up
        recorder.finalize()


class ConcurrentRecordAndFinalizeTests(ThreadSafetyTestBase):
    """Tests for concurrent record and finalize operations."""

    def test_concurrent_record_and_finalize(self):
        """Test that concurrent record and finalize operations are handled safely."""
        recorder = self._create_recorder()
        recorder.__enter__()
        
        num_records = 20
        records_completed = [0]
        records_lock = threading.Lock()
        
        def record_result(idx):
            try:
                result = self._create_test_result(f"test-{idx}")
                recorder.record(result)
                with records_lock:
                    records_completed[0] += 1
            except Exception:
                pass  # May fail if finalize closes the file first
        
        # Start recording threads
        threads = []
        for i in range(num_records):
            t = threading.Thread(target=record_result, args=(i,))
            threads.append(t)
            t.start()
        
        # Give some time for records to start
        time.sleep(0.05)
        
        # Finalize while records are being written
        recorder.finalize()
        
        # Wait for all threads
        for t in threads:
            t.join(timeout=1.0)
        
        # Recorder should be finalized
        self.assertTrue(recorder._finalized)


class ConcurrentSummaryAccessTests(ThreadSafetyTestBase):
    """Tests for concurrent summary access."""

    def test_concurrent_summary_reads_return_consistent_data(self):
        """Test that concurrent summary reads return consistent snapshots."""
        recorder = self._create_recorder()
        num_readers = 10
        reads_per_thread = 20
        
        summaries = []
        summaries_lock = threading.Lock()
        
        def read_summary():
            for _ in range(reads_per_thread):
                summary = recorder.summary
                with summaries_lock:
                    summaries.append(summary)
        
        threads = []
        for _ in range(num_readers):
            t = threading.Thread(target=read_summary)
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # All summaries should have the same runid
        for summary in summaries:
            self.assertEqual(summary["runid"], self.runid)

    def test_summary_returns_independent_copies(self):
        """Test that summary property returns independent copies."""
        recorder = self._create_recorder()
        
        summary1 = recorder.summary
        summary2 = recorder.summary
        
        # Modify summary1
        summary1["runid"] = "modified"
        
        # summary2 and internal summary should be unchanged
        self.assertEqual(summary2["runid"], self.runid)
        self.assertEqual(recorder._summary["runid"], self.runid)


if __name__ == "__main__":
    unittest.main()
