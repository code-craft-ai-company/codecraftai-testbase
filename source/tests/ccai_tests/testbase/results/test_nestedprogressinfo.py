"""
    .. module:: ccai_tests.testbase.results.test_nestedprogressinfo
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for NestedProgressInfo class.

    .. moduleauthor:: CodeCraftX
"""

import unittest
from datetime import datetime

from ccai.testbase.results.model.progressinfo import ProgressInfo
from ccai.testbase.results.model.nestedprogressinfo import NestedProgressInfo
from ccai.testbase.results.model.progresscode import ProgressCode
from ccai.testbase.results.model.progresstype import ProgressType


class NestedProgressInfoConstructorTests(unittest.TestCase):
    """Tests for NestedProgressInfo constructor (Requirements 22.1-22.11)."""

    def test_constructor_with_parent_id(self):
        """Test that NestedProgressInfo can be created with a parent_id."""
        progress = NestedProgressInfo(
            id="child-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="5",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id="parent-456"
        )
        
        self.assertEqual(progress.parent_id, "parent-456")

    def test_constructor_without_parent_id(self):
        """Test that NestedProgressInfo can be created without a parent_id (root level)."""
        progress = NestedProgressInfo(
            id="root-123",
            category="test-suite",
            moniker="Integration Tests",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now()
        )
        
        self.assertIsNone(progress.parent_id)

    def test_constructor_with_depth(self):
        """Test that NestedProgressInfo can be created with a depth value."""
        progress = NestedProgressInfo(
            id="nested-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="5",
            position="2",
            status=ProgressCode.Running,
            when=datetime.now(),
            parent_id="parent-456",
            depth=2
        )
        
        self.assertEqual(progress.depth, 2)

    def test_constructor_default_children_ids(self):
        """Test that children_ids defaults to empty list."""
        progress = NestedProgressInfo(
            id="test-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="1",
            position="0",
            status=ProgressCode.NotStarted,
            when=datetime.now()
        )
        
        self.assertEqual(progress.children_ids, [])


class NestedProgressInfoAsDictTests(unittest.TestCase):
    """Tests for NestedProgressInfo.as_dict method (Requirements 22.10)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_datetime = datetime(2025, 2, 20, 10, 30, 0, 123456)
        self.progress = NestedProgressInfo(
            id="nested-test-123",
            category="test-execution",
            moniker="test_module.test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="10",
            position="5",
            status=ProgressCode.Running,
            when=self.test_datetime,
            data={"worker_id": "worker-1"},
            parent_id="parent-456",
            children_ids=["child-1", "child-2"],
            depth=1
        )

    def test_as_dict_includes_parent_id(self):
        """Test that as_dict includes parent_id field."""
        result = self.progress.as_dict()
        
        self.assertIn("parent_id", result)
        self.assertEqual(result["parent_id"], "parent-456")

    def test_as_dict_includes_children_ids(self):
        """Test that as_dict includes children_ids field."""
        result = self.progress.as_dict()
        
        self.assertIn("children_ids", result)
        self.assertEqual(result["children_ids"], ["child-1", "child-2"])

    def test_as_dict_includes_depth(self):
        """Test that as_dict includes depth field."""
        result = self.progress.as_dict()
        
        self.assertIn("depth", result)
        self.assertEqual(result["depth"], 1)

    def test_as_dict_includes_base_fields(self):
        """Test that as_dict includes all base ProgressInfo fields."""
        result = self.progress.as_dict()
        
        self.assertEqual(result["id"], "nested-test-123")
        self.assertEqual(result["category"], "test-execution")
        self.assertEqual(result["moniker"], "test_module.test_function")
        self.assertEqual(result["ptype"], "Sequential")
        self.assertEqual(result["status"], "Running")


class NestedProgressInfoFromDictTests(unittest.TestCase):
    """Tests for NestedProgressInfo.from_dict method (Requirements 22.11)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dict = {
            "id": "nested-789",
            "category": "integration-test",
            "moniker": "integration.test_suite",
            "ptype": "TimeSpan",
            "range_min": "0",
            "range_max": "3600",
            "position": "1800",
            "status": "Paused",
            "when": "2025-02-20T15:45:30.654321",
            "data": {"key": "value"},
            "parent_id": "parent-123",
            "children_ids": ["child-a", "child-b"],
            "depth": 2
        }

    def test_from_dict_returns_nestedprogressinfo(self):
        """Test that from_dict returns a NestedProgressInfo instance."""
        result = NestedProgressInfo.from_dict(self.test_dict)
        
        self.assertIsInstance(result, NestedProgressInfo)

    def test_from_dict_reconstructs_parent_id(self):
        """Test that from_dict reconstructs parent_id correctly."""
        result = NestedProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.parent_id, "parent-123")

    def test_from_dict_reconstructs_children_ids(self):
        """Test that from_dict reconstructs children_ids correctly."""
        result = NestedProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.children_ids, ["child-a", "child-b"])

    def test_from_dict_reconstructs_depth(self):
        """Test that from_dict reconstructs depth correctly."""
        result = NestedProgressInfo.from_dict(self.test_dict)
        
        self.assertEqual(result.depth, 2)

    def test_from_dict_handles_missing_nested_fields(self):
        """Test that from_dict handles missing nested fields with defaults."""
        minimal_dict = {
            "id": "minimal-123",
            "category": "test",
            "moniker": "test.minimal",
            "ptype": "Sequential",
            "range_min": "0",
            "range_max": "1",
            "position": "0",
            "status": "Running",
            "when": "2025-02-20T12:00:00"
        }
        
        result = NestedProgressInfo.from_dict(minimal_dict)
        
        self.assertIsNone(result.parent_id)
        self.assertEqual(result.children_ids, [])
        self.assertEqual(result.depth, 0)


class NestedProgressInfoFromProgressInfoTests(unittest.TestCase):
    """Tests for NestedProgressInfo.from_progress_info factory method."""

    def test_from_progress_info_converts_correctly(self):
        """Test that from_progress_info converts ProgressInfo to NestedProgressInfo."""
        base_progress = ProgressInfo(
            id="base-123",
            category="test",
            moniker="test_function",
            ptype=ProgressType.Sequential,
            range_min="0",
            range_max="5",
            position="2",
            status=ProgressCode.Running,
            when=datetime.now(),
            data={"key": "value"}
        )
        
        nested = NestedProgressInfo.from_progress_info(
            base_progress,
            parent_id="parent-456",
            depth=1
        )
        
        self.assertIsInstance(nested, NestedProgressInfo)
        self.assertEqual(nested.id, "base-123")
        self.assertEqual(nested.parent_id, "parent-456")
        self.assertEqual(nested.depth, 1)
        self.assertEqual(nested.children_ids, [])

    def test_from_progress_info_preserves_all_fields(self):
        """Test that from_progress_info preserves all base fields."""
        test_datetime = datetime(2025, 3, 15, 14, 30, 0)
        base_progress = ProgressInfo(
            id="preserve-123",
            category="preserve-category",
            moniker="preserve.moniker",
            ptype=ProgressType.NumericRange,
            range_min="10",
            range_max="100",
            position="50",
            status=ProgressCode.Paused,
            when=test_datetime,
            data={"nested": {"data": True}}
        )
        
        nested = NestedProgressInfo.from_progress_info(base_progress)
        
        self.assertEqual(nested.category, "preserve-category")
        self.assertEqual(nested.moniker, "preserve.moniker")
        self.assertEqual(nested.ptype, ProgressType.NumericRange)
        self.assertEqual(nested.range_min, "10")
        self.assertEqual(nested.range_max, "100")
        self.assertEqual(nested.position, "50")
        self.assertEqual(nested.status, ProgressCode.Paused)
        self.assertEqual(nested.when, test_datetime)
        self.assertEqual(nested.data, {"nested": {"data": True}})


class NestedProgressInfoChildManagementTests(unittest.TestCase):
    """Tests for NestedProgressInfo child management methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.progress = NestedProgressInfo(
            id="parent-123",
            category="test-suite",
            moniker="Test Suite",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="100",
            position="0",
            status=ProgressCode.Running,
            when=datetime.now()
        )

    def test_add_child_adds_to_children_ids(self):
        """Test that add_child adds child ID to children_ids list."""
        self.progress.add_child("child-1")
        
        self.assertIn("child-1", self.progress.children_ids)

    def test_add_child_prevents_duplicates(self):
        """Test that add_child does not add duplicate child IDs."""
        self.progress.add_child("child-1")
        self.progress.add_child("child-1")
        
        self.assertEqual(self.progress.children_ids.count("child-1"), 1)

    def test_remove_child_removes_from_children_ids(self):
        """Test that remove_child removes child ID from children_ids list."""
        self.progress.add_child("child-1")
        self.progress.add_child("child-2")
        
        self.progress.remove_child("child-1")
        
        self.assertNotIn("child-1", self.progress.children_ids)
        self.assertIn("child-2", self.progress.children_ids)

    def test_remove_child_handles_nonexistent_id(self):
        """Test that remove_child handles non-existent child ID gracefully."""
        self.progress.add_child("child-1")
        
        # Should not raise an exception
        self.progress.remove_child("nonexistent")
        
        self.assertIn("child-1", self.progress.children_ids)


class NestedProgressInfoRoundTripTests(unittest.TestCase):
    """Tests for NestedProgressInfo round-trip serialization."""

    def test_round_trip_preserves_all_fields(self):
        """Test that as_dict followed by from_dict preserves all fields."""
        original = NestedProgressInfo(
            id="round-trip-test",
            category="round-trip-category",
            moniker="round.trip.moniker",
            ptype=ProgressType.NumericRange,
            range_min="100",
            range_max="500",
            position="250",
            status=ProgressCode.Running,
            when=datetime(2025, 3, 10, 14, 25, 30, 999999),
            data={"nested": {"key": "value"}},
            parent_id="parent-round-trip",
            children_ids=["child-1", "child-2", "child-3"],
            depth=3
        )
        
        serialized = original.as_dict()
        reconstructed = NestedProgressInfo.from_dict(serialized)
        
        self.assertEqual(reconstructed.id, original.id)
        self.assertEqual(reconstructed.category, original.category)
        self.assertEqual(reconstructed.moniker, original.moniker)
        self.assertEqual(reconstructed.ptype, original.ptype)
        self.assertEqual(reconstructed.range_min, original.range_min)
        self.assertEqual(reconstructed.range_max, original.range_max)
        self.assertEqual(reconstructed.position, original.position)
        self.assertEqual(reconstructed.status, original.status)
        self.assertEqual(reconstructed.when, original.when)
        self.assertEqual(reconstructed.data, original.data)
        self.assertEqual(reconstructed.parent_id, original.parent_id)
        self.assertEqual(reconstructed.children_ids, original.children_ids)
        self.assertEqual(reconstructed.depth, original.depth)


if __name__ == "__main__":
    unittest.main()
