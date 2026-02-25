"""
    .. module:: automojo_tests.testbase.results.test_nested_progress_tracking
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for nested progress tracking in ResultRecorder.

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
from automojo.testbase.results.model.nestedprogressinfo import NestedProgressInfo
from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progresstype import ProgressType

from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultRecorder


class NestedProgressTrackingTests(unittest.TestCase):
    """Tests for nested progress tracking in ResultRecorder (Requirements 22.1-22.11, 28.1-28.6)."""

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

    def _create_nested_progress(self, progress_id: str, parent_id: str = None,
                                 status: ProgressCode = ProgressCode.Running,
                                 depth: int = 0) -> NestedProgressInfo:
        """Helper to create a NestedProgressInfo object."""
        return NestedProgressInfo(
            id=progress_id,
            category="test-execution",
            moniker=f"test_{progress_id}",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="5",
            status=status,
            when=datetime.now(),
            parent_id=parent_id,
            depth=depth
        )


class PostNestedProgressTests(NestedProgressTrackingTests):
    """Tests for post_nested_progress method (Requirements 22.1-22.11)."""

    def test_post_nested_progress_registers_progress(self):
        """Test that post_nested_progress registers progress with aggregator."""
        progress = self._create_nested_progress("test-123")
        
        result = self.recorder.post_nested_progress(progress)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "test-123")

    def test_post_nested_progress_updates_running_tasks(self):
        """Test that post_nested_progress updates running_tasks dictionary."""
        progress = self._create_nested_progress("test-123")
        
        self.recorder.post_nested_progress(progress)
        
        self.assertIn("test-123", self.recorder._running_tasks)

    def test_post_nested_progress_removes_completed_from_running_tasks(self):
        """Test that completed progress is removed from running_tasks."""
        # First add a running progress
        running_progress = self._create_nested_progress("test-123", status=ProgressCode.Running)
        self.recorder.post_nested_progress(running_progress)
        
        self.assertIn("test-123", self.recorder._running_tasks)
        
        # Now mark it as completed
        completed_progress = self._create_nested_progress("test-123", status=ProgressCode.Completed)
        self.recorder.post_nested_progress(completed_progress)
        
        self.assertNotIn("test-123", self.recorder._running_tasks)

    def test_post_nested_progress_establishes_parent_child(self):
        """Test that post_nested_progress establishes parent-child relationships."""
        parent = self._create_nested_progress("parent-123", depth=0)
        child = self._create_nested_progress("child-456", parent_id="parent-123", depth=1)
        
        self.recorder.post_nested_progress(parent)
        self.recorder.post_nested_progress(child)
        
        parent_progress = self.recorder.get_nested_progress("parent-123")
        self.assertIn("child-456", parent_progress.children_ids)


class GetAggregatedProgressTests(NestedProgressTrackingTests):
    """Tests for get_aggregated_progress method (Requirements 28.1-28.6)."""

    def test_get_aggregated_progress_returns_metrics(self):
        """Test that get_aggregated_progress returns aggregation metrics."""
        parent = self._create_nested_progress("parent-123", depth=0)
        child1 = self._create_nested_progress("child-1", parent_id="parent-123",
                                               status=ProgressCode.Completed, depth=1)
        child2 = self._create_nested_progress("child-2", parent_id="parent-123",
                                               status=ProgressCode.Running, depth=1)
        
        self.recorder.post_nested_progress(parent)
        self.recorder.post_nested_progress(child1)
        self.recorder.post_nested_progress(child2)
        
        aggregated = self.recorder.get_aggregated_progress("parent-123")
        
        self.assertIsNotNone(aggregated)
        self.assertEqual(aggregated["total_children"], 2)
        self.assertEqual(aggregated["completed_count"], 1)
        self.assertEqual(aggregated["running_count"], 1)

    def test_get_aggregated_progress_calculates_percentage(self):
        """Test that get_aggregated_progress calculates completion percentage."""
        parent = self._create_nested_progress("parent-123", depth=0)
        
        # Add 4 children: 2 completed, 2 not
        for i in range(4):
            status = ProgressCode.Completed if i < 2 else ProgressCode.Running
            child = self._create_nested_progress(f"child-{i}", parent_id="parent-123",
                                                  status=status, depth=1)
            self.recorder.post_nested_progress(child)
        
        self.recorder.post_nested_progress(parent)
        
        aggregated = self.recorder.get_aggregated_progress("parent-123")
        
        self.assertAlmostEqual(aggregated["completion_percentage"], 50.0)

    def test_get_aggregated_progress_returns_none_for_unknown(self):
        """Test that get_aggregated_progress returns None for unknown ID."""
        aggregated = self.recorder.get_aggregated_progress("nonexistent")
        
        self.assertIsNone(aggregated)


class GetProgressTreeTests(NestedProgressTrackingTests):
    """Tests for get_progress_tree method (Requirements 22.1-22.11)."""

    def test_get_progress_tree_returns_hierarchy(self):
        """Test that get_progress_tree returns hierarchical structure."""
        parent = self._create_nested_progress("parent-123", depth=0)
        child = self._create_nested_progress("child-456", parent_id="parent-123", depth=1)
        
        self.recorder.post_nested_progress(parent)
        self.recorder.post_nested_progress(child)
        
        tree = self.recorder.get_progress_tree()
        
        self.assertIn("roots", tree)
        self.assertEqual(len(tree["roots"]), 1)
        self.assertEqual(tree["roots"][0]["id"], "parent-123")
        self.assertEqual(len(tree["roots"][0]["children"]), 1)

    def test_get_progress_tree_includes_total_count(self):
        """Test that get_progress_tree includes total count."""
        for i in range(3):
            progress = self._create_nested_progress(f"test-{i}", depth=0)
            self.recorder.post_nested_progress(progress)
        
        tree = self.recorder.get_progress_tree()
        
        self.assertEqual(tree["total_count"], 3)


class GetNestedProgressTests(NestedProgressTrackingTests):
    """Tests for get_nested_progress method."""

    def test_get_nested_progress_returns_progress(self):
        """Test that get_nested_progress returns the progress indicator."""
        progress = self._create_nested_progress("test-123")
        self.recorder.post_nested_progress(progress)
        
        result = self.recorder.get_nested_progress("test-123")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "test-123")

    def test_get_nested_progress_returns_none_for_unknown(self):
        """Test that get_nested_progress returns None for unknown ID."""
        result = self.recorder.get_nested_progress("nonexistent")
        
        self.assertIsNone(result)


class GetChildProgressTests(NestedProgressTrackingTests):
    """Tests for get_child_progress method."""

    def test_get_child_progress_returns_children(self):
        """Test that get_child_progress returns child progress indicators."""
        parent = self._create_nested_progress("parent-123", depth=0)
        child1 = self._create_nested_progress("child-1", parent_id="parent-123", depth=1)
        child2 = self._create_nested_progress("child-2", parent_id="parent-123", depth=1)
        
        self.recorder.post_nested_progress(parent)
        self.recorder.post_nested_progress(child1)
        self.recorder.post_nested_progress(child2)
        
        children = self.recorder.get_child_progress("parent-123")
        
        self.assertEqual(len(children), 2)
        child_ids = [c.id for c in children]
        self.assertIn("child-1", child_ids)
        self.assertIn("child-2", child_ids)

    def test_get_child_progress_returns_empty_for_no_children(self):
        """Test that get_child_progress returns empty list for no children."""
        progress = self._create_nested_progress("test-123", depth=0)
        self.recorder.post_nested_progress(progress)
        
        children = self.recorder.get_child_progress("test-123")
        
        self.assertEqual(len(children), 0)


class GetRootProgressTests(NestedProgressTrackingTests):
    """Tests for get_root_progress method."""

    def test_get_root_progress_returns_roots_only(self):
        """Test that get_root_progress returns only root-level progress."""
        root1 = self._create_nested_progress("root-1", depth=0)
        root2 = self._create_nested_progress("root-2", depth=0)
        child = self._create_nested_progress("child-1", parent_id="root-1", depth=1)
        
        self.recorder.post_nested_progress(root1)
        self.recorder.post_nested_progress(root2)
        self.recorder.post_nested_progress(child)
        
        roots = self.recorder.get_root_progress()
        
        self.assertEqual(len(roots), 2)
        root_ids = [r.id for r in roots]
        self.assertIn("root-1", root_ids)
        self.assertIn("root-2", root_ids)
        self.assertNotIn("child-1", root_ids)


class ClearNestedProgressTests(NestedProgressTrackingTests):
    """Tests for clear_nested_progress method."""

    def test_clear_nested_progress_removes_progress(self):
        """Test that clear_nested_progress removes the progress indicator."""
        progress = self._create_nested_progress("test-123")
        self.recorder.post_nested_progress(progress)
        
        removed = self.recorder.clear_nested_progress("test-123")
        
        self.assertIsNotNone(removed)
        self.assertIsNone(self.recorder.get_nested_progress("test-123"))

    def test_clear_nested_progress_removes_from_running_tasks(self):
        """Test that clear_nested_progress removes from running_tasks."""
        progress = self._create_nested_progress("test-123")
        self.recorder.post_nested_progress(progress)
        
        self.assertIn("test-123", self.recorder._running_tasks)
        
        self.recorder.clear_nested_progress("test-123")
        
        self.assertNotIn("test-123", self.recorder._running_tasks)

    def test_clear_nested_progress_cascades_to_children(self):
        """Test that clear_nested_progress removes all descendants."""
        parent = self._create_nested_progress("parent-123", depth=0)
        child = self._create_nested_progress("child-456", parent_id="parent-123", depth=1)
        grandchild = self._create_nested_progress("grandchild-789", parent_id="child-456", depth=2)
        
        self.recorder.post_nested_progress(parent)
        self.recorder.post_nested_progress(child)
        self.recorder.post_nested_progress(grandchild)
        
        self.recorder.clear_nested_progress("parent-123")
        
        self.assertIsNone(self.recorder.get_nested_progress("parent-123"))
        self.assertIsNone(self.recorder.get_nested_progress("child-456"))
        self.assertIsNone(self.recorder.get_nested_progress("grandchild-789"))

    def test_clear_nested_progress_returns_none_for_unknown(self):
        """Test that clear_nested_progress returns None for unknown ID."""
        removed = self.recorder.clear_nested_progress("nonexistent")
        
        self.assertIsNone(removed)


if __name__ == "__main__":
    unittest.main()
