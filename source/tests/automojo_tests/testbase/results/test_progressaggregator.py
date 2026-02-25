"""
    .. module:: automojo_tests.testbase.results.test_progressaggregator
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for ProgressAggregator class.

    .. moduleauthor:: AutomationX
"""

import unittest
from datetime import datetime

from automojo.testbase.results.model.progressinfo import ProgressInfo
from automojo.testbase.results.model.nestedprogressinfo import NestedProgressInfo
from automojo.testbase.results.model.progressaggregator import ProgressAggregator
from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.model.progresstype import ProgressType


class ProgressAggregatorBasicTests(unittest.TestCase):
    """Tests for basic ProgressAggregator functionality (Requirements 22.1-22.11, 28.1-28.6)."""

    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = ProgressAggregator()

    def test_aggregator_starts_empty(self):
        """Test that a new aggregator has no progress indicators."""
        self.assertEqual(len(self.aggregator), 0)

    def test_register_progress_adds_to_aggregator(self):
        """Test that register_progress adds a progress indicator."""
        progress = NestedProgressInfo(
            id="test-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now()
        )
        
        self.aggregator.register_progress(progress)
        
        self.assertEqual(len(self.aggregator), 1)

    def test_register_progress_returns_nested_progress(self):
        """Test that register_progress returns a NestedProgressInfo."""
        progress = NestedProgressInfo(
            id="test-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now()
        )
        
        result = self.aggregator.register_progress(progress)
        
        self.assertIsInstance(result, NestedProgressInfo)

    def test_register_progress_converts_progressinfo(self):
        """Test that register_progress converts ProgressInfo to NestedProgressInfo."""
        progress = ProgressInfo(
            id="base-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now()
        )
        
        result = self.aggregator.register_progress(progress)
        
        self.assertIsInstance(result, NestedProgressInfo)
        self.assertEqual(result.id, "base-123")


class ProgressAggregatorHierarchyTests(unittest.TestCase):
    """Tests for ProgressAggregator hierarchy management (Requirements 22.1-22.11, 28.1-28.6)."""

    def setUp(self):
        """Set up test fixtures with a parent-child hierarchy."""
        self.aggregator = ProgressAggregator()
        
        # Create parent progress
        self.parent = NestedProgressInfo(
            id="parent-123",
            category="test-suite",
            moniker="Integration Tests",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id=None,
            depth=0
        )
        
        # Create child progress
        self.child1 = NestedProgressInfo(
            id="child-1",
            category="test",
            moniker="test_login",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id="parent-123",
            depth=1
        )
        
        self.child2 = NestedProgressInfo(
            id="child-2",
            category="test",
            moniker="test_logout",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.NotStarted,
            when=datetime.now(),
            parent_id="parent-123",
            depth=1
        )

    def test_parent_child_relationship_established(self):
        """Test that parent-child relationships are established correctly."""
        self.aggregator.register_progress(self.parent)
        self.aggregator.register_progress(self.child1)
        
        parent = self.aggregator.get_progress("parent-123")
        
        self.assertIn("child-1", parent.children_ids)

    def test_get_children_returns_child_progress(self):
        """Test that get_children returns child progress indicators."""
        self.aggregator.register_progress(self.parent)
        self.aggregator.register_progress(self.child1)
        self.aggregator.register_progress(self.child2)
        
        children = self.aggregator.get_children("parent-123")
        
        self.assertEqual(len(children), 2)
        child_ids = [c.id for c in children]
        self.assertIn("child-1", child_ids)
        self.assertIn("child-2", child_ids)

    def test_get_root_progress_returns_roots_only(self):
        """Test that get_root_progress returns only root-level progress."""
        self.aggregator.register_progress(self.parent)
        self.aggregator.register_progress(self.child1)
        self.aggregator.register_progress(self.child2)
        
        roots = self.aggregator.get_root_progress()
        
        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0].id, "parent-123")


class ProgressAggregatorAggregationTests(unittest.TestCase):
    """Tests for ProgressAggregator aggregation functionality (Requirements 28.1-28.6)."""

    def setUp(self):
        """Set up test fixtures with a hierarchy for aggregation testing."""
        self.aggregator = ProgressAggregator()
        
        # Create parent
        self.parent = NestedProgressInfo(
            id="suite-123",
            category="test-suite",
            moniker="Test Suite",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id=None,
            depth=0
        )
        self.aggregator.register_progress(self.parent)

    def _create_child(self, child_id: str, status: ProgressCode) -> NestedProgressInfo:
        """Helper to create a child progress indicator."""
        return NestedProgressInfo(
            id=child_id,
            category="test",
            moniker=f"test_{child_id}",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="1" if status == ProgressCode.Completed else "0",
            status=status,
            when=datetime.now(),
            parent_id="suite-123",
            depth=1
        )

    def test_aggregation_counts_completed(self):
        """Test that aggregation correctly counts completed children."""
        self.aggregator.register_progress(self._create_child("c1", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c2", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c3", ProgressCode.Running))
        
        aggregated = self.aggregator.get_aggregated_progress("suite-123")
        
        self.assertEqual(aggregated["completed_count"], 2)
        self.assertEqual(aggregated["running_count"], 1)
        self.assertEqual(aggregated["total_children"], 3)

    def test_aggregation_calculates_completion_percentage(self):
        """Test that aggregation calculates completion percentage correctly."""
        self.aggregator.register_progress(self._create_child("c1", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c2", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c3", ProgressCode.Running))
        self.aggregator.register_progress(self._create_child("c4", ProgressCode.NotStarted))
        
        aggregated = self.aggregator.get_aggregated_progress("suite-123")
        
        # 2 completed out of 4 = 50%
        self.assertAlmostEqual(aggregated["completion_percentage"], 50.0)

    def test_aggregation_status_errored_takes_priority(self):
        """Test that Errored status takes priority in aggregate status."""
        self.aggregator.register_progress(self._create_child("c1", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c2", ProgressCode.Errored))
        self.aggregator.register_progress(self._create_child("c3", ProgressCode.Running))
        
        aggregated = self.aggregator.get_aggregated_progress("suite-123")
        
        self.assertEqual(aggregated["aggregate_status"], "Errored")

    def test_aggregation_status_failed_takes_priority_over_running(self):
        """Test that Failed status takes priority over Running."""
        self.aggregator.register_progress(self._create_child("c1", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c2", ProgressCode.Failed))
        self.aggregator.register_progress(self._create_child("c3", ProgressCode.Running))
        
        aggregated = self.aggregator.get_aggregated_progress("suite-123")
        
        self.assertEqual(aggregated["aggregate_status"], "Failed")

    def test_aggregation_status_completed_when_all_done(self):
        """Test that aggregate status is Completed when all children are done."""
        self.aggregator.register_progress(self._create_child("c1", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c2", ProgressCode.Completed))
        self.aggregator.register_progress(self._create_child("c3", ProgressCode.Completed))
        
        aggregated = self.aggregator.get_aggregated_progress("suite-123")
        
        self.assertEqual(aggregated["aggregate_status"], "Completed")

    def test_aggregation_returns_none_for_unknown_id(self):
        """Test that get_aggregated_progress returns None for unknown ID."""
        aggregated = self.aggregator.get_aggregated_progress("nonexistent")
        
        self.assertIsNone(aggregated)


class ProgressAggregatorRemovalTests(unittest.TestCase):
    """Tests for ProgressAggregator removal functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = ProgressAggregator()
        
        # Create a hierarchy: parent -> child -> grandchild
        self.parent = NestedProgressInfo(
            id="parent",
            category="suite",
            moniker="Parent",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id=None,
            depth=0
        )
        
        self.child = NestedProgressInfo(
            id="child",
            category="module",
            moniker="Child",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id="parent",
            depth=1
        )
        
        self.grandchild = NestedProgressInfo(
            id="grandchild",
            category="test",
            moniker="Grandchild",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id="child",
            depth=2
        )
        
        self.aggregator.register_progress(self.parent)
        self.aggregator.register_progress(self.child)
        self.aggregator.register_progress(self.grandchild)

    def test_remove_progress_removes_from_aggregator(self):
        """Test that remove_progress removes the progress indicator."""
        self.aggregator.remove_progress("grandchild")
        
        self.assertIsNone(self.aggregator.get_progress("grandchild"))
        self.assertEqual(len(self.aggregator), 2)

    def test_remove_progress_removes_from_parent_children(self):
        """Test that remove_progress removes from parent's children list."""
        self.aggregator.remove_progress("grandchild")
        
        child = self.aggregator.get_progress("child")
        self.assertNotIn("grandchild", child.children_ids)

    def test_remove_progress_cascades_to_children(self):
        """Test that remove_progress removes all descendants."""
        self.aggregator.remove_progress("child")
        
        # Both child and grandchild should be removed
        self.assertIsNone(self.aggregator.get_progress("child"))
        self.assertIsNone(self.aggregator.get_progress("grandchild"))
        self.assertEqual(len(self.aggregator), 1)

    def test_remove_progress_returns_removed_progress(self):
        """Test that remove_progress returns the removed progress."""
        removed = self.aggregator.remove_progress("grandchild")
        
        self.assertIsNotNone(removed)
        self.assertEqual(removed.id, "grandchild")

    def test_remove_progress_returns_none_for_unknown(self):
        """Test that remove_progress returns None for unknown ID."""
        removed = self.aggregator.remove_progress("nonexistent")
        
        self.assertIsNone(removed)


class ProgressAggregatorTreeTests(unittest.TestCase):
    """Tests for ProgressAggregator tree functionality."""

    def setUp(self):
        """Set up test fixtures with a multi-level hierarchy."""
        self.aggregator = ProgressAggregator()
        
        # Create root 1 with children
        root1 = NestedProgressInfo(
            id="root1",
            category="suite",
            moniker="Suite 1",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id=None,
            depth=0
        )
        
        child1 = NestedProgressInfo(
            id="child1",
            category="test",
            moniker="Test 1",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id="root1",
            depth=1
        )
        
        # Create root 2 (no children)
        root2 = NestedProgressInfo(
            id="root2",
            category="suite",
            moniker="Suite 2",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="50",
            position="0",
            status=ProgressCode.NotStarted,
            when=datetime.now(),
            parent_id=None,
            depth=0
        )
        
        self.aggregator.register_progress(root1)
        self.aggregator.register_progress(child1)
        self.aggregator.register_progress(root2)

    def test_get_progress_tree_returns_roots(self):
        """Test that get_progress_tree returns all root nodes."""
        tree = self.aggregator.get_progress_tree()
        
        self.assertIn("roots", tree)
        self.assertEqual(len(tree["roots"]), 2)

    def test_get_progress_tree_includes_children(self):
        """Test that get_progress_tree includes nested children."""
        tree = self.aggregator.get_progress_tree()
        
        # Find root1 in the tree
        root1_node = None
        for root in tree["roots"]:
            if root["id"] == "root1":
                root1_node = root
                break
        
        self.assertIsNotNone(root1_node)
        self.assertIn("children", root1_node)
        self.assertEqual(len(root1_node["children"]), 1)
        self.assertEqual(root1_node["children"][0]["id"], "child1")

    def test_get_progress_tree_includes_total_count(self):
        """Test that get_progress_tree includes total count."""
        tree = self.aggregator.get_progress_tree()
        
        self.assertIn("total_count", tree)
        self.assertEqual(tree["total_count"], 3)


class ProgressAggregatorUpdateTests(unittest.TestCase):
    """Tests for ProgressAggregator update functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.aggregator = ProgressAggregator()
        
        progress = NestedProgressInfo(
            id="test-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="0",
            status=ProgressCode.NotStarted,
            when=datetime.now()
        )
        self.aggregator.register_progress(progress)

    def test_update_progress_updates_position(self):
        """Test that update_progress updates the position."""
        self.aggregator.update_progress("test-123", position="5")
        
        progress = self.aggregator.get_progress("test-123")
        self.assertEqual(progress.position, "5")

    def test_update_progress_updates_status(self):
        """Test that update_progress updates the status."""
        self.aggregator.update_progress("test-123", status=ProgressCode.Running)
        
        progress = self.aggregator.get_progress("test-123")
        self.assertEqual(progress.status, ProgressCode.Running)

    def test_update_progress_updates_data(self):
        """Test that update_progress updates the data."""
        self.aggregator.update_progress("test-123", data={"key": "value"})
        
        progress = self.aggregator.get_progress("test-123")
        self.assertEqual(progress.data, {"key": "value"})

    def test_update_progress_returns_none_for_unknown(self):
        """Test that update_progress returns None for unknown ID."""
        result = self.aggregator.update_progress("nonexistent", position="5")
        
        self.assertIsNone(result)


class ProgressAggregatorClearTests(unittest.TestCase):
    """Tests for ProgressAggregator clear functionality."""

    def test_clear_removes_all_progress(self):
        """Test that clear removes all progress indicators."""
        aggregator = ProgressAggregator()
        
        for i in range(5):
            progress = NestedProgressInfo(
                id=f"test-{i}",
                category="test",
                moniker=f"test_{i}",
                ptype=ProgressType.Sequential,
                range_min="0",
                range_max="1",
                position="0",
                status=ProgressCode.Running,
                when=datetime.now()
            )
            aggregator.register_progress(progress)
        
        self.assertEqual(len(aggregator), 5)
        
        aggregator.clear()
        
        self.assertEqual(len(aggregator), 0)


if __name__ == "__main__":
    unittest.main()
